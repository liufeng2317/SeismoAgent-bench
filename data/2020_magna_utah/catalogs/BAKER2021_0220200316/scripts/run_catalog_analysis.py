#!/usr/bin/env python3
"""Baker Magna pick-level release: event collapse, pick inventory and figures."""
import csv,json,hashlib
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'analysis';REF='BAKER2021_0220200316';CASE='2020_magna_utah';SOURCE=ROOT/f'{REF}__catalog_picks.csv';UTC=timezone.utc
START=datetime(2020,3,18,tzinfo=UTC);END=datetime(2020,3,26,tzinfo=UTC);LAT=(40.69,40.84);LON=(-112.14,-111.94);DEP=(-1.3,13.1)
def num(x):
 try:return float(x)
 except:return None
def dt(x):
 try:return datetime.fromisoformat(x.replace('Z','+00:00')).replace(tzinfo=UTC)
 except:return None
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read():
 with SOURCE.open() as f:return list(csv.DictReader(f))
def events(rows):
 out={}
 for r in rows:
  k=r['event_number'];
  if k not in out:out[k]={'native_event_id':r['catalog_evid'],'datetime':dt(r['origin_time']),'latitude_deg':num(r['event_latitude']),'longitude_deg':num(r['event_longitude']),'depth_km':num(r['event_depth']),'magnitude':num(r['magnitude']),'magnitude_type':r['magnitude_type'],'pick_count':0}
  out[k]['pick_count']+=1
 return list(out.values())
def mask(r):return r['datetime'] and START<=r['datetime']<END and LAT[0]<=r['latitude_deg']<=LAT[1] and LON[0]<=r['longitude_deg']<=LON[1] and DEP[0]<=r['depth_km']<=DEP[1]
def stat(rr):
 o={'row_count':len(rr),'unique_native_event_ids':len({r['native_event_id'] for r in rr}),'duplicate_native_event_ids':len(rr)-len({r['native_event_id'] for r in rr}),'pick_rows':sum(r.get('pick_count',0) for r in rr),'magnitude_types':dict(Counter(r.get('magnitude_type','') for r in rr)),'ranges':{}}
 for k in ('latitude_deg','longitude_deg','depth_km','magnitude'):
  v=[r[k] for r in rr if r[k] is not None];o['ranges'][k]=[min(v),max(v)] if v else [None,None]
 return o
def plot(items):
 out=A/'figures';out.mkdir(parents=True,exist_ok=True);xyz=[r for r in items if all(r.get(k) is not None for k in ('longitude_deg','latitude_deg','depth_km'))];fig,ax=plt.subplots(2,2,figsize=(7.2,6.4))
 for a,x,y,xl,yl,inv in ((ax[0,0],'longitude_deg','latitude_deg','Longitude (°E)','Latitude (°)',False),(ax[0,1],'depth_km','latitude_deg','Depth (km)','Latitude (°)',False),(ax[1,0],'longitude_deg','depth_km','Longitude (°E)','Depth (km)',True)):
  a.scatter([r[x] for r in xyz],[r[y] for r in xyz],s=5,alpha=.4,c='#2C5F8A',linewidths=0,rasterized=True);a.set(xlabel=xl,ylabel=yl);a.spines[['top','right']].set_visible(False)
  if inv:a.invert_yaxis()
 ax[1,1].hist([r['depth_km'] for r in xyz],bins='auto',orientation='horizontal',color='#009E73',edgecolor='white');ax[1,1].invert_yaxis();ax[1,1].set(xlabel='Events',ylabel='Depth (km)');ax[1,1].spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(out/'baker_benchmark_spatial_three_views_v2.png',dpi=300);plt.close(fig)
 timed=sorted([r for r in items if r['datetime']],key=lambda r:r['datetime']);days=Counter(r['datetime'].date() for r in timed);fig,ax=plt.subplots(figsize=(7.2,3.2));ds=sorted(days);ax.bar(ds,[days[d] for d in ds],color='#2C5F8A');ax.tick_params(axis='x',rotation=30);ax.set(xlabel='Origin time (UTC)',ylabel='Events per day');fig.tight_layout();fig.savefig(out/'baker_benchmark_seismicity_time_v2.png',dpi=300);plt.close(fig)
 mags=[r for r in timed if r['magnitude'] is not None];fig,ax=plt.subplots(1,2,figsize=(7.2,3.2));ax[0].hist([r['magnitude'] for r in mags],bins='auto',color='#2C5F8A',edgecolor='white');ax[0].set(xlabel='Source magnitude',ylabel='Events');ax[1].scatter([r['datetime'] for r in mags],[r['magnitude'] for r in mags],s=5,c='#D55E00',alpha=.45);ax[1].set(xlabel='Origin time (UTC)',ylabel='Source magnitude');fig.tight_layout();fig.savefig(out/'baker_benchmark_magnitude_diagnostics_v2.png',dpi=300);plt.close(fig)
def main():
 for d in (A/'stats',A/'figures',A/'derived'):d.mkdir(parents=True,exist_ok=True)
 rr=read();ee=events(rr);sels={'full':ee,'time_only':[r for r in ee if r['datetime'] and START<=r['datetime']<END],'benchmark':[r for r in ee if mask(r)]};result={'pick_rows':len(rr),'event_counts':{k:stat(v) for k,v in sels.items()},'phase_types':dict(Counter(r['phase'] for r in rr))}
 for n,v in sels.items():(A/'stats').mkdir(exist_ok=True);(A/'stats'/f'{n}_events_v1.json').write_text(json.dumps({'case_id':CASE,'source_ref':REF,'product_id':'event_collapse','selection':n,'stats':stat(v)},indent=2)+'\n')
 (A/'stats'/'picks_full_v1.json').write_text(json.dumps({'case_id':CASE,'source_ref':REF,'product_id':'pick_rows','stats':{'row_count':len(rr),'phase_types':result['phase_types'],'stations':len({(r['network'],r['station']) for r in rr})}},indent=2)+'\n');plot(sels['benchmark']);(A/'catalog_analysis.md').write_text(f'# {REF} catalog analysis\n\nBaker is a pick-level release. Event counts are after collapsing repeated pick rows by `event_number`; pick rows remain a separate denominator.\n\n| Product | Full | Time-only | Benchmark |\n|---|---:|---:|---:|\n| Event collapse | {len(ee)} | {len(sels["time_only"])} | {len(sels["benchmark"])} |\n| Pick rows | {len(rr):,} | n/a | {sum(r["pick_count"] for r in sels["benchmark"]):,} |\n\nPhase rows: `{result["phase_types"]}`; stations: `{len({(r["network"],r["station"]) for r in rr})}`. Schema: `docs/schemas/catalog_event.schema.yaml`.\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
