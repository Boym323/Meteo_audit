#!/usr/bin/env python3
"""Generate bounded read-only cross-copy concordance queries for gap overlay hits."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
IN=ROOT/'sql/readonly/gap_slot_source_availability/chunks'
OUT=ROOT/'sql/readonly/gap_source_copy_concordance';OUT.mkdir(parents=True,exist_ok=True)
files=sorted(IN.glob('gap_slot_source_availability_*.sql'))
manifest=[]
fields=['outTemp','outHumidity','rain','rainRate','windSpeed']
for i,path in enumerate(files,1):
 text=path.read_text()
 start=text.index('WITH targets AS ')
 end=text.index('), matches AS (',start)
 targets=text[start:end+1]
 sql=targets+''', wh_hits AS (
 SELECT t.gap_id,t.gap_band,t.left_time,t.right_time,a.dateTime ts,
        a.usUnits wh_units,a.`interval` wh_interval,a.outTemp wh_temp,a.outHumidity wh_rh,
        a.rain wh_rain,a.rainRate wh_rainRate,a.windSpeed wh_wind
 FROM targets t JOIN weewx_WH1080.archive a
   ON a.dateTime>t.left_time AND a.dateTime<t.right_time AND MOD(a.dateTime-t.left_time,300)=0
 LEFT JOIN loucka_reconstruction.archive r ON r.dateTime=a.dateTime
 WHERE r.dateTime IS NULL
)
SELECT CAST(SUBSTRING_INDEX(h.gap_id,':',1) AS UNSIGNED) utc_year,h.gap_band,
 CASE WHEN h.ts>=1514764800 AND h.ts<1522540800 THEN 'PROTECTED_Q1_2018_DIAGNOSTIC' ELSE 'NORMAL' END protection_scope,
 COUNT(*) wh1080_rows,SUM(o.dateTime IS NOT NULL) old_weewx_rows,
 SUM(o.dateTime IS NULL) old_weewx_missing,
 SUM(h.wh_units=17) wh_units17,SUM(h.wh_interval=5) wh_interval5,
 SUM(o.usUnits<=>h.wh_units) units_equal,SUM(o.`interval`<=>h.wh_interval) intervals_equal,
 SUM(o.outTemp<=>h.wh_temp) outTemp_equal,SUM(o.outTemp IS NOT NULL AND h.wh_temp IS NOT NULL) outTemp_both_present,
 SUM(o.outTemp IS NOT NULL AND h.wh_temp IS NOT NULL AND o.outTemp<>h.wh_temp) outTemp_conflict,
 SUM(h.wh_temp=0) wh_outTemp_zero,SUM(h.wh_temp IS NULL) wh_outTemp_null,
 SUM(o.outHumidity<=>h.wh_rh) outHumidity_equal,SUM(o.outHumidity IS NOT NULL AND h.wh_rh IS NOT NULL) outHumidity_both_present,
 SUM(o.outHumidity IS NOT NULL AND h.wh_rh IS NOT NULL AND o.outHumidity<>h.wh_rh) outHumidity_conflict,
 SUM(h.wh_rh IS NULL) wh_outHumidity_null,
 SUM(o.rain<=>h.wh_rain) rain_equal,SUM(o.rain IS NOT NULL AND h.wh_rain IS NOT NULL) rain_both_present,
 SUM(o.rain IS NOT NULL AND h.wh_rain IS NOT NULL AND o.rain<>h.wh_rain) rain_conflict,
 SUM(h.wh_rain IS NULL) wh_rain_null,
 SUM(o.rainRate<=>h.wh_rainRate) rainRate_equal,SUM(o.rainRate IS NOT NULL AND h.wh_rainRate IS NOT NULL) rainRate_both_present,
 SUM(o.rainRate IS NOT NULL AND h.wh_rainRate IS NOT NULL AND o.rainRate<>h.wh_rainRate) rainRate_conflict,
 SUM(h.wh_rainRate IS NULL) wh_rainRate_null,
 SUM(o.windSpeed<=>h.wh_wind) windSpeed_equal,SUM(o.windSpeed IS NOT NULL AND h.wh_wind IS NOT NULL) windSpeed_both_present,
 SUM(o.windSpeed IS NOT NULL AND h.wh_wind IS NOT NULL AND o.windSpeed<>h.wh_wind) windSpeed_conflict,
 SUM(h.wh_wind IS NULL) wh_windSpeed_null
FROM wh_hits h LEFT JOIN old_weewx.archive o ON o.dateTime=h.ts
GROUP BY utc_year,h.gap_band,protection_scope
'''
 out=OUT/f'gap_source_copy_concordance_{i:03d}.sql';out.write_text('-- READ-ONLY cross-copy quality screen; source agreement is not provenance.\n'+sql)
 manifest.append({'chunk':i,'input':str(path.relative_to(ROOT)),'path':str(out.relative_to(ROOT)),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
mf={'query_count':len(manifest),'source_scope':'WH1080 source rows in frozen conditional 5-minute gap slots, reconstruction target absent; exact-time old_weewx comparison','variables':fields,'queries':manifest,'read_only':True}
(ROOT/'data/gap_source_copy_concordance_query_manifest.json').write_text(json.dumps(mf,indent=2)+'\n')
print(json.dumps({'query_count':len(manifest),'total_sql_bytes':sum(x['bytes'] for x in manifest)}))
