#!/usr/bin/env python3
import csv,json,hashlib
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/'analysis'; CASE='2019_ridgecrest_california'; REF='SHELLY2020_0220190309'; UTC=timezone.utc
EVENT=ROOT/'raw_article'/f'{REF}__catalog_DataS1.txt'; PHASE=ROOT/'raw'/'Ridgecrest_2019_correlation_phase_arrivals.csv'
START=datetime(2019,7,4,tzinfo=UTC); END=datetime(2019,7,7,tzinfo=UTC); LAT=(35.45,36.05); LON=(-117.90,-117.20); DEP=(0,20)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def num(x):
 try:return float(x)
 except:return None
def dt(x):
 try:return datetime.fromisoformat(x.replace('Z','+00:00')).replace(tzinfo=UTC)
 except:return None
def rows():
 for n,line in enumerate(EVENT.open(errors='replace'),1):
  if not line.strip() or line.lstrip().startswith('#'):continue
  p=line.split()
  if len(p)<11:continue
  yield {'native_event_id':p[10],'datetime':dt(f'{p[0]}-{p[1]}-{p[2]}T{p[3]}:{p[4]}:{p[5]}Z'),'latitude_deg':num(p[6]),'longitude_deg':num(p[7]),'depth_km':num(p[8]),'magnitude':num(p[9]),'source_row':n}
def mask(r):return r['datetime'] and START<=r['datetime']<END and LAT[0]<=r['latitude_deg']<=LAT[1] and LON[0]<=r['longitude_deg']<=LON[1] and DEP[0]<=r['depth_km']<=DEP[1]
def stat(rr):
 o={'row_count':len(rr),'unique_native_event_ids':len({r['native_event_id'] for r in rr}),'duplicate_native_event_ids':len(rr)-len({r['native_event_id'] for r in rr}),'ranges':{}}
 for k in ('latitude_deg','longitude_deg','depth_km','magnitude'):
  v=[r[k] for r in rr if r[k] is not None];o['ranges'][k]=[min(v),max(v)] if v else [None,None]
 return o
def phase_stat():
 n=0;ids=set();stations=Counter();ph=Counter()
 with PHASE.open(errors='replace') as f:
  for r in csv.DictReader(f):
   n+=1;ids.add(r.get('match_id',''));stations[f"{r.get('network','')}.{r.get('station','')}"]+=1;ph[r.get('phase','')]+=1
 return {'row_count':n,'unique_match_ids':len(ids),'network_stations':len(stations),'phase_types':dict(ph),'top_stations':dict(stations.most_common(20))}
