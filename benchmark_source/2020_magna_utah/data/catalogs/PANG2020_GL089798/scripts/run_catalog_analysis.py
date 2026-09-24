#!/usr/bin/env python3
"""Pang Magna event catalog audit with strict and normalized time handling."""
import csv,json,hashlib,math
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'analysis';REF='PANG2020_GL089798';CASE='2020_magna_utah';SOURCE=ROOT/f'{REF}__catalog_primary.txt';UTC=timezone.utc
START=datetime(2020,3,18,tzinfo=UTC);END=datetime(2020,3,26,tzinfo=UTC);LAT=(40.69,40.84);LON=(-112.14,-111.94);DEP=(-1.3,13.1)
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse_time(date,tm,normalize=False):
 try:
  y,m,d=map(int,date.split('-')); parts=tm.split(':'); h=int(parts[0]); mi=int(parts[1]); sec_text=parts[2]; ss=float(sec_text)
  if not normalize and not (0<=ss<60): return None
  base=datetime(y,m,d,h,mi,0,tzinfo=UTC)
  return base+timedelta(seconds=ss)
 except:return None

def num(x):
 try:return float(x)
 except:return None
def rows(normalize=False):
 with SOURCE.open(errors='replace') as f:
  for n,line in enumerate(f,1):
   if not line.strip() or line.startswith('#'):continue
   p=line.split();
   if len(p)<7 or not p[0][:4].isdigit():continue
   yield {'source_row':n,'native_event_id':p[6],'datetime':parse_time(p[0],p[1],normalize),'latitude_deg':num(p[2]),'longitude_deg':num(p[3]),'depth_km':num(p[4]),'magnitude':num(p[5]),'event_type':p[7] if len(p)>7 else ''}
def mask(r):return r['datetime'] and START<=r['datetime']<END and LAT[0]<=r['latitude_deg']<=LAT[1] and LON[0]<=r['longitude_deg']<=LON[1] and DEP[0]<=r['depth_km']<=DEP[1]
def stat(rr):
 o={'row_count':len(rr),'unique_native_event_ids':len({r['native_event_id'] for r in rr}),'duplicate_native_event_ids':len(rr)-len({r['native_event_id'] for r in rr}),'event_types':dict(Counter(r['event_type'] or 'UUSS/other' for r in rr)),'ranges':{}}
 for k in ('latitude_deg','longitude_deg','depth_km','magnitude'):
  v=[r[k] for r in rr if r[k] is not None];o['ranges'][k]=[min(v),max(v)] if v else [None,None]
 return o
def plot(items):
 out=A/'figures';out.mkdir(parents=True,exist_ok=True);xyz=[r for r in items if all(r.get(k) is not None for k in ('longitude_deg','latitude_deg','depth_km'))];fig,ax=plt.subplots(2,2,figsize=(7.2,6.4))
 for a,x,y,xl,yl,inv in ((ax[0,0],'longitude_deg','latitude_deg','Longitude (°E)','Latitude (°)',False),(ax[0,1],'depth_km','latitude_deg','Depth (km)','Latitude (°)',False),(ax[1,0],'longitude_deg','depth_km','Longitude (°E)','Depth (km)',True)):
  a.scatter([r[x] for r in xyz],[r[y] for r in xyz],s=5,alpha=.4,c='#2C5F8A',linewidths=0,rasterized=True);a.set(xlabel=xl,ylabel=yl);a.spines[['top','right']].set_visible(False)
  if inv:a.invert_yaxis()
 ax[1,1].hist([r['depth_km'] for r in xyz],bins='auto',orientation='horizontal',color='#009E73',edgecolor='white');ax[1,1].invert_yaxis();ax[1,1].set(xlabel='Events',ylabel='Depth (km)');ax[1,1].spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(out/'pang_benchmark_spatial_three_views_v2.png',dpi=300);plt.close(fig)
 timed=sorted([r for r in items if r['datetime']],key=lambda r:r['datetime']);days=Counter(r['datetime'].date() for r in timed);fig,ax=plt.subplots(figsize=(7.2,3.2));ds=sorted(days);ax.bar(ds,[days[d] for d in ds],color='#2C5F8A');ax.tick_params(axis='x',rotation=30);ax.set(xlabel='Origin time (UTC)',ylabel='Events per day');fig.tight_layout();fig.savefig(out/'pang_benchmark_seismicity_time_v2.png',dpi=300);plt.close(fig)
 mags=[r for r in timed if r['magnitude'] is not None];fig,ax=plt.subplots(1,2,figsize=(7.2,3.2));ax[0].hist([r['magnitude'] for r in mags],bins='auto',color='#2C5F8A',edgecolor='white');ax[0].set(xlabel='Source Mc',ylabel='Events');ax[1].scatter([r['datetime'] for r in mags],[r['magnitude'] for r in mags],s=5,c='#D55E00',alpha=.45);ax[1].set(xlabel='Origin time (UTC)',ylabel='Source Mc');fig.tight_layout();fig.savefig(out/'pang_benchmark_magnitude_diagnostics_v2.png',dpi=300);plt.close(fig)
def main():
 for d in (A/'stats',A/'figures',A/'derived'):d.mkdir(parents=True,exist_ok=True)
 allr=list(rows(False));norm=list(rows(True));sels={'full':allr,'time_only':[r for r in allr if r['datetime'] and START<=r['datetime']<END],'benchmark':[r for r in allr if mask(r)]};result={'strict':{k:stat(v) for k,v in sels.items()},'normalized':{'full':stat(norm),'time_only':stat([r for r in norm if r['datetime'] and START<=r['datetime']<END]),'benchmark':stat([r for r in norm if mask(r)])}}
 for n,v in result['strict'].items():(A/'stats').mkdir(exist_ok=True);(A/'stats'/f'{n}_strict_v1.json').write_text(json.dumps({'case_id':CASE,'source_ref':REF,'product_id':'primary_event_catalog','selection':n,'stats':v},indent=2)+'\n')
 plot(sels['benchmark']);(A/'catalog_analysis.md').write_text(f'# {REF} catalog analysis\\n\\nPang ISC event-level release. Strict parsing preserves source rows with canonical seconds; normalized parsing is a sensitivity only.\\n\\n| Selection | Strict rows | Mc > -4 | Template-Matching |\\n|---|---:|---:|---:|\\n| Full | {result["strict"]["full"]["row_count"]} | {sum(r["magnitude"] is not None and r["magnitude"]>-4 for r in allr)} | {sum(r["event_type"]=="Template-Matching" for r in allr)} |\\n| Benchmark | {result["strict"]["benchmark"]["row_count"]} | {sum(r["magnitude"] is not None and r["magnitude"]>-4 for r in sels["benchmark"])} | {sum(r["event_type"]=="Template-Matching" for r in sels["benchmark"])} |\\n\\nSchema: `docs/schemas/catalog_event.schema.yaml`.\\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
