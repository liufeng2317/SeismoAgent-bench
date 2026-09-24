#!/usr/bin/env python3
"""Product-specific audit for the Tan et al. SUGAR releases."""
from __future__ import annotations
import csv, json, math, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
CASE_ID="2016_kaikoura_new_zealand"; SOURCE_REF="TAN2024_JB028735"; ROOT=Path(__file__).resolve().parents[1]; ANALYSIS=ROOT/"analysis"; SUP=ROOT.parent.parent/"references"/SOURCE_REF/"supplement"; UTC=timezone.utc
START=datetime(2016,12,1,tzinfo=UTC); END=datetime(2016,12,9,tzinfo=UTC); LAT_MIN,LAT_MAX=-43.5,-41.2; LON_MIN,LON_MAX=172,175.2; DEPTH_MIN,DEPTH_MAX=0,60
S10=ROOT/"TAN2024_JB028735__catalog_sugar_S10.xlsx"; S11=ROOT/"TAN2024_JB028735__catalog_sugar_relocated_S11.xlsx"; PHASE=ROOT/"TAN2024_JB028735__phases_associated.zip"; S12=SUP/"2024jb028735-sup-0005-table si-s12.xlsx"
def tag(e):return e.tag.rsplit('}',1)[-1]
def xlsx_rows(path):
 with zipfile.ZipFile(path) as z:
  shared=[]
  if 'xl/sharedStrings.xml' in z.namelist():
   root=ET.fromstring(z.read('xl/sharedStrings.xml'))
   for si in root:
    shared.append(''.join(t.text or '' for t in si.iter() if tag(t)=='t'))
  root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
  for row in root.iter():
   if tag(row)!='row':continue
   vals={}
   for c in list(row):
    if tag(c)!='c':continue
    ref=c.attrib.get('r',''); col=''.join(ch for ch in ref if ch.isalpha()); value=''
    v=next((x for x in c if tag(x)=='v'),None)
    if v is not None and v.text is not None:
     value=v.text
     if c.attrib.get('t')=='s':
      try:value=shared[int(value)]
      except (ValueError,IndexError):pass
    elif c.attrib.get('t')=='inlineStr': value=''.join(x.text or '' for x in c.iter() if tag(x)=='t')
    vals[col]=value
   if vals: yield vals
def workbook(path):
 it=xlsx_rows(path); h=next(it); headers=[h[k] for k in sorted(h,key=lambda x:(len(x),x))]
 for vals in it:
  keys=sorted(vals,key=lambda x:(len(x),x)); yield dict(zip(headers,[vals[k] for k in keys]))
def num(v):
 try:
  x=float(v); return x if math.isfinite(x) else None
 except: return None
def parse_dt(v):
 try:return datetime.fromisoformat(str(v).replace('Z','+00:00')).replace(tzinfo=UTC)
 except:return None
def s10_rows():
 for r in workbook(S10): yield {'native_event_id':r.get('ID',''),'datetime':parse_dt(r.get('Time')),'latitude_deg':num(r.get('Lat')),'longitude_deg':num(r.get('Lon')),'depth_km':num(r.get('Dep')),'magnitude':num(r.get('M')),'cluster_size':None}
def s11_rows():
 for r in workbook(S11):
  try:t=datetime(int(r['year']),int(r['month']),int(r['day']),int(r['hour']),int(r['minute']),tzinfo=UTC)+__import__('datetime').timedelta(seconds=float(r['second']))
  except:t=None
  yield {'native_event_id':r.get('id',''),'datetime':t,'latitude_deg':num(r.get('latRelocate')),'longitude_deg':num(r.get('lonRelocate')),'depth_km':num(r.get('depRelocate')),'magnitude':num(r.get('magnitude')),'cluster_size':num(r.get('events in cluster'))}
def in_time(r):return r['datetime'] is not None and START<=r['datetime']<END
def in_mask(r):return in_time(r) and all(r[k] is not None for k in ('latitude_deg','longitude_deg','depth_km')) and LAT_MIN<=r['latitude_deg']<=LAT_MAX and LON_MIN<=r['longitude_deg']<=LON_MAX and DEPTH_MIN<=r['depth_km']<=DEPTH_MAX
def stats(items):
 o={'row_count':len(items),'unique_native_event_ids':len({r['native_event_id'] for r in items}),'duplicate_native_event_ids':len(items)-len({r['native_event_id'] for r in items}),'ranges':{}}
 for k in ('latitude_deg','longitude_deg','depth_km','magnitude'):
  v=[r[k] for r in items if r[k] is not None];o['ranges'][k]=[min(v),max(v)] if v else [None,None]
 if any(r['cluster_size'] is not None for r in items):o['cluster_size_ge_10']=sum((r['cluster_size'] or 0)>=10 for r in items)
 return o
