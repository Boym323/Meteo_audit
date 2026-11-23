import test from "node:test";
import assert from "node:assert/strict";
import {parseCsv,median,quantile,fit,forecast,describe,evaluateEpoch,runModel,EPOCHS} from "../scripts/backtest_pressure_epoch_monthly.mjs";

test("robust median, quantile, MAE and MAD",()=>{
  assert.equal(median([3,1,2]),2);
  assert.equal(median([2,1]),1.5);
  assert.ok(Math.abs(quantile([1,2,3],0.95)-2.9)<1e-12);
  const a=describe([-2,0,2]);
  assert.equal(a.medianBias,0);
  assert.equal(a.mad,2);
  assert.ok(Math.abs(a.mae-4/3)<1e-12);
});

test("Theil-Sen recovers a known linear calibration drift",()=>{
  const train=Array.from({length:8},(_,i)=>({x:12+i,H:-25+0.5*i}));
  const linear=fit(train,"H","trend");
  const constant=fit(train,"H","constant");
  assert.ok(Math.abs(linear.slope-0.5)<1e-12);
  assert.ok(Math.abs(forecast(linear,22)-(-25+0.5*10))<1e-12);
  assert.ok(Math.abs(forecast(constant,22)+23.25)<1e-12);
});

test("the historical epoch definitions are disjoint",()=>{
  for(const type of ["daily","hourly"]){
    const x=EPOCHS.filter(e=>e.type===type);
    for(let i=1;i<x.length;i++)assert.ok(x[i-1].end<x[i].start);
  }
});

test("incomplete post-change epoch is never accepted",()=>{
  const epoch=EPOCHS.find(x=>x.id==="H4");
  const fake={hourly:{"2024-06":{month:"2024-06",x:293,H:0,M:0}}};
  assert.equal(evaluateEpoch(fake,epoch).status,"INSUFFICIENT_MONTHS");
});

test("raw baseline is preferred if already perfect",()=>{
  const epoch={id:"X",tag:"synthetic",type:"hourly",start:"2018-01",end:"2019-12"};
  const catalog={hourly:{}};
  for(let i=0;i<24;i++){
    const month=String(i%12+1).padStart(2,"0");
    const key=(2018+Math.floor(i/12))+"-"+month;
    catalog.hourly[key]={month:key,x:216+i,H:0,M:0};
  }
  const out=evaluateEpoch(catalog,epoch);
  assert.equal(out.references.H.selected,"raw");
  assert.equal(out.references.M.selected,"raw");
});

test("perturbing held-out months cannot change fitting or method selection",()=>{
  const epoch={id:"X",tag:"synthetic",type:"hourly",start:"2018-01",end:"2019-12"};
  const catalog={hourly:{}};
  for(let i=0;i<24;i++){
    const month=String(i%12+1).padStart(2,"0"),key=(2018+Math.floor(i/12))+"-"+month;
    catalog.hourly[key]={month:key,x:216+i,H:-20-i*0.3,M:-19.8-i*0.3};
  }
  const first=evaluateEpoch(catalog,epoch);
  for(let i=19;i<24;i++){
    const key=(2018+Math.floor(i/12))+"-"+String(i%12+1).padStart(2,"0");
    catalog.hourly[key].H+=1000;
    catalog.hourly[key].M-=1000;
  }
  const changed=evaluateEpoch(catalog,epoch);
  for(const station of ["H","M"]){
    const a=first.references[station],b=changed.references[station];
    assert.equal(a.selected,b.selected);
    for(const kind of ["raw","constant","trend"]){
      assert.deepEqual(a.models[kind].parameters,b.models[kind].parameters);
      assert.deepEqual(a.models[kind].validation,b.models[kind].validation);
    }
  }
});

test("CSV parser fails closed on shape changes",()=>{
  assert.deepEqual(parseCsv("a,b\n1,2\n"),[{a:"1",b:"2"}]);
  assert.throws(()=>parseCsv("a,b\n1,2,3\n"),/Unsupported CSV layout/);
});
