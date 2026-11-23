#!/usr/bin/env node
/**
 * Diagnostic-only epoch pressure calibration backtest for Loučka.
 * Source: official CHMI hourly references already monthly-aggregated by PR #89.
 * No SQL connections or weather database writes. No replacement values.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const EPOCHS = [
  {
    "id": "D1",
    "tag": "2009–2011 před výpadkem",
    "type": "daily",
    "start": "2009-04",
    "end": "2011-08"
  },
  {
    "id": "D2",
    "tag": "2012 až před skokem 2013",
    "type": "daily",
    "start": "2012-03",
    "end": "2013-07"
  },
  {
    "id": "D3",
    "tag": "po skoku 2013 až 2015",
    "type": "daily",
    "start": "2013-09",
    "end": "2015-12"
  },
  {
    "id": "D4",
    "tag": "2016–2017",
    "type": "daily",
    "start": "2016-01",
    "end": "2017-12"
  },
  {
    "id": "H1",
    "tag": "2018 až před přepnutím 2019",
    "type": "hourly",
    "start": "2018-01",
    "end": "2019-03"
  },
  {
    "id": "H2",
    "tag": "2019 po přepnutí až před GW1000",
    "type": "hourly",
    "start": "2019-05",
    "end": "2022-07"
  },
  {
    "id": "H3",
    "tag": "GW1000 před změnou kopie 2024",
    "type": "hourly",
    "start": "2022-09",
    "end": "2024-04"
  },
  {
    "id": "H4",
    "tag": "přechod mezi změnami 2024",
    "type": "hourly",
    "start": "2024-06",
    "end": "2024-06"
  },
  {
    "id": "H5",
    "tag": "2024 změněná kopie až 2026",
    "type": "hourly",
    "start": "2024-08",
    "end": "2026-01"
  },
  {
    "id": "H6",
    "tag": "2026 po březnovém rozchodu",
    "type": "hourly",
    "start": "2026-04",
    "end": "2026-11"
  }
];
function parseCsv(s){
 const lines=s.trim().split(/\r?\n/),columns=lines.shift().split(",");
 return lines.filter(Boolean).map(line=>{const v=line.split(",");if(v.length!==columns.length)throw Error("Unsupported CSV layout, expected "+columns.length+" got "+v.length);return Object.fromEntries(columns.map((c,i)=>[c,v[i]]))});
}

function median(a){if(!a.length)throw Error("empty median");const x=a.slice().sort((b,c)=>b-c),i=Math.floor(x.length/2);return x.length%2?x[i]:(x[i-1]+x[i])/2;}

function quantile(a,p){if(!a.length||p<0||p>1)throw Error("invalid quantile");const v=a.slice().sort((x,y)=>x-y),i=(v.length-1)*p,j=Math.floor(i);return v[j]+(v[Math.min(j+1,v.length-1)]-v[j])*(i-j);}

function fit(train,field,kind){
 if(kind==="raw")return {kind,intercept:0,slope:0};
 if(kind==="constant")return {kind,intercept:median(train.map(x=>x[field])),slope:0};
 if(kind!=="trend")throw Error("unknown model");
 const slopes=[];for(let i=0;i<train.length;i++)for(let j=i+1;j<train.length;j++){const d=train[j].x-train[i].x;if(d)slopes.push((train[j][field]-train[i][field])/d);}
 const slope=median(slopes);
 return {kind,intercept:median(train.map(x=>x[field]-slope*x.x)),slope};
}

function forecast(model,x){return model.intercept+model.slope*x;}

function describe(values){
 const m=median(values),abs=values.map(v=>Math.abs(v));
 return {n:values.length,mae:abs.reduce((a,b)=>a+b,0)/values.length,medianBias:m,mad:median(values.map(v=>Math.abs(v-m))),p95AbsoluteMonthlyMedian:quantile(abs,.95)};
}

function buildCatalog(hourText,dailyText){
 const catalog={hourly:{},daily:{}};
 const add=(type,month,station,value,n)=>{
   if(!Number.isFinite(value)||!Number.isFinite(n))return;
   const x=(Number(month.slice(0,4))-2000)*12+(Number(month.slice(5,7))-1);
   const r=catalog[type][month]??={month,x};
   r[station]=value;r[station+"n"]=n;
   catalog[type][month]=r;
 };
 for(const r of parseCsv(hourText)){
  if(r.element!=="P_hm"||r.loucka_field!=="barometer"||Number(r.n)<48)continue;
  const station=r.station_id.endsWith("11774")?"H":r.station_id.endsWith("11782")?"M":null;
  if(station)add("hourly",r.utc_year+"-"+r.month.padStart(2,"0"),station,Number(r.median),Number(r.n));
 }
 for(const r of parseCsv(dailyText)){
  if(Number(r.chmi_daily_avg_rows)<15||Number(r.loucka_archive_rows)<2000)continue;
  const station=r.station_id.endsWith("11774")?"H":r.station_id.endsWith("11782")?"M":null;
  if(station)add("daily",r.year+"-"+r.month.padStart(2,"0"),station,Number(r.height_adjusted_pressure_minus_chmi_P_hpa),Number(r.chmi_daily_avg_rows));
 }
 return catalog;
}

function evaluateEpoch(catalog,epoch){
 const rows=Object.values(catalog[epoch.type]||{}).filter(r=>r.month>=epoch.start&&r.month<=epoch.end&&Number.isFinite(r.H)&&Number.isFinite(r.M)).sort((a,b)=>a.month.localeCompare(b.month));
 const result={id:epoch.id,tag:epoch.tag,type:epoch.type,start:epoch.start,end:epoch.end,months:rows.length,field:epoch.type==="hourly"?"barometer − ČHMÚ P_hm":"height-adjusted pressure − ČHMÚ daily P (coarse)"};
 if(rows.length<8){result.status="INSUFFICIENT_MONTHS";return result;}
 const n=rows.length,nTrain=Math.max(4,Math.floor(n*0.6)),nValidation=Math.max(2,Math.floor(n*.2));
 if(n-nTrain-nValidation<2)throw Error("insufficient future holdout");
 const train=rows.slice(0,nTrain),val=rows.slice(nTrain,nTrain+nValidation),hold=rows.slice(nTrain+nValidation);
 result.splits={train:[train[0].month,train.at(-1).month],validation:[val[0].month,val.at(-1).month],holdout:[hold[0].month,hold.at(-1).month]};
 result.references={};
 for(const own of ["H","M"]){
   const other=own==="H"?"M":"H",models={};
   for(const kind of ["raw","constant","trend"]){
     const model=fit(train,own,kind);
     models[kind]={parameters:model,validation:describe(val.map(r=>r[own]-forecast(model,r.x))),holdoutOwn:describe(hold.map(r=>r[own]-forecast(model,r.x))),holdoutIndependent:describe(hold.map(r=>r[other]-forecast(model,r.x)))};
   }
   const selected=["raw","constant","trend"].sort((a,b)=>models[a].validation.mae-models[b].validation.mae)[0];
   result.references[own]={selected,models};
 }
 const h=result.references.H.models[result.references.H.selected],m=result.references.M.models[result.references.M.selected];
 const pass=hold.length>=3&&[h.holdoutOwn,h.holdoutIndependent,m.holdoutOwn,m.holdoutIndependent].every(s=>s.mae<=1.5&&s.p95AbsoluteMonthlyMedian<=3);
 result.status=epoch.type==="daily"?"COARSE_CONTEXT_ONLY":pass?"MONTHLY_BACKTEST_PASS_NOT_APPLY":"MONTHLY_BACKTEST_UNSATISFACTORY";
 return result;
}

function runModel(hourText,dailyText){const data=buildCatalog(hourText,dailyText);return {schema:"loucka-pressure-monthly-calibration-backtest-v1",scope:"MONTHLY_DIAGNOSTICS_ONLY_NO_WEATHER_DATABASE_WRITES",method:"Theil-Sen robust trend; constant median; raw baseline; validation selects model independently per CHMI station. Chronological 60/20/20 train/validation/holdout. Never train or select on held-out months.",stationIds:{H:"0-20000-0-11774",M:"0-20000-0-11782"},epochs:EPOCHS.map(e=>evaluateEpoch(data,e))};}
export {parseCsv,median,quantile,fit,forecast,describe,buildCatalog,evaluateEpoch,runModel,EPOCHS};
function main(){
 const hourly=fs.readFileSync(path.join(ROOT,"reports/parallel-audit/pressure-chmi-numeric-2009-2026/hourly_monthly_stats.csv"),"utf8");
 const daily=fs.readFileSync(path.join(ROOT,"reports/parallel-audit/pressure-chmi-numeric-2009-2026/daily_chmi_monthly_context.csv"),"utf8");
 const result=runModel(hourly,daily);
 const encoded=JSON.stringify(result,null,2)+"\n";
 const idx=process.argv.indexOf("--out");
 if(idx>=0){const destination=process.argv[idx+1];if(!destination)throw Error("--out requires a file path");fs.writeFileSync(destination,encoded,{flag:"w",encoding:"utf8"});}
 else process.stdout.write(encoded);
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url))main();