def write_norm(product,items):
 out=ANALYSIS/'derived'/product;out.mkdir(parents=True,exist_ok=True);path=out/f'{SOURCE_REF}__{product}__normalized_v1.csv'
 with path.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['event_id','native_event_id','origin_time_utc','latitude_deg','longitude_deg','depth_km','magnitude','cluster_size'])
  for i,r in enumerate(items,1):w.writerow([f'E{i:06d}',r['native_event_id'],r['datetime'].isoformat().replace('+00:00','Z') if r['datetime'] else '',r['latitude_deg'],r['longitude_deg'],r['depth_km'],r['magnitude'],r['cluster_size']])
def phase_stats():
 rows=files=0;events=set();stations=Counter();phases=Counter()
 with zipfile.ZipFile(PHASE) as z:
  for name in z.namelist():
   if not name.endswith('.dat'):continue
   files+=1
   with z.open(name) as f:
    for raw in f.read().decode('utf-8','replace').splitlines()[1:]:
     parts=raw.split()
     if len(parts)<4:continue
     rows+=1;events.add(parts[0]);stations[parts[1]]+=1;phases[parts[2]]+=1
 return {'file_count':files,'phase_rows':rows,'unique_event_ids':len(events),'stations':len(stations),'phase_types':dict(phases),'top_stations':dict(stations.most_common(20))}
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
 products={'sugar_s10':list(s10_rows()),'sugar_s11':list(s11_rows())}; result={}
 for product,rr in products.items():
  sels={'full':rr,'time_only':[r for r in rr if in_time(r)],'benchmark':[r for r in rr if in_mask(r)]}; result[product]={'counts':{k:stats(v) for k,v in sels.items()}}
  write_norm(product,rr); od=ANALYSIS/'stats'/product;od.mkdir(parents=True,exist_ok=True)
  for name,items in sels.items():(od/f'{name}_v1.json').write_text(json.dumps({'case_id':CASE_ID,'source_ref':SOURCE_REF,'product_id':product,'selection':name,'parser_version':'kaikoura-tan-v1','stats':stats(items)},indent=2)+'\n')
 result['associated_phase']=phase_stats(); (ANALYSIS/'stats'/'associated_phase').mkdir(parents=True,exist_ok=True);(ANALYSIS/'stats'/'associated_phase'/'full_v1.json').write_text(json.dumps({'case_id':CASE_ID,'source_ref':SOURCE_REF,'product_id':'associated_phase','kind':'phase','parser_version':'kaikoura-tan-v1','stats':result['associated_phase']},indent=2)+'\n')
 if S12.exists():
  s12=list(workbook(S12)); result['focal_mechanisms_s12']={'row_count':len(s12),'columns':list(s12[0]) if s12 else []};(ANALYSIS/'stats'/'focal_mechanisms_s12').mkdir(parents=True,exist_ok=True);(ANALYSIS/'stats'/'focal_mechanisms_s12'/'full_v1.json').write_text(json.dumps(result['focal_mechanisms_s12'],indent=2)+'\n')
 for product in ('sugar_s10','sugar_s11'):
  plot_event_diagnostics([r for r in products[product] if in_mask(r)],f'{product}_benchmark',f'{SOURCE_REF} · {product} benchmark')
 lines=['# TAN2024_JB028735 catalog analysis','','S10, S11, associated phases, and S12 mechanisms are separate products.','','| Product | Full rows/files | Time-only | Benchmark |','|---|---:|---:|---:|']
 for p in ('sugar_s10','sugar_s11'):lines.append(f"| `{p}` | {result[p]['counts']['full']['row_count']} | {result[p]['counts']['time_only']['row_count']} | {result[p]['counts']['benchmark']['row_count']} |")
 lines.append(f"| `associated_phase` | {result['associated_phase']['phase_rows']} phase rows / {result['associated_phase']['file_count']} files | n/a | n/a |")
 if 'focal_mechanisms_s12' in result:lines.append(f"| `focal_mechanisms_s12` | {result['focal_mechanisms_s12']['row_count']} solutions | n/a | n/a |")
 lines += ['', 'S10 is the detection/located catalog; S11 is the released GrowClust intermediate. The 41,392 article count must be reconstructed from S11 cluster size >=10. Phase rows and S12 mechanisms are not event rows.', '', 'Schemas: `docs/schemas/catalog_event.schema.yaml`; phase product remains product-specific and is not merged into event counts.']
 (ANALYSIS/'catalog_analysis.md').write_text('\n'.join(lines)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
