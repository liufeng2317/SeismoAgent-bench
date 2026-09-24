#!/usr/bin/env python3
import csv,json,hashlib,tarfile,io
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]; A=ROOT/"analysis"; UTC=timezone.utc
START=datetime(2019,7,4,tzinfo=UTC); END=datetime(2019,7,7,tzinfo=UTC)
LAT=(35.45,36.05); LON=(-117.90,-117.20); DEP=(0,20)
def num(x):
 try:return float(x)
 except:return None
def dt(x):
 try:return datetime.fromisoformat(str(x).replace("Z","+00:00")).astimezone(UTC)
 except:return None
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
 return h.hexdigest()
def mask(r):
 return r["datetime"] and START<=r["datetime"]<END and LAT[0]<=r["latitude_deg"]<=LAT[1] and LON[0]<=r["longitude_deg"]<=LON[1] and DEP[0]<=r["depth_km"]<=DEP[1]
def stat(rr):
 o={"row_count":len(rr),"unique_native_event_ids":len({str(r.get("native_event_id","")) for r in rr}),"duplicate_native_event_ids":len(rr)-len({str(r.get("native_event_id","")) for r in rr}),"ranges":{}}
 for k in ("latitude_deg","longitude_deg","depth_km","magnitude"):
  v=[r[k] for r in rr if r.get(k) is not None]; o["ranges"][k]=[min(v),max(v)] if v else [None,None]
 return o
def plots(items,stem,title):
 out=A/"figures"; out.mkdir(parents=True,exist_ok=True); xyz=[r for r in items if all(r.get(k) is not None for k in ("longitude_deg","latitude_deg","depth_km"))]
 if not xyz:return
 fig,ax=plt.subplots(2,2,figsize=(7.2,6.4))
 for a,x,y,xl,yl in ((ax[0,0],"longitude_deg","latitude_deg","Longitude (°E)","Latitude (°)"),(ax[0,1],"depth_km","latitude_deg","Depth (km)","Latitude (°)"),(ax[1,0],"longitude_deg","depth_km","Longitude (°E)","Depth (km)")):
  a.scatter([r[x] for r in xyz],[r[y] for r in xyz],s=5,alpha=.4,c="#2C5F8A",linewidths=0,rasterized=True);a.set(xlabel=xl,ylabel=yl);a.spines[["top","right"]].set_visible(False)
 ax[0,1].invert_xaxis(); ax[1,0].invert_yaxis()
 ax[1,1].hist([r["depth_km"] for r in xyz],bins="auto",orientation="horizontal",color="#009E73",edgecolor="white",linewidth=.3); ax[1,1].invert_yaxis(); ax[1,1].set(xlabel="Events",ylabel="Depth (km)"); ax[1,1].spines[["top","right"]].set_visible(False); ax[1,1].text(.98,.04,f"n = {len(xyz):,}",transform=ax[1,1].transAxes,ha="right",va="bottom",fontsize=8)
 fig.suptitle(title,x=.07,ha="left"); fig.tight_layout(); fig.savefig(out/f"{stem}_spatial_three_views_v2.png",dpi=300); plt.close(fig)
 timed=sorted([r for r in items if r.get("datetime")],key=lambda r:r["datetime"]); days=Counter(r["datetime"].date() for r in timed); fig,ax=plt.subplots(figsize=(7.2,3.2)); ds=sorted(days); ax.bar(ds,[days[d] for d in ds],color="#2C5F8A"); ax.set(xlabel="Origin time (UTC)",ylabel="Events per day"); ax.tick_params(axis="x",rotation=30); ax.spines[["top","right"]].set_visible(False); fig.tight_layout(); fig.savefig(out/f"{stem}_seismicity_time_v2.png",dpi=300); plt.close(fig)
 mags=[r for r in timed if r.get("magnitude") is not None]; fig,ax=plt.subplots(1,2,figsize=(7.2,3.2)); ax[0].hist([r["magnitude"] for r in mags],bins="auto",color="#2C5F8A",edgecolor="white"); ax[0].set(xlabel="Native magnitude",ylabel="Events"); ax[1].scatter([r["datetime"] for r in mags],[r["magnitude"] for r in mags],s=5,c="#D55E00",alpha=.45,linewidths=0); ax[1].set(xlabel="Origin time (UTC)",ylabel="Native magnitude"); [a.spines[["top","right"]].set_visible(False) for a in ax]; fig.tight_layout(); fig.savefig(out/f"{stem}_magnitude_diagnostics_v2.png",dpi=300); plt.close(fig)
def write_stats(ref,products):
 for d in (A/"stats",A/"figures",A/"derived"):d.mkdir(parents=True,exist_ok=True)
 lines=[f"# {ref} catalog analysis","", "Each product is parsed with its native schema; benchmark selection uses the Ridgecrest fixed window (2019-07-04 to 2019-07-07, 35.45–36.05°N, −117.90–−117.20°E, depth 0–20 km).","", "| Product | Full | Time-only | Benchmark |", "|---|---:|---:|---:|"]
 for p,(rr,src) in products.items():
  sels={"full":rr,"time_only":[r for r in rr if r.get("datetime") and START<=r["datetime"]<END],"benchmark":[r for r in rr if mask(r)]};
  for n,v in sels.items(): (A/"stats"/p).mkdir(parents=True,exist_ok=True); (A/"stats"/p/f"{n}_v1.json").write_text(json.dumps({"case_id":"2019_ridgecrest_california","source_ref":ref,"product_id":p,"selection":n,"stats":stat(v)},indent=2)+"\n")
  lines.append(f"| `{p}` | {len(sels['full']):,} | {len(sels['time_only']):,} | {len(sels['benchmark']):,} |")
  plots(sels["benchmark"],p,f"{ref} · {p} benchmark")
 (A/"catalog_analysis.md").write_text("\n".join(lines)+"\n")
def main():
 ref="ROSS2019_SCIENCE"; p=ROOT/"raw"/f"{ref}__catalog_qtm.tar.gz"; rr=[]
 with tarfile.open(p,"r:gz") as t:
  f=t.extractfile("ridgecrest_qtm.cat")
  for i,line in enumerate(io.TextIOWrapper(f),1):
   z=line.split()
   if len(z)<25: continue
   try: d=datetime(int(z[0]),int(z[1]),int(z[2]),int(z[3]),int(z[4]),tzinfo=UTC)+__import__('datetime').timedelta(seconds=float(z[5]))
   except: continue
   rr.append({"source_row":i,"native_event_id":z[6],"datetime":d,"latitude_deg":num(z[7]),"longitude_deg":num(z[8]),"depth_km":num(z[9]),"magnitude":num(z[10]),"nbranch":num(z[13]),"qnpair":num(z[14]),"qndiffP":num(z[15]),"qndiffS":num(z[16]),"rmsP":num(z[17]),"rmsS":num(z[18])})
 write_stats(ref,{"qtm_event_catalog":(rr,p)})
 (A/"catalog_analysis.md").write_text((A/"catalog_analysis.md").read_text()+"\nQTM source rows preserve the original `nbranch` quality indicator; rows with nbranch > 1 are the multi-branch subset, not a separate catalog.\n")
if __name__=="__main__":main()
