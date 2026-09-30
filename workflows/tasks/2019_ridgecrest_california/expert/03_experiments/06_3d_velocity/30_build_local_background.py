#!/usr/bin/env python3
"""Replace the regional depth background; retain fixed fractional lateral variations."""
from pathlib import Path
import argparse, importlib.util, json
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
import yaml
from scipy.spatial import ConvexHull
from scipy.interpolate import interp1d
HERE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('grids30',Path(__file__).with_name('29_build_3d_grids.py'));G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
G.configure(.25)
PREVIOUS=G.OUT
OUT=HERE/'export/30_local_background'
G.OUT=OUT/'grids'

def prepare():
    G.OUT.mkdir(parents=True,exist_ok=True)
    baseline=G.OUT/'baseline'
    if not baseline.exists():baseline.symlink_to(PREVIOUS/'baseline',target_is_directory=True)
    assert baseline.resolve()==(PREVIOUS/'baseline').resolve()
    cfg=yaml.safe_load((HERE/'00_config/validation.yaml').read_text())
    blocks,depth,tri,ratio_error=G.archive()
    xx,yy=np.meshgrid(G.AXES[0],G.AXES[1],indexing='ij');query=np.column_stack([xx.ravel(),yy.ravel()])
    lon,lat=G.PROJ(query[:,0],query[:,1],inverse=True)
    roi=(lat>=cfg['latitude_bounds'][0])&(lat<=cfg['latitude_bounds'][1])&(lon>=cfg['longitude_bounds'][0])&(lon<=cfg['longitude_bounds'][1])
    simplex=tri.find_simplex(query);margin=np.full(len(query),np.inf)
    for plane in ConvexHull(tri.points).equations:margin=np.minimum(margin,-(query@plane[:2]+plane[2]))
    blend=np.clip(margin/15,0,1);blend[simplex<0]=0
    simplex=np.maximum(simplex,0);delta=query-tri.transform[simplex,2,:];bary=np.einsum('ijk,ik->ij',tri.transform[simplex,:2,:],delta);weights=np.column_stack([bary,1-bary.sum(axis=1)]);vertices=tri.simplices[simplex]
    assert roi.sum()>100 and blend[roi].sum()>100
    sources=[Path(__file__),Path(G.__file__),G.RAW,HERE/'00_config/validation.yaml',G.BASE/'grids/P.in',G.BASE/'stations.csv',PREVIOUS/'grid_design.json',G.BINDIR/'Grid2Time',G.BINDIR/'Grid2Time1.c',G.BINDIR/'Time_3d_NLL.c']
    design=dict(round=10,model='Local 1D depth background with regional fractional lateral variations; zero station corrections.',formula='For each phase and benchmark depth z: M(z)=sum_ROI(w*Vraw)/sum_ROI(w); Vnew(x,y,z)=Vlocal(z)*(1+w(x,y)*(Vraw(x,y,z)/M(z)-1)). Same fixed 15km geographic support taper as stage29. ROI mean Vnew equals Vlocal up to float32 rounding, including partially tapered ROI cells. No amplitude fitting/scanning.',roi_latitude=cfg['latitude_bounds'],roi_longitude=cfg['longitude_bounds'],roi_columns=int(roi.sum()),averaging='Uniform benchmark XY grid cells within the existing geographic case bounds; no event/reference coordinates or outcome weighting.',fixed='Original archive interpolation/datum and native .25km grid; original local LAYER profile. Outside archive support retain local background. Full-strength fractional lateral variations, independently for P and S.',comparison='Reuse verified stage29 matched 3D background and stage20 original fine 2D controls. Same heldout/reference/depth/retention/omission gates, no confirmation data.',source_sha256={str(p):G.sha(p) for p in sources})
    d=OUT/'model_design.json'
    if d.exists():assert json.loads(d.read_text())==design
    else:G.write_json(d,design)
    rows=np.array([list(map(float,l.split()[1:])) for l in (G.BASE/'grids/P.in').read_text().splitlines() if l.startswith('LAYER ')])
    iz=np.searchsorted(rows[:,0],G.AXES[2],side='right')-1;shape=tuple(len(a) for a in G.AXES)
    folder=G.OUT/'regional';folder.mkdir(exist_ok=True);profiles=[];checks=[]
    for index,phase in enumerate(['P','S']):
        lv=np.sum(blocks[index,:,:,0][:,vertices]*weights[None,:,:],axis=2)
        raw=interp1d(depth,lv,axis=0,bounds_error=False,fill_value=(lv[0],lv[-1]))(G.AXES[2]-.7).T
        mean=np.sum(raw[roi]*blend[roi,None],axis=0)/blend[roi].sum()
        col=1 if phase=='P' else 3
        local=rows[iz,col]+rows[iz,col+1]*(G.AXES[2]-rows[iz,0])
        candidate=local[None,:]*(1+blend[:,None]*(raw/mean[None,:]-1))
        assert np.isfinite(candidate).all() and candidate.min()>0
        assert np.max(np.abs(candidate[roi].mean(axis=0)-local))<1e-8
        assert np.max(np.abs(candidate[blend==0]-local[None,:]))<1e-8
        profiles.extend(dict(phase=phase,benchmark_depth_km=z,local_velocity_km_s=v,regional_weighted_mean_km_s=m) for z,v,m in zip(G.AXES[2],local,mean))
        buf=folder/f'model.{phase}.mod.buf';hdr=buf.with_suffix('.hdr')
        expected=(G.SPACING/candidate).astype(np.float32).reshape(shape)
        if not buf.exists():
            expected.tofile(buf);hdr.write_text(f'{shape[0]} {shape[1]} {shape[2]} -130 -120 -3 .25 .25 .25 SLOW_LEN FLOAT\nTRANSFORM NONE\n')
        actual=np.memmap(buf,mode='r',dtype=np.float32,shape=shape)
        assert np.array_equal(actual,expected)
        checks.append(dict(phase=phase,min_velocity_km_s=float(candidate.min()),max_velocity_km_s=float(candidate.max()),model_sha256=G.sha(buf),header_sha256=G.sha(hdr),roi_mean_error_km_s=float(np.max(np.abs(candidate[roi].mean(axis=0)-local)))))
        del raw,candidate,expected,actual
        print('Verified normalized model',phase,flush=True)
    pd.DataFrame(profiles).to_csv(OUT/'background_profiles.csv',index=False);G.write_json(OUT/'model_checks.json',checks)
    return pd.read_csv(G.BASE/'stations.csv')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);a=ap.parse_args()
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'grid.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stations=prepare();jobs=[(s,phase,'regional') for s in stations.to_dict('records') for phase in ['P','S']]
        with ThreadPoolExecutor(max_workers=a.workers) as pool:
            fs=[pool.submit(G.grid,*job) for job in jobs]
            for i,f in enumerate(as_completed(fs),1):f.result();print(f'[{i}/{len(jobs)}] candidate grid complete',flush=True)
        G.write_json(OUT/'grid_run.json',dict(complete=True,n_grids=len(jobs),spacing_km=.25,controls='Linked unchanged stage29 matched background grids'))
if __name__=='__main__':main()
