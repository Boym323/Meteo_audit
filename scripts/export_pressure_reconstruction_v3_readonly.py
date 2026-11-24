#!/usr/bin/env python3
"""Read-only, verified local pressure archive export for V3 analysis."""
from __future__ import annotations
import argparse,configparser,csv,hashlib,json
from pathlib import Path
import pymysql
from pymysql.cursors import Cursor

EXPECTED=('lo-infra-db-mariadb01',1,'loucka_web_ro@192.168.0.131')
START=1230768000  # 2009-01-01T00:00:00Z
END=1795564800    # 2026-11-25T00:00:00Z, exclusive; 2026 partial through Nov 24
QUERY='SELECT `dateTime`,`usUnits`,`interval`,`pressure`,`barometer`,`outTemp` FROM `loucka_reconstruction`.`archive` WHERE `dateTime` >= %s AND `dateTime` < %s ORDER BY `dateTime`'

def export(cnf:Path,out_dir:Path):
 cfg=configparser.ConfigParser(interpolation=None)
 if not cfg.read(cnf) or cfg.get('client','user',fallback='')!='loucka_web_ro':raise PermissionError('Existing read-only client config required')
 conn=pymysql.connect(read_default_file=str(cnf),read_default_group='client',database='loucka_reconstruction',autocommit=False,connect_timeout=15,read_timeout=240,write_timeout=240,cursorclass=Cursor)
 out_dir.mkdir(parents=True,exist_ok=True);dest=out_dir/'loucka-pressure-archive-2009-2026.csv'
 try:
  with conn.cursor() as cur:
   cur.execute('START TRANSACTION READ ONLY')
   cur.execute('SELECT @@hostname,@@server_id,CURRENT_USER()')
   host,sid,user=cur.fetchone()
   if (host,int(sid),user)!=EXPECTED:raise RuntimeError('Unexpected database identity')
   cur.execute('SELECT COUNT(*) FROM `loucka_reconstruction`.`archive` WHERE `dateTime` >= %s AND `dateTime` < %s',(START,END))
   expected=int(cur.fetchone()[0])
   with dest.open('w',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['dateTime_utc','usUnits','interval_min','pressure_hpa','barometer_hpa','outTemp_c'])
    cur.execute(QUERY,(START,END));count=0
    while True:
     batch=cur.fetchmany(10000)
     if not batch:break
     for r in batch:
      if int(r[1])!=16:raise ValueError('Unexpected WeeWX usUnits; do not convert without verified unit mapping')
      writer.writerow([int(r[0]),int(r[1]),r[2],r[3],r[4],r[5]]);count+=1
   if count!=expected:raise RuntimeError(f'row count mismatch {count} != {expected}')
   raw=dest.read_bytes();manifest={'database':'loucka_reconstruction.archive','server':host,'server_id':int(sid),'account':user,'transaction':'START TRANSACTION READ ONLY','query':QUERY,'utc_range':['2009-01-01T00:00:00Z','2026-11-25T00:00:00Z'],'row_count':count,'row_count_query':expected,'timestamp_filter':'all archive timestamp rows, no hourly-only MOD filter','units':{'usUnits':16,'pressure':'hPa','barometer':'hPa','outTemp':'C'},'file':dest.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
   (out_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
   return {'rows':count,'sha256':manifest['sha256'],'file':str(dest),'identity':{'server':host,'server_id':int(sid),'account':user}}
 finally:conn.rollback();conn.close()

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cnf',type=Path,default=Path('/root/meteo-loucka-ro.cnf'));ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args();print(json.dumps(export(a.cnf,a.out_dir)))
if __name__=='__main__':main()
