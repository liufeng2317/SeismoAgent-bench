#!/usr/bin/env python3
"""GeoNet/GNS operational baseline audit for Kaikōura."""
from __future__ import annotations
import csv,json,hashlib,math
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
CASE_ID="2016_kaikoura_new_zealand"; SOURCE_REF="GEONET_2016_KAIKOURA"; ROOT=Path(__file__).resolve().parents[1]; ANALYSIS=ROOT/"analysis"; UTC=timezone.utc
START=datetime(2016,12,1,tzinfo=UTC); END=datetime(2016,12,9,tzinfo=UTC); LAT_MIN,LAT_MAX=-43.5,-41.2; LON_MIN,LON_MAX=172,175.2; DEPTH_MIN,DEPTH_MAX=0,60
PRODUCTS={"operational_full":ROOT/"GEONET_2016_KAIKOURA__catalog_operational_full.txt","operational_benchmark":ROOT/"GEONET_2016_KAIKOURA__catalog_operational_benchmark.txt"}
def sha256(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def num(v):
 try:
  x=float(v); return x if math.isfinite(x) else None
 except: return None
def parse_dt(v):
 try:return datetime.fromisoformat(v.replace('Z','+00:00')).replace(tzinfo=UTC)
 except:return None
def rows(path):
 with path.open(encoding='utf-8',errors='replace') as f:
  header=f.readline().lstrip('#').strip().split('|')
  header=[x.strip() for x in header]
  for no,line in enumerate(f,2):
   if not line.strip():continue
   vals=[x.strip() for x in line.rstrip('\n').split('|')]
   if len(vals)!=len(header):continue
   r=dict(zip(header,vals)); yield {'source_row':no,'native_event_id':r.get('EventID',''),'datetime':parse_dt(r.get('Time','')),'latitude_deg':num(r.get('Latitude')),'longitude_deg':num(r.get('Longitude')),'depth_km':num(r.get('Depth/km')),'magnitude':num(r.get('Magnitude')),'magnitude_type':r.get('MagType',''),'event_type':r.get('EventType',''),'raw':r}
def in_time(r):return r['datetime'] is not None and START<=r['datetime']<END
def in_mask(r):return in_time(r) and all(r[k] is not None for k in ('latitude_deg','longitude_deg','depth_km')) and LAT_MIN<=r['latitude_deg']<=LAT_MAX and LON_MIN<=r['longitude_deg']<=LON_MAX and DEPTH_MIN<=r['depth_km']<=DEPTH_MAX
def stats(items):
 o={'row_count':len(items),'unique_native_event_ids':len({r['native_event_id'] for r in items}),'duplicate_native_event_ids':len(items)-len({r['native_event_id'] for r in items}),'magnitude_types':dict(Counter(r['magnitude_type'] for r in items)),'event_types':dict(Counter(r['event_type'] for r in items)),'ranges':{}}
 for k in ('latitude_deg','longitude_deg','depth_km','magnitude'):
  v=[r[k] for r in items if r[k] is not None];o['ranges'][k]=[min(v),max(v)] if v else [None,None]
 return o
def plot_event_diagnostics(items, stem, title):
    """Write the four benchmark event diagnostics; non-event products never call this."""
    out=ANALYSIS/"figures"; out.mkdir(parents=True,exist_ok=True)
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
 for d in (ANALYSIS/'derived',ANALYSIS/'stats',ANALYSIS/'figures'):d.mkdir(parents=True,exist_ok=True)
 all_result={}
 for product,path in PRODUCTS.items():
  rr=list(rows(path)); sels={'full':rr,'time_only':[r for r in rr if in_time(r)],'benchmark':[r for r in rr if in_mask(r)]}
  all_result[product]={'source_sha256':sha256(path),'counts':{k:stats(v) for k,v in sels.items()}}
  od=ANALYSIS/'stats'/product;od.mkdir(parents=True,exist_ok=True)
  for name,items in sels.items():(od/f'{name}_v1.json').write_text(json.dumps({'case_id':CASE_ID,'source_ref':SOURCE_REF,'product_id':product,'selection':name,'parser_version':'kaikoura-geonet-v1','source_path':path.name,'source_sha256':sha256(path),'stats':stats(items)},indent=2)+'\n')
  if product=='operational_benchmark':
   out=ANALYSIS/'derived'/product;out.mkdir(parents=True,exist_ok=True)
   with (out/f'{SOURCE_REF}__{product}__normalized_v1.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['event_id','native_event_id','origin_time_utc','latitude_deg','longitude_deg','depth_km','magnitude','magnitude_type','event_type','source_row']);
    for i,r in enumerate(sels['benchmark'],1):w.writerow([f'E{i:06d}',r['native_event_id'],r['datetime'].isoformat().replace('+00:00','Z'),r['latitude_deg'],r['longitude_deg'],r['depth_km'],r['magnitude'],r['magnitude_type'],r['event_type'],r['source_row']])
  if product=='operational_benchmark': plot_event_diagnostics(sels['benchmark'],'geonet_operational_benchmark',f'{SOURCE_REF} · operational benchmark')
 lines=['# GEONET_2016_KAIKOURA catalog analysis','','GeoNet is retained as the official operational Q3 baseline; it is not merged with research catalogs.','','| Product | Full | Time-only | Benchmark |','|---|---:|---:|---:|']
 for p,v in all_result.items():lines.append(f"| `{p}` | {v['counts']['full']['row_count']} | {v['counts']['time_only']['row_count']} | {v['counts']['benchmark']['row_count']} |")
 lines += ['', 'Native EventID, magnitude types, and event types are preserved. Schema: `docs/schemas/catalog_event.schema.yaml`.']
 (ANALYSIS/'catalog_analysis.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(all_result,indent=2))
if __name__=='__main__':main()
