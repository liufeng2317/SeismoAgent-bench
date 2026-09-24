#!/usr/bin/env python3
"""Product-specific audit for the Lanza et al. QuakeML catalog.

The file contains two origin products per event in places: SIMUL and the
HypoDD-relocated origin. The preferred origin is selected, rather than
flattening both into one event table.
"""
from __future__ import annotations
import csv, hashlib, json, math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
CASE_ID="2016_kaikoura_new_zealand"; SOURCE_REF="LANZA2019_GL082780"; ROOT=Path(__file__).resolve().parents[1]; ANALYSIS=ROOT/"analysis"; UTC=timezone.utc
SOURCE=ROOT/"raw"/"grl59060-sup-0003-ds01.xml"
START=datetime(2016,12,1,tzinfo=UTC); END=datetime(2016,12,9,tzinfo=UTC); LAT_MIN,LAT_MAX=-43.5,-41.2; LON_MIN,LON_MAX=172.0,175.2; DEPTH_MIN,DEPTH_MAX=0.0,60.0

def local(tag): return tag.rsplit('}',1)[-1]
def text(el, name):
    for x in el.iter():
        if local(x.tag)==name and x.text and x.text.strip(): return x.text.strip()
    return None
def direct(el, name):
    for x in list(el):
        if local(x.tag)==name: return x
    return None
def val(el,name):
    x=direct(el,name)
    return text(x,'value') if x is not None else None
def num(v):
    try:
        x=float(v); return x if math.isfinite(x) else None
    except (TypeError,ValueError): return None
def dt(v):
    try:return datetime.fromisoformat(v.replace('Z','+00:00')).astimezone(UTC)
    except (TypeError,ValueError,AttributeError):return None
def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def parse_origin(o):
    method=text(o,'methodID') or ''
    return {'origin_id':o.attrib.get('publicID',''),'datetime':dt(val(o,'time')),'latitude_deg':num(val(o,'latitude')),'longitude_deg':num(val(o,'longitude')),'depth_km':(num(val(o,'depth'))/1000 if num(val(o,'depth')) is not None else None),'method_id':method,'method':('HypoDD' if 'hypodd' in method.lower() else ('SIMUL' if 'simul' in method.lower() else method or 'unknown')),'used_phase_count':num(text(direct(o,'quality'),'usedPhaseCount') if direct(o,'quality') is not None else None)}
def events():
    for _,elem in ET.iterparse(SOURCE,events=('end',)):
        if local(elem.tag)!='event': continue
        event_id=elem.attrib.get('publicID',''); preferred=text(elem,'preferredOriginID'); origins=[]
        for o in elem.iter():
            if local(o.tag)=='origin': origins.append(parse_origin(o))
        chosen=next((o for o in origins if o['origin_id']==preferred), None) or (origins[0] if origins else None)
        if chosen:
            chosen['native_event_id']=event_id; chosen['preferred_origin_id']=preferred; chosen['origin_count']=len(origins); yield chosen
        elem.clear()
def in_time(r):return r['datetime'] is not None and START<=r['datetime']<END
def in_mask(r):return in_time(r) and all(r[k] is not None for k in ('latitude_deg','longitude_deg','depth_km')) and LAT_MIN<=r['latitude_deg']<=LAT_MAX and LON_MIN<=r['longitude_deg']<=LON_MAX and DEPTH_MIN<=r['depth_km']<=DEPTH_MAX
def stats(items):
    o={'row_count':len(items),'unique_native_event_ids':len({r['native_event_id'] for r in items}),'duplicate_native_event_ids':len(items)-len({r['native_event_id'] for r in items}),'origin_methods':dict(Counter(r['method'] for r in items)),'ranges':{}}
    for k in ('latitude_deg','longitude_deg','depth_km'):
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
    rr=list(events()); sels={'full':rr,'time_only':[r for r in rr if in_time(r)],'benchmark':[r for r in rr if in_mask(r)]}
    result={'case_id':CASE_ID,'source_ref':SOURCE_REF,'source_path':str(SOURCE.relative_to(ROOT)),'source_sha256':sha256(SOURCE),'parser_version':'kaikoura-lanza-quakeml-v1','origin_selection':'preferredOriginID; fallback first origin','counts':{k:stats(v) for k,v in sels.items()}}
    out=ANALYSIS/'derived'/SOURCE_REF;out.mkdir(parents=True,exist_ok=True)
    with (out/f'{SOURCE_REF}__preferred_origins__normalized_v1.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['event_id','native_event_id','preferred_origin_id','origin_time_utc','latitude_deg','longitude_deg','depth_km','origin_method','used_phase_count','origin_count'])
        for i,r in enumerate(sels['benchmark'],1):w.writerow([f'E{i:06d}',r['native_event_id'],r['preferred_origin_id'],r['datetime'].isoformat().replace('+00:00','Z') if r['datetime'] else '',r['latitude_deg'],r['longitude_deg'],r['depth_km'],r['method'],r['used_phase_count'],r['origin_count']])
    for name,items in sels.items():
        d=ANALYSIS/'stats'/SOURCE_REF;d.mkdir(parents=True,exist_ok=True)
        (d/f'{name}_v1.json').write_text(json.dumps({'case_id':CASE_ID,'source_ref':SOURCE_REF,'product_id':'preferred_origins','selection':name,'parser_version':result['parser_version'],'source_path':result['source_path'],'source_sha256':result['source_sha256'],'stats':stats(items)},indent=2)+'\n')
    plot_event_diagnostics(sels['benchmark'],'lanza_preferred_origins_benchmark',f'{SOURCE_REF} · preferred origins benchmark')
    lines=['# LANZA2019_GL082780 catalog analysis','','This QuakeML contains multiple origin solutions per event. The parser retains the `preferredOriginID` solution and does not merge SIMUL and HypoDD origins as independent events.','', '| Selection | Events | HypoDD | SIMUL |','|---|---:|---:|---:|']
    for name,items in sels.items(): c=Counter(r['method'] for r in items);lines.append(f"| `{name}` | {len(items)} | {c.get('HypoDD',0)} | {c.get('SIMUL',0)} |")
    lines += ['',f'Input: `{result["source_path"]}`; SHA-256 `{result["source_sha256"]}`.','Depth is converted from QuakeML metres to kilometres. Schema: `docs/schemas/catalog_event.schema.yaml`.']
    (ANALYSIS/'catalog_analysis.md').write_text('\n'.join(lines)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
