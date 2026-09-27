#!/usr/bin/env python3
"""Traceable SCEDC archive interpretation and matched 3-D travel-time grid pilot."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import argparse,hashlib,json,subprocess
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
from scipy.spatial import Delaunay,ConvexHull
from scipy.interpolate import interp1d,RegularGridInterpolator
from pyproj import Proj
from threadpoolctl import threadpool_limits
threadpool_limits(1)
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/29_3d_velocity';BASE=HERE/'export/04_locate_nonlinloc'
RAW=HERE.parents[2]/'benchmark_source/2019_ridgecrest_california/data/models/raw/SCEDC_SOCAL_3D/vel.sc8196ord1_sc04.07qd.out'
BINDIR=Path('/liufeng1afs/software/NLLoc/NLL7.00_src/src')
PROJ=Proj(proj='aeqd',lon_0=-117.55,lat_0=35.75,datum='WGS84',units='km')
SPACING=1.0
AXES=(np.arange(-130,111,dtype=float),np.arange(-120,121,dtype=float),np.arange(-3,36,dtype=float))

def configure(spacing):
    global OUT,AXES,SPACING
    SPACING=spacing;OUT=HERE/f"export/29_3d_velocity/h{int(spacing*1000):04d}m"
    AXES=tuple(np.arange(a,b+spacing/2,spacing) for a,b in [(-130,110),(-120,120),(-3,35)])


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write_json(p,value):
    tmp=p.with_name(p.name+'.tmp')
    with tmp.open('w') as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,p)


def archive():
    sections=[]
    for line in RAW.read_text().splitlines():
        if line.lstrip().startswith('LAYR'):
            sections.append(dict(depth=float(line.split()[2].rstrip('k')),rows=[]));continue
        if not line.strip():continue
        value=float(line[:6]);ld=float(line[6:8]);lm=float(line[8:13]);od=float(line[14:17]);om=float(line[17:22])
        assert 0<=lm<60 and 0<=om<60
        suffix=list(map(float,line[22:].split()))
        if len(suffix)==4:
            duplicate,x,y,z=suffix;assert value==duplicate
        else:
            assert len(suffix)==3
            x,y,z=suffix
        assert z==sections[-1]['depth']
        sections[-1]['rows'].append([value,ld+lm/60,-od-om/60,x,y,z])
    assert len(sections)==27 and all(len(s['rows'])==1107 for s in sections)
    blocks=np.array([s['rows'] for s in sections]).reshape(3,9,1107,6)
    assert np.allclose(blocks[0,:,:,1:],blocks[1,:,:,1:]) and np.allclose(blocks[0,:,:,1:],blocks[2,:,:,1:])
    assert np.allclose(blocks[0,:,:,1:5],blocks[0,0,:,1:5][None,:,:])
    depth=blocks[0,:,0,5];assert list(depth)==[1,4,6,10,15,17,22,31,33]
    ratio_error=float(np.max(np.abs(blocks[0,:,:,0]/blocks[1,:,:,0]-blocks[2,:,:,0])));assert ratio_error<.011
    assert np.all(blocks[:2,:,:,0]>0) and np.all(blocks[0,:,:,0]>blocks[1,:,:,0])
    x,y=PROJ(blocks[0,0,:,2],blocks[0,0,:,1]);tri=Delaunay(np.column_stack([x,y]))
    return blocks,depth,tri,ratio_error


def prepare_models():
    OUT.mkdir(exist_ok=True);blocks,depth,tri,ratio_error=archive()
    xx,yy=np.meshgrid(AXES[0],AXES[1],indexing='ij');query=np.column_stack([xx.ravel(),yy.ravel()]);simplex=tri.find_simplex(query)
    outside=simplex<0
    margin=np.full(len(query),np.inf)
    for plane in ConvexHull(tri.points).equations:
        margin=np.minimum(margin,-(query@plane[:2]+plane[2]))
    blend=np.clip(margin/15.,0.,1.);blend[outside]=0.
    simplex=np.maximum(simplex,0)
    delta=query-tri.transform[simplex,2,:];bary=np.einsum('ijk,ik->ij',tri.transform[simplex,:2,:],delta);weights=np.column_stack([bary,1-bary.sum(axis=1)]);vertices=tri.simplices[simplex]
    n=len(query);shape=tuple(len(a) for a in AXES);h=SPACING
    stations=pd.read_csv(BASE/'stations.csv')
    assert all(stations[f'{v}(km)'].between(a[0]+1,a[-1]-1).all() for v,a in zip(['x','y'],AXES[:2]))
    files=[Path(__file__),RAW,BASE/'stations.csv',HERE/'00_config/nonlinloc.yaml',BINDIR/'Grid2Time',BINDIR/'Grid2Time1.c',BINDIR/'Time_3d_NLL.c',BASE/'grids/P.in',BASE/'grids/S.in']
    design=dict(scope='Matched-volume baseline versus SCEDC-supported hybrid 3D archive; numerical/coverage pilot, not precision-certified or adopted.',shape=shape,origins=[float(a[0]) for a in AXES],spacing_km=h,property_blocks='Vp, Vs, Vp/Vs inferred from redundant numeric ranges and ratio consistency; not an independently documented exact archive release/schema.',max_ratio_consistency_error=ratio_error,background_only_columns=int(outside.sum()),taper_width_km=15.,coordinates='Read printed degrees/minutes, west-negative longitude; project nodes to benchmark AEQD. Piecewise-linear Delaunay horizontal interpolation and linear depth interpolation of velocities, not slowness. Inside the geographic hull, blend into baseline over a fixed 15km inward boundary distance (one published horizontal grid scale); outside the hull use baseline. CI.FUR lies outside archive support. No nearest-neighbor extrapolation.',depth='Archive depth assumed below sea level per Hauksson 2007 SCEC report; evaluate at benchmark z-0.7. Constant extension above 1km and below33km, explicit approximation. Receivers retain original elevations/burial.',primary_sources=['https://service.scedc.caltech.edu/ftp/catalogs/hauksson/Socal_3Dmodel/vel.sc8196ord1_sc04.07qd.out.Z','https://files.scec.org/s3fs-public/reports/2007/07058_report.pdf','https://doi.org/10.1029/2000JB900016'],source_sha256={str(p):sha(p) for p in files})
    path=OUT/'grid_design.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(json.dumps(design))
    else:write_json(path,design)
    # Baseline values come from exact previously executed LAYER entries, including gradients.
    rows=[list(map(float,l.split()[1:])) for l in (BASE/'grids/P.in').read_text().splitlines() if l.startswith('LAYER ')]
    rows=np.array(rows);iz=np.searchsorted(rows[:,0],AXES[2],side='right')-1
    values=[]
    for index,phase in enumerate(['P','S']):
        layer_values=np.sum(blocks[index,:,:,0][:,vertices]*weights[None,:,:],axis=2)
        regional=interp1d(depth,layer_values,axis=0,bounds_error=False,fill_value=(layer_values[0],layer_values[-1]))(AXES[2]-.7).T.reshape(shape)
        vpcol=1 if phase=='P' else 3;gradcol=vpcol+1
        profile=rows[iz,vpcol]+rows[iz,gradcol]*(AXES[2]-rows[iz,0]);baseline=np.broadcast_to(profile,shape)
        weight=blend.reshape(shape[:2])[...,None];regional=weight*regional+(1-weight)*baseline
        assert np.isfinite(regional).all() and regional.min()>0
        for label,velocity in [('regional',regional),('baseline',baseline)]:
            folder=OUT/label;folder.mkdir(exist_ok=True);buf=folder/f'model.{phase}.mod.buf';hdr=buf.with_suffix('.hdr')
            if not buf.exists():
                (h/velocity).astype('float32').tofile(buf)
                hdr.write_text(f'{shape[0]} {shape[1]} {shape[2]} -130 -120 -3 {h} {h} {h} SLOW_LEN FLOAT\nTRANSFORM NONE\n')
            actual=np.memmap(buf,mode='r',dtype='float32',shape=shape)
            assert np.max(np.abs(actual-h/velocity))<1e-7
            values.append(dict(model=label,phase=phase,min_velocity_km_s=float(velocity.min()),max_velocity_km_s=float(velocity.max()),bytes=buf.stat().st_size,sha256=sha(buf)))
    pd.DataFrame(values).to_csv(OUT/'model_summary.csv',index=False)
    pd.DataFrame(dict(depth_below_sea_level_km=np.tile(depth,1107),latitude=np.repeat(blocks[0,0,:,1],9),longitude=np.repeat(blocks[0,0,:,2],9),vp_km_s=blocks[0,:,:,0].T.ravel(),vs_km_s=blocks[1,:,:,0].T.ravel())).to_csv(OUT/'interpreted_nodes.csv',index=False)
    print('Model grids verified:',shape,'; explicit background-only columns='+str(int(outside.sum()))+'; ratio discrepancy',ratio_error,flush=True)
    return stations


def grid(station,phase,label):
    folder=OUT/label;sid=station['nll_station'];control=folder/f'{phase}_{sid}.in'
    text=f'CONTROL 1 54321\nTRANS NONE\nGTFILES model time {phase}\nGTMODE GRID3D ANGLES_NO\nGT_PLFD 1.e-3 0\nGTSRCE {sid} XYZ {station["x(km)"]:.8f} {station["y(km)"]:.8f} {station["z(km)"]:.8f} 0\n'
    marker=folder/f'{phase}_{sid}.complete.json';buf=folder/f'time.{phase}.{sid}.time.buf';hdr=buf.with_suffix('.hdr')
    identity=dict(control=text,model_sha256=sha(folder/f'model.{phase}.mod.buf'))
    if marker.exists():
        m=json.loads(marker.read_text());assert m['input']==identity and sha(buf)==m['time_sha256'];return
    control.write_text(text)
    with (folder/f'{phase}_{sid}.log').open('w') as log:subprocess.run([str(BINDIR/'Grid2Time'),control.name],cwd=folder,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=900)
    shape=tuple(len(a) for a in AXES);g=np.memmap(buf,mode='r',dtype=np.float32,shape=shape)
    assert np.isfinite(g).all() and g.min()>=0 and g.max()<200
    fields=hdr.read_text().splitlines()[0].split();assert tuple(map(int,fields[:3]))==shape and fields[9]=='TIME'
    write_json(marker,dict(input=identity,time_sha256=sha(buf),header_sha256=sha(hdr)))


def predict(directory,p,stations):
    result=np.empty(len(p))
    for (sid,phase),g in p.groupby(['instrument_id','phase']):
        alias=stations.loc[sid,'nll_station'];buf=directory/f'time.{phase}.{alias}.time.buf'
        grid=np.memmap(buf,dtype=np.float32,mode='r',shape=tuple(len(a) for a in AXES))
        result[g.index]=RegularGridInterpolator(AXES,grid,bounds_error=True)(g[['x_km','y_km','depth_km']].to_numpy())
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--spacing',type=float,choices=[1.,.5,.25],default=1.);ap.add_argument('--all',action='store_true');ap.add_argument('--workers',type=int,default=4);args=ap.parse_args()
    configure(args.spacing)
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'grid.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        stations=prepare_models()
        # One fixed pilot event, selected by event ID before inspecting this model's solutions.
        cohort=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv');eid=sorted(cohort.event_id)[0]
        phases=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv');used=phases[phases.event_id.eq(eid)].instrument_id.unique()
        chosen=stations if args.all else stations[stations.id.isin(used)]
        tasks=[(s,p,m) for m in ['baseline','regional'] for s in chosen.to_dict('records') for p in ['P','S']]
        print('Grid generation:',len(tasks),'tasks; pilot event',eid,flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            jobs={pool.submit(grid,*t):t for t in tasks}
            for i,f in enumerate(as_completed(jobs),1):
                f.result();print(f'[{i}/{len(tasks)}] completed',flush=True)
        write_json(OUT/'grid_run.json',dict(pilot_event=eid,n_station_phase_model_grids=len(tasks),all_stations=args.all,complete=True))

if __name__=='__main__':main()