def plot_event_diagnostics(items, stem, title):
    """Write the four benchmark event diagnostics; non-event products never call this."""
    out=A/"figures"; out.mkdir(parents=True,exist_ok=True)
    for old in out.glob(f"{stem}_overview_v1.*"): old.unlink()
    valid_xyz=[r for r in items if all(r.get(k) is not None for k in ("longitude_deg","latitude_deg","depth_km"))]
    if valid_xyz:
        fig,ax=plt.subplots(2,2,figsize=(7.2,6.4)); color="#2C5F8A"
        panels=((ax[0,0],"longitude_deg","latitude_deg","Longitude (°E)","Latitude (°)",False),
                (ax[0,1],"depth_km","latitude_deg","Depth (km)","Latitude (°)",True),
                (ax[1,0],"longitude_deg","depth_km","Longitude (°E)","Depth (km)",True))
        for a,x,y,xlab,ylab,invert_depth in panels:
            a.scatter([r[x] for r in valid_xyz],[r[y] for r in valid_xyz],s=4,alpha=.38,c=color,linewidths=0,rasterized=True)
            a.set(xlabel=xlab,ylabel=ylab); a.spines[["top","right"]].set_visible(False)
            if invert_depth:
                if x!="depth_km": a.invert_yaxis()
        depths=[r["depth_km"] for r in items if r.get("depth_km") is not None]
        if depths:
            ax[1,1].hist(depths,bins="auto",orientation="horizontal",color="#009E73",alpha=.85,edgecolor="white",linewidth=.3)
            ax[1,1].invert_yaxis(); ax[1,1].set(xlabel="Events",ylabel="Depth (km)")
        else:
            ax[1,1].axis("off")
        ax[1,1].text(.98,.04,f"n = {len(valid_xyz):,}",transform=ax[1,1].transAxes,fontsize=8,ha="right",va="bottom")
        fig.suptitle(title,x=.07,ha="left",fontsize=10); fig.tight_layout(); fig.savefig(out/f"{stem}_spatial_three_views_v2.png",dpi=300,bbox_inches="tight"); plt.close(fig)
    timed=sorted((r for r in items if r.get("datetime") is not None),key=lambda r:r["datetime"])
    if timed:
        daily=Counter(r["datetime"].date() for r in timed); days=sorted(daily)
        fig,ax=plt.subplots(figsize=(7.2,3.2)); ax.bar(days,[daily[d] for d in days],width=.85,color="#2C5F8A",alpha=.85); ax.set(xlabel="Origin time (UTC)",ylabel="Events per day"); ax.spines[["top","right"]].set_visible(False); ax.tick_params(axis="x",rotation=30); fig.tight_layout(); fig.savefig(out/f"{stem}_seismicity_time_v2.png",dpi=300,bbox_inches="tight"); plt.close(fig)
    mags=[r for r in timed if r.get("magnitude") is not None]
    if mags:
        fig,ax=plt.subplots(1,2,figsize=(7.2,3.2)); values=[r["magnitude"] for r in mags]
        ax[0].hist(values,bins="auto",color="#2C5F8A",alpha=.88,edgecolor="white",linewidth=.3); ax[0].set(xlabel="Native magnitude",ylabel="Events"); ax[0].spines[["top","right"]].set_visible(False)
        ax[1].scatter([r["datetime"] for r in mags],values,s=4,c="#D55E00",alpha=.4,linewidths=0,rasterized=True); ax[1].set(xlabel="Origin time (UTC)",ylabel="Native magnitude"); ax[1].spines[["top","right"]].set_visible(False); ax[1].tick_params(axis="x",rotation=30)
        fig.tight_layout(); fig.savefig(out/f"{stem}_magnitude_diagnostics_v2.png",dpi=300,bbox_inches="tight"); plt.close(fig)

def main():
 for d in (A/'stats',A/'figures',A/'derived'):d.mkdir(parents=True,exist_ok=True)
 rr=list(rows()); sels={'full':rr,'time_only':[r for r in rr if r['datetime'] and START<=r['datetime']<END],'benchmark':[r for r in rr if mask(r)]}; ps=phase_stat()
 for k,v in sels.items():(A/'stats'/f'event_{k}_v1.json').write_text(json.dumps({'case_id':CASE,'source_ref':REF,'product_id':'DataS1_event_catalog','selection':k,'source_sha256':sha(EVENT),'stats':stat(v)},indent=2)+'\n')
 (A/'stats'/'phase_arrivals_full_v1.json').write_text(json.dumps({'case_id':CASE,'source_ref':REF,'product_id':'correlation_phase_arrivals','source_sha256':sha(PHASE),'stats':ps},indent=2)+'\n')
 items=sels['benchmark']; plot_event_diagnostics(items,'shelly_DataS1_benchmark',f'{REF} · DataS1 benchmark')
 lines=['# '+REF+' catalog analysis','','`DataS1` is the event catalog; the correlation table is a separate pick-level product and is not included in event counts.','','| Product | Full | Time-only | Benchmark |','|---|---:|---:|---:|',f"| DataS1 event catalog | {len(rr)} | {len(sels['time_only'])} | {len(sels['benchmark'])} |",f"| Correlation phase arrivals | {ps['row_count']} rows | n/a | n/a |",'','Schema: `docs/schemas/catalog_event.schema.yaml`; phase arrivals retain their product-specific fields.']
 (A/'catalog_analysis.md').write_text('\n'.join(lines)+'\n'); print(json.dumps({'event_catalog':{k:stat(v) for k,v in sels.items()},'phase_arrivals':ps},indent=2))
if __name__=='__main__':main()
