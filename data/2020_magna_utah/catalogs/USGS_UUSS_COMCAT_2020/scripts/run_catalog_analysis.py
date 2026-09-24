#!/usr/bin/env python3
"""Magna official UUSS/ComCat event baseline analysis."""
import csv,json,hashlib
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'analysis';REF='USGS_UUSS_COMCAT_2020';CASE='2020_magna_utah';UTC=timezone.utc
START=datetime(2020,3,18,tzinfo=UTC);END=datetime(2020,3,26,tzinfo=UTC);LAT=(40.69,40.84);LON=(-112.14,-111.94);DEP=(-1.3,13.1)
FILES={'operational_full':ROOT/f'{REF}__catalog_operational_full.csv','operational_benchmark':ROOT/f'{REF}__catalog_operational_benchmark.csv'}
def dt(x):
 try:return datetime.fromisoformat(x.replace('Z','+00:00')).astimezone(UTC)
 except:return None
def num(x):
 try:return float(x)
 except:return None
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def rows(p):
 with p.open() as f:
  for r in csv.DictReader(f):yield {'native_event_id':r.get('id',''),'datetime':dt(r.get('time','')),'latitude_deg':num(r.get('latitude')),'longitude_deg':num(r.get('longitude')),'depth_km':num(r.get('depth')),'magnitude':num(r.get('mag')),'magnitude_type':r.get('magType',''),'event_type':r.get('type',''),'raw':r}
def mask(r):return r['datetime'] and START<=r['datetime']<END and LAT[0]<=r['latitude_deg']<=LAT[1] and LON[0]<=r['longitude_deg']<=LON[1] and DEP[0]<=r['depth_km']<=DEP[1]
def stat(rr):
 o={'row_count':len(rr),'unique_native_event_ids':len({r['native_event_id'] for r in rr}),'duplicate_native_event_ids':len(rr)-len({r['native_event_id'] for r in rr}),'magnitude_types':dict(Counter(r['magnitude_type'] for r in rr)),'event_types':dict(Counter(r['event_type'] for r in rr)),'ranges':{}}
 for k in ('latitude_deg','longitude_deg','depth_km','magnitude'):
  v=[r[k] for r in rr if r[k] is not None];o['ranges'][k]=[min(v),max(v)] if v else [None,None]
 return o
def plot(items,stem,title):
 out=A/'figures';out.mkdir(parents=True,exist_ok=True);xyz=[r for r in items if all(r.get(k) is not None for k in ('longitude_deg','latitude_deg','depth_km'))]
 if not xyz:return
 fig,ax=plt.subplots(2,2,figsize=(7.2,6.4));
 for a,x,y,xl,yl,inv in ((ax[0,0],'longitude_deg','latitude_deg','Longitude (°E)','Latitude (°)',False),(ax[0,1],'depth_km','latitude_deg','Depth (km)','Latitude (°)',False),(ax[1,0],'longitude_deg','depth_km','Longitude (°E)','Depth (km)',True)):
  a.scatter([r[x] for r in xyz],[r[y] for r in xyz],s=5,alpha=.4,c='#2C5F8A',linewidths=0,rasterized=True);a.set(xlabel=xl,ylabel=yl);a.spines[['top','right']].set_visible(False)
  if inv:a.invert_yaxis()
 ax[1,1].hist([r['depth_km'] for r in xyz],bins='auto',orientation='horizontal',color='#009E73',edgecolor='white',linewidth=.3);ax[1,1].invert_yaxis();ax[1,1].set(xlabel='Events',ylabel='Depth (km)');ax[1,1].spines[['top','right']].set_visible(False);ax[1,1].text(.98,.04,f'n = {len(xyz):,}',transform=ax[1,1].transAxes,ha='right',va='bottom',fontsize=8);fig.suptitle(title,x=.07,ha='left');fig.tight_layout();fig.savefig(out/f'{stem}_spatial_three_views_v2.png',dpi=300);plt.close(fig)
 timed=sorted([r for r in items if r['datetime']],key=lambda r:r['datetime']);days=Counter(r['datetime'].date() for r in timed);fig,ax=plt.subplots(figsize=(7.2,3.2));ds=sorted(days);ax.bar(ds,[days[d] for d in ds],color='#2C5F8A');ax.set(xlabel='Origin time (UTC)',ylabel='Events per day');ax.tick_params(axis='x',rotation=30);ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(out/f'{stem}_seismicity_time_v2.png',dpi=300);plt.close(fig)
 mags=[r for r in timed if r['magnitude'] is not None];fig,ax=plt.subplots(1,2,figsize=(7.2,3.2));ax[0].hist([r['magnitude'] for r in mags],bins='auto',color='#2C5F8A',edgecolor='white');ax[0].set(xlabel='Native magnitude',ylabel='Events');ax[1].scatter([r['datetime'] for r in mags],[r['magnitude'] for r in mags],s=5,c='#D55E00',alpha=.45,linewidths=0);ax[1].set(xlabel='Origin time (UTC)',ylabel='Native magnitude');[a.spines[['top','right']].set_visible(False) for a in ax];fig.tight_layout();fig.savefig(out/f'{stem}_magnitude_diagnostics_v2.png',dpi=300);plt.close(fig)
def main():
 for d in (A/'stats',A/'figures',A/'derived'):d.mkdir(parents=True,exist_ok=True)
 result={}
 for product,p in FILES.items():
  rr=list(rows(p)); sels={'full':rr,'time_only':[r for r in rr if r['datetime'] and START<=r['datetime']<END],'benchmark':[r for r in rr if mask(r)]};result[product]={'source_sha256':sha(p),'counts':{k:stat(v) for k,v in sels.items()}}
  for n,v in sels.items():(A/'stats'/product).mkdir(parents=True,exist_ok=True);(A/'stats'/product/f'{n}_v1.json').write_text(json.dumps({'case_id':CASE,'source_ref':REF,'product_id':product,'selection':n,'stats':stat(v)},indent=2)+'\n')
  plot(sels['benchmark'],product,'USGS_UUSS_COMCAT_2020 · '+product+' benchmark')
 (A/'catalog_analysis.md').write_text('# USGS_UUSS_COMCAT_2020 catalog analysis\n\nOfficial UUSS/ComCat routine baseline; source-native event types and magnitude scales are preserved.\n\n| Product | Full | Time-only | Benchmark |\n|---|---:|---:|---:|\n'+''.join(f"| `{p}` | {v['counts']['full']['row_count']} | {v['counts']['time_only']['row_count']} | {v['counts']['benchmark']['row_count']} |\\n" for p,v in result.items())+'\nSchemas: `docs/schemas/catalog_event.schema.yaml`.\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
