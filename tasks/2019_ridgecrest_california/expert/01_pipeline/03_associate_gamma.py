#!/usr/bin/env python3
"""Associate PhaseNet arrivals with local GaMMA; preserve traceable initial locations."""
import os
for name in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS','LOKY_MAX_CPU_COUNT']:
    os.environ[name]='1'
import argparse
import contextlib
import copy
import hashlib
import importlib.metadata
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import sys
import time
import numpy as np
import pandas as pd
import yaml
from pyproj import Proj

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
STATE={}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def initialize(library,stations,config,out):
    sys.path.insert(0,str(Path(library)/'basic_fun/GaMMA'))
    from gamma.seismic_ops import initialize_eikonal
    import gamma.utils as gu
    os.chdir(out)
    # Build one table per worker, then reuse it in the library's association entry point.
    with open(os.devnull,'w') as quiet, contextlib.redirect_stdout(quiet):
        grid=initialize_eikonal(copy.deepcopy(config['eikonal']))
    gu.initialize_eikonal=lambda unused:grid
    STATE.update(stations=stations,config=config,grid=grid)


def run_block(job,picks,out):
    from gamma.utils import association
    from gamma.seismic_ops import calc_time
    name,start,end=job
    began=time.monotonic();np.random.seed(42)
    directory=Path(out)/'blocks';log=directory/f'{name}.log'
    with log.open('w') as handle,contextlib.redirect_stdout(handle),contextlib.redirect_stderr(handle):
        events,assignments=association(picks,STATE['stations'],copy.deepcopy(STATE['config']),method='BGMM')
    kept=[];links=[]
    for event in events:
        origin=pd.Timestamp(event['time'],tz='UTC')
        if not start<=origin<end:continue
        subset=[a for a in assignments if a[1]==event['event_index']]
        indices=[int(a[0]) for a in subset];observed=picks.loc[indices]
        station=STATE['stations'].set_index('id').loc[observed['id']]
        location=np.array([[event[k] for k in ['x(km)','y(km)','z(km)']]+[0.]])
        travel=calc_time(location,station[['x(km)','y(km)','z(km)']].values,observed['type'].str.lower().values,
                         eikonal=STATE['grid']).ravel()
        residual=(observed['timestamp']-origin).dt.total_seconds().values-travel
        local_id=f"{name}_{event['event_index']}"
        kept.append(dict(candidate_id=local_id,origin_time=origin.isoformat(),x_km=event['x(km)'],y_km=event['y(km)'],
                         depth_km=event['z(km)'],sigma_time_s=event['sigma_time'],block=name))
        for index,res in zip(indices,residual):links.append(dict(candidate_id=local_id,pick_index=index,residual_s=float(res)))
    result=dict(events=kept,assignments=links,input_picks=len(picks),seconds=round(time.monotonic()-began,2))
    destination=directory/f'{name}.json';temp=destination.with_suffix('.tmp')
    temp.write_text(json.dumps(result,allow_nan=False));temp.replace(destination)
    return name,len(kept),len(links),result['seconds']


