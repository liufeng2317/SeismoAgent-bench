#!/usr/bin/env python3
"""Product-specific audit for the Chamberlain corrected and legacy releases."""
from __future__ import annotations
import csv, hashlib, json, math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CASE_ID="2016_kaikoura_new_zealand"
SOURCE_REF="CHAMBERLAIN2021_JB022304"
ROOT=Path(__file__).resolve().parents[1]
ANALYSIS=ROOT/"analysis"
UTC=timezone.utc
START=datetime(2016,12,1,tzinfo=UTC); END=datetime(2016,12,9,tzinfo=UTC)
LAT_MIN,LAT_MAX=-43.5,-41.2; LON_MIN,LON_MAX=172.0,175.2; DEPTH_MIN,DEPTH_MAX=0.0,60.0
PRODUCTS={
 "growclust_corrected":ROOT/"CHAMBERLAIN2021_JB022304__catalog_growclust_corrected_focal_mechanisms.csv",
 "growclust_legacy":ROOT/"CHAMBERLAIN2021_JB022304__catalog_growclust.csv",
}

def sha256(path):
 h=hashlib.sha256();
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def num(v):
 try:
  x=float(v); return x if math.isfinite(x) else None
 except (TypeError,ValueError): return None
def dt(v):
 if not v: return None
 try:
  x=datetime.fromisoformat(v.replace("Z","+00:00")); return x.replace(tzinfo=UTC) if x.tzinfo is None else x.astimezone(UTC)
 except ValueError: return None
def rows(path):
 with path.open(encoding="utf-8",errors="replace",newline="") as f:
  for source_row,r in enumerate(csv.DictReader(f),1):
   yield {"source_row":source_row,"native_event_id":r.get("event_id") or "","datetime":dt(r.get("time")),"latitude_deg":num(r.get("latitude")),"longitude_deg":num(r.get("longitude")),"depth_km":(num(r.get("depth"))/1000 if num(r.get("depth")) is not None else None),"magnitude":num(r.get("magnitude")),"local_magnitude":num(r.get("local_magnitude")),"strike":num(r.get("strike")),"dip":num(r.get("dip")),"rake":num(r.get("rake")),"slip_style":r.get("Slip style") or "Unknown","raw":r}
def in_window(r): return r["datetime"] is not None and START<=r["datetime"]<END
def in_mask(r): return in_window(r) and all(r[k] is not None for k in ("latitude_deg","longitude_deg","depth_km")) and LAT_MIN<=r["latitude_deg"]<=LAT_MAX and LON_MIN<=r["longitude_deg"]<=LON_MAX and DEPTH_MIN<=r["depth_km"]<=DEPTH_MAX
def stats(items):
 out={"row_count":len(items),"unique_native_event_ids":len({r["native_event_id"] for r in items if r["native_event_id"]}),"duplicate_native_event_ids":len(items)-len({r["native_event_id"] for r in items if r["native_event_id"]}),"missing_magnitude":sum(r["magnitude"] is None for r in items),"complete_focal_mechanisms":sum(all(r[k] is not None for k in ("strike","dip","rake")) for r in items),"slip_styles":dict(Counter(r["slip_style"] for r in items)),"ranges":{}}
 for k in ("latitude_deg","longitude_deg","depth_km","magnitude"):
  v=[r[k] for r in items if r[k] is not None]; out["ranges"][k]=[min(v),max(v)] if v else [None,None]
 return out
def write_norm(product,items):
 out=ANALYSIS/"derived"/product; out.mkdir(parents=True,exist_ok=True)
 path=out/f"{SOURCE_REF}__{product}__normalized_v1.csv"
 fields=["event_id","native_event_id","origin_time_utc","latitude_deg","longitude_deg","depth_km","magnitude","local_magnitude","strike","dip","rake","slip_style","source_row"]
 with path.open("w",newline="",encoding="utf-8") as f:
  w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
  for i,r in enumerate(items,1):
   w.writerow({"event_id":f"E{i:06d}","native_event_id":r["native_event_id"],"origin_time_utc":r["datetime"].isoformat().replace("+00:00","Z") if r["datetime"] else "",**{k:r[k] for k in fields[3:]}})
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
 for d in (ANALYSIS/"derived",ANALYSIS/"stats",ANALYSIS/"figures"): d.mkdir(parents=True,exist_ok=True)
 result={}
 for product,path in PRODUCTS.items():
  all_rows=list(rows(path)); selections={"full":all_rows,"time_only":[r for r in all_rows if in_window(r)],"benchmark":[r for r in all_rows if in_mask(r)]}
  result[product]={"source_path":str(path.relative_to(ROOT)),"source_sha256":sha256(path),"counts":{k:stats(v) for k,v in selections.items()}}
  if product=="growclust_corrected": write_norm(product,selections["full"])
  od=ANALYSIS/"stats"/product; od.mkdir(parents=True,exist_ok=True)
  for name,items in selections.items():
   payload={"case_id":CASE_ID,"source_ref":SOURCE_REF,"product_id":product,"selection":name,"parser_version":"kaikoura-chamberlain-v1","source_path":str(path.relative_to(ROOT)),"source_sha256":sha256(path),"stats":stats(items)}
   (od/f"{name}_v1.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
 items=[r for r in rows(PRODUCTS["growclust_corrected"]) if in_mask(r)]
 plot_event_diagnostics(items,"chamberlain_corrected_benchmark",f"{SOURCE_REF} · corrected benchmark")
 lines=[f"# {SOURCE_REF} catalog analysis","","Product-specific processing keeps corrected and legacy releases separate.","","| Product | Full | Time-only | Benchmark |", "|---|---:|---:|---:|"]
 for p,v in result.items(): lines.append(f"| `{p}` | {v['counts']['full']['row_count']} | {v['counts']['time_only']['row_count']} | {v['counts']['benchmark']['row_count']} |")
 lines += ["","The corrected release is the benchmark product. The legacy file is retained for release comparison only; native event IDs are not cross-catalog keys.","","Schema: `docs/schemas/catalog_event.schema.yaml`."]
 (ANALYSIS/"catalog_analysis.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2))
if __name__=="__main__": main()