def merge(out,jobs,original,stations,settings,proj):
    events=[];links=[]
    for name,_,_ in jobs:
        block=json.loads((out/'blocks'/f'{name}.json').read_text());events+=block['events'];links+=block['assignments']
    ev=pd.DataFrame(events);ass=pd.DataFrame(links)
    if ev.empty:raise RuntimeError('No associated events; inspect block logs')
    # Resolve overlapping-block candidates using shared observations, not only proximity.
    by_id={e['candidate_id']:e for e in events};sets={k:set(g.pick_index) for k,g in ass.groupby('candidate_id')}
    rms={k:float(np.sqrt(np.mean(g.residual_s**2))) for k,g in ass.groupby('candidate_id')}
    ranking=sorted(sets,key=lambda k:(-len(sets[k]),rms[k],k));retained=[];rejected=[]
    pick_owners={}
    for key in ranking:
        candidates=set().union(*(pick_owners.get(i,set()) for i in sets[key]))
        duplicate=None
        for other in sorted(candidates):
            shared=len(sets[key]&sets[other]);a=by_id[key];b=by_id[other]
            dt=abs((pd.Timestamp(a['origin_time'])-pd.Timestamp(b['origin_time'])).total_seconds())
            distance=np.linalg.norm([a['x_km']-b['x_km'],a['y_km']-b['y_km'],a['depth_km']-b['depth_km']])
            if shared>=.5*min(len(sets[key]),len(sets[other])) and dt<=2 and distance<=10:
                duplicate=other;break
        if duplicate:rejected.append(dict(candidate_id=key,reason='shared_pick_duplicate',retained_candidate=duplicate));continue
        retained.append(key)
        for i in sets[key]:pick_owners.setdefault(i,set()).add(key)
    ass=ass[ass.candidate_id.isin(retained)].copy();conflicts=int(ass.pick_index.duplicated().sum())
    ass['abs_residual']=ass.residual_s.abs()
    ass=ass.sort_values(['abs_residual','candidate_id']).drop_duplicates('pick_index').drop(columns='abs_residual')
    catalog=[];valid=[]
    for key,g in ass.groupby('candidate_id'):
        observed=original.loc[g.pick_index];pc=int((observed.phase=='P').sum());sc=int((observed.phase=='S').sum());ns=observed.station_id.nunique()
        if len(g)<settings['min_picks_per_eq'] or pc<settings['min_p_picks_per_eq'] or sc<settings['min_s_picks_per_eq'] or ns<settings['min_stations']:
            rejected.append(dict(candidate_id=key,reason='insufficient_support_after_conflict_resolution',retained_candidate=''));continue
        e=by_id[key];longitude,latitude=proj(e['x_km'],e['y_km'],inverse=True)
        st=stations.set_index('id').loc[observed.instrument_id].drop_duplicates('station_id')
        azimuth=np.sort(np.degrees(np.arctan2(st['x(km)']-e['x_km'],st['y(km)']-e['y_km']))%360)
        gap=float(np.max(np.diff(np.r_[azimuth,azimuth[0]+360])))
        bounds=settings['depth_bounds_km'];flags=[]
        if min(e['depth_km']-bounds[0],bounds[1]-e['depth_km'])<.5:flags.append('near_depth_bound')
        if gap>180:flags.append('azimuth_gap_gt_180')
        if not (-117.90<=longitude<=-117.20 and 35.45<=latitude<=36.05):flags.append('outside_core_region')
        catalog.append(dict(**e,longitude=longitude,latitude=latitude,depth_below_sea_level_km=e['depth_km']-settings['reference_elevation_km'],
                            n_picks=len(g),n_p=pc,n_s=sc,n_stations=ns,rms_residual_s=float(np.sqrt(np.mean(g.residual_s**2))),
                            azimuth_gap_deg=gap,quality_flags=';'.join(flags)))
        valid.append(key)
    catalog=pd.DataFrame(catalog).sort_values(['origin_time','candidate_id']).reset_index(drop=True)
    catalog.insert(0,'event_id',[f'gamma_{i+1:07d}' for i in range(len(catalog))])
    ass=ass[ass.candidate_id.isin(valid)].merge(catalog[['candidate_id','event_id']],on='candidate_id',validate='many_to_one')
    exported=original.merge(ass[['pick_index','event_id','residual_s']],left_index=True,right_on='pick_index',how='left',validate='one_to_one').sort_values('pick_id')
    exported['association_status']=np.where(exported.event_id.notna(),'associated','unassociated')
    exported=exported.drop(columns=['pick_index'])
    assert exported.pick_id.is_unique and len(exported)==len(original)
    assert int(catalog.n_picks.sum())==int(exported.event_id.notna().sum())
    assert np.isfinite(catalog[['latitude','longitude','depth_km','rms_residual_s']].values).all()
    catalog.to_csv(out/'events.csv',index=False);exported.to_csv(out/'picks.csv',index=False)
    pd.DataFrame(rejected,columns=['candidate_id','reason','retained_candidate']).to_csv(out/'rejected_candidates.csv',index=False)
    return dict(events=len(catalog),input_picks=len(original),associated_picks=len(ass),unassociated_picks=len(original)-len(ass),
                duplicate_candidates=sum(r['reason']=='shared_pick_duplicate' for r in rejected),conflicting_assignments=conflicts,
                rejected_candidates=len(rejected),median_rms_s=float(catalog.rms_residual_s.median()),
                median_stations=float(catalog.n_stations.median()),depth_bound_events=int(catalog.quality_flags.str.contains('near_depth_bound').sum()))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--scope',choices=['pilot','full'],default='pilot')
    args=ap.parse_args();settings=yaml.safe_load((HERE/'00_config/association.yaml').read_text());cfg=yaml.safe_load((HERE/'00_config/config.yaml').read_text())
    export=HERE/cfg['export_root'];out=(export/'03_associate_gamma'/args.scope).resolve();(out/'blocks').mkdir(parents=True,exist_ok=True)
    import fcntl
    lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    library=(HERE/cfg['tools']['trace_library']).resolve();pick_path=export/'02_pick_phasenet/full/picks.csv'
    assert yaml.safe_load((pick_path.parent/'run.yaml').read_text())['status']=='complete'
    original=pd.read_csv(pick_path,keep_default_na=False);original['instrument_id']=original.station_id+'.'+original.location+'.'+original.channel_family
    meta_path=export/'01_prepare_inputs/full/waveform_inputs.csv';meta=pd.read_csv(meta_path,keep_default_na=False)
    station_inventory=(HERE/cfg['data_root']/'stations/station_inventory.json').resolve()
    epochs=json.loads(station_inventory.read_text())['channel_epochs']
    depths={}
    for seed in meta.seed_id.unique():
        matching=[e for e in epochs if '.'.join(e[k] for k in ['network','station','location','channel'])==seed
                  and (not e['effective_start'] or pd.Timestamp(e['effective_start'])<=pd.Timestamp(cfg['candidate_window']['start_utc']))
                  and (not e['effective_end'] or pd.Timestamp(e['effective_end'])>=pd.Timestamp(cfg['candidate_window']['end_utc']))]
        if len(matching)!=1:raise ValueError(f'Ambiguous sensor depth epoch: {seed}')
        depths[seed]=float(matching[0]['depth_m'])
    meta['sensor_depth_m']=meta.seed_id.map(depths)
    meta['id']=meta.station_id+'.'+meta.location+'.'+meta.family
    meta=meta[meta.id.isin(original.instrument_id.unique())]
    for _,g in meta.groupby('id'):
        assert len(g[['latitude','longitude','elevation_m','sensor_depth_m']].drop_duplicates())==1
    stations=meta.drop_duplicates('id')[['id','station_id','latitude','longitude','elevation_m','sensor_depth_m']].copy()
    proj=Proj(proj='aeqd',lon_0=settings['projection_center'][0],lat_0=settings['projection_center'][1],datum='WGS84',units='km')
    stations['x(km)'],stations['y(km)']=proj(stations.longitude.values,stations.latitude.values)
    stations['z(km)']=settings['reference_elevation_km']-(stations.elevation_m-stations.sensor_depth_m)/1000
    stations.to_csv(out/'stations.csv',index=False)
    corners=np.array([proj(lon,lat) for lon in settings['longitude_bounds'] for lat in settings['latitude_bounds']])
    xymin=corners.min(axis=0);xymax=corners.max(axis=0);bounds=[(float(xymin[0]),float(xymax[0])),(float(xymin[1]),float(xymax[1])),tuple(settings['depth_bounds_km']),(None,None)]
    model_path=HERE/'../../../data/2019_ridgecrest_california/data/models/velocity_models.json'
    model=json.loads(model_path.read_text())['models'][settings['velocity_model']]
    radius=float(np.max(np.linalg.norm(corners[:,None,:]-stations[['x(km)','y(km)']].values[None,:,:],axis=2)))+10
    grid=dict(vel=dict(z=[r['top_of_layer_km'] for r in model['rows']],p=[r['vp_km_s'] for r in model['rows']],s=[r['vs_km_s'] for r in model['rows']]),
              xlim=[0,radius],ylim=[0,1],zlim=[-5,35],h=settings['eikonal_spacing_km'])
    config={k:settings[k] for k in ['dbscan_eps','dbscan_min_samples','oversample_factor','covariance_prior','min_picks_per_eq','min_p_picks_per_eq','min_s_picks_per_eq','min_stations','max_sigma11']}
    config.update(use_amplitude=False,use_dbscan=True,ncpu=1,dims=['x(km)','y(km)','z(km)'],vel={'p':6.,'s':6./1.73},eikonal=grid,bfgs_bounds=bounds)
    config.update({k:list(b) for k,b in zip(config['dims'],bounds)})
    times=pd.to_datetime(original.time_utc,utc=True)
    if args.scope=='pilot':
        windows=[('quiet','2019-07-04T16:00Z','2019-07-04T16:10Z'),('m64','2019-07-04T17:30Z','2019-07-04T17:45Z'),('m71','2019-07-06T03:15Z','2019-07-06T03:30Z')]
        jobs=[(name,pd.Timestamp(a),pd.Timestamp(b)) for name,a,b in windows]
    else:
        a=pd.Timestamp(cfg['candidate_window']['start_utc']);end=pd.Timestamp(cfg['candidate_window']['end_utc']);jobs=[]
        while a<end:
            b=min(a+pd.Timedelta(seconds=settings['chunk_seconds']),end);jobs.append((a.strftime('%Y%m%dT%H%M%S'),a,b));a=b
    provenance=dict(scope=args.scope,settings=settings,gamma_config=config,model_source=model,
        input_sha256=sha(pick_path),station_input_sha256=sha(meta_path),station_inventory_sha256=sha(station_inventory),script_sha256=sha(__file__),
        library_sha256={p.name:sha(p) for p in sorted((library/'basic_fun/GaMMA/gamma').glob('*.py'))},
        versions={k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','scikit-learn','numba','pyproj']})
    fingerprint=out/'inputs.json'
    serialized=json.dumps(provenance,sort_keys=True,indent=2)
    if fingerprint.exists() and fingerprint.read_text()!=serialized:raise ValueError('Inputs changed; use separate output or preserve the previous attempt first')
    fingerprint.write_text(serialized)
    tasks=[]
    for job in jobs:
        if (out/'blocks'/f'{job[0]}.json').exists():continue
        mask=(times>=job[1]-pd.Timedelta(seconds=settings['buffer_seconds']))&(times<job[2]+pd.Timedelta(seconds=settings['buffer_seconds']))
        subset=pd.DataFrame(dict(id=original.loc[mask,'instrument_id'],timestamp=times[mask],type=original.loc[mask,'phase'],prob=original.loc[mask,'probability']))
        tasks.append((job,subset))
    began=time.monotonic();print(f'{args.scope}: {len(jobs)} blocks, {len(tasks)} pending, {settings["workers"]} CPU workers',flush=True)
    with ProcessPoolExecutor(max_workers=min(settings['workers'],max(1,len(tasks))),mp_context=multiprocessing.get_context('spawn'),initializer=initialize,initargs=(str(library),stations,config,str(out))) as pool:
        futures=[pool.submit(run_block,job,picks,str(out)) for job,picks in tasks]
        for i,f in enumerate(as_completed(futures),1):
            name,ne,npicks,seconds=f.result();print(f'[{i}/{len(tasks)}] {name}: {ne} events, {npicks} assigned picks, {seconds:.1f}s',flush=True)
    result=merge(out,jobs,original,stations,settings,proj)
    result.update(status='complete',scope=args.scope,completed_blocks=len(jobs),wall_seconds=round(time.monotonic()-began,2))
    (out/'run.yaml').write_text(yaml.safe_dump(result,sort_keys=False))
    (out/'README.md').write_text('''# GaMMA initial association

`events.csv` contains initial locations, stable event IDs and support/residual/geometry statistics. `picks.csv` preserves every input pick with its event ID and residual, or an unassociated status. Unassociated does not mean false. Pilot output only associates its three development windows; all other picks remain unassociated. `rejected_candidates.csv` records overlap reconciliation. `stations.csv`, `inputs.json`, block checkpoints/logs and `run.yaml` preserve execution context. Raw data and PhaseNet outputs are unchanged.

Local GaMMA BGMM, arrival times only; no amplitude or magnitude estimation. The library's placeholder magnitude 999 is omitted. Returned assignment scores are omitted because the local source pairs event-filtered pick indices with an unfiltered density-score vector; they are not reliable association probabilities. PhaseNet probabilities remain in the phase table. Travel-time residuals are recomputed independently with the same forward model.

The Shelly Table 1 numeric profile is linearly interpolated by GaMMA's 0.5-km eikonal grid, including between the 8- and 30-km nodes; this is an explicit baseline approximation, not reproduction of published hypoDD layer semantics. Model zero and reported depth_km use a nominal 0.7-km-above-sea-level surface; depth_below_sea_level_km = depth_km - 0.7. Stations use z = 0.7 - (elevation_m - sensor_depth_m)/1000, including the PB borehole sensor depths from the valid StationXML epochs. GaMMA looks up the source-minus-station vertical separation in a surface-source 1-D table: this is an approximate elevation treatment, not full station-specific layered ray tracing. Values above the first velocity node use its velocity. Constant 6 km/s is used only for DBSCAN spatial scaling; association uses the tabulated P/S travel times. All observed instruments remain included irrespective of station location. Initial event bounds include margins around the planned core region.

Time blocks include 120-s pick buffers and own events by half-open origin-time intervals. Shared-pick duplicates within 2 s / 10 km are reconciled; conflicting assignments use the smaller absolute residual, then support thresholds are reapplied. Remaining unused picks are retained. Events near depth bounds, with azimuth gaps >180 degrees or outside the core region are flagged, not silently removed. Initial positions and residual statistics are not formal location uncertainties or validated earthquake ground truth. Next: NonLinLoc absolute location and quality review. No reference event catalog was used.
''')
    print(yaml.safe_dump(result,sort_keys=False),flush=True)


if __name__=='__main__':main()
