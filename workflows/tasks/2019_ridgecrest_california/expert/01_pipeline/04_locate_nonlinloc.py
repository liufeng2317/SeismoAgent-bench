#!/usr/bin/env python3
"""Re-locate fixed GaMMA event/pick groups with local NonLinLoc binaries."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import numpy as np
import pandas as pd
from pyproj import Proj
import yaml

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def execute(binary,control,cwd,log,timeout):
    with log.open('w') as f:
        proc=subprocess.run([str(binary),os.path.relpath(control,cwd)],cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    if proc.returncode:raise RuntimeError(f'{binary.name} returned {proc.returncode}; see {log}')


def tokens(body,prefix):
    line=next(x for x in body.splitlines() if x.startswith(prefix+' '))
    return line.split()[1:]


def pairs(body,prefix):
    a=tokens(body,prefix);return dict(zip(a[::2],a[1::2]))


def parse_hyp(path,event,observations,station_map,proj):
    body=path.read_text();status=re.match(r'NLLOC\s+"[^"]*"\s+"([^"]+)"',body).group(1)
    h=pairs(body,'HYPOCENTER');q=pairs(body,'QUALITY');stats=pairs(body,'STATISTICS')
    geo=tokens(body,'GEOGRAPHIC');year,month,day,hour,minute=map(int,geo[1:6]);sec=float(geo[6])
    origin=pd.Timestamp(year=year,month=month,day=day,hour=hour,minute=minute,tz='UTC')+pd.Timedelta(seconds=sec)
    x,y,z=[float(h[k]) for k in ['x','y','z']];lon,lat=proj(x,y,inverse=True)
    row=dict(event_id=event['event_id'],status=status,origin_time=origin.isoformat(),longitude=lon,latitude=lat,
             x_km=x,y_km=y,depth_km=z,depth_below_sea_level_km=z-.7,rms_residual_s=float(q['RMS']),
             n_phases=int(q['Nphs']),azimuth_gap_deg=float(q['Gap']),
             posterior_mean_x_km=float(stats['ExpectX']),posterior_mean_y_km=float(stats['Y']),posterior_mean_depth_km=float(stats['Z']),
             posterior_sigma_x_km=np.sqrt(max(0,float(stats['CovXX']))),posterior_sigma_y_km=np.sqrt(max(0,float(stats['YY']))),
             posterior_sigma_depth_km=np.sqrt(max(0,float(stats['ZZ']))),
             horizontal_shift_km=np.hypot(x-event['x_km'],y-event['y_km']),depth_shift_km=z-event['depth_km'],
             gamma_depth_km=event['depth_km'],gamma_rms_residual_s=event['rms_residual_s'])
    links=[];expected={(r['instrument_id'],r['phase']):r for r in observations}
    inside=False
    for line in body.splitlines():
        if line.startswith('PHASE '):inside=True;continue
        if line.startswith('END_PHASE'):inside=False
        if not inside or ' > ' not in line:continue
        before,after=line.split(' > ');a=before.split();b=after.split()
        instrument=station_map[a[0]];phase=a[4];p=expected[(instrument,phase)]
        # Verify the parser maps an unchanged arrival, not merely a station/phase label.
        stamp=pd.to_datetime(a[6],format='%Y%m%d',utc=True)+pd.Timedelta(hours=int(a[7])//100,minutes=int(a[7])%100,seconds=float(a[8]))
        assert abs((stamp-pd.Timestamp(p['time_utc'])).total_seconds())<.00011
        links.append(dict(event_id=row['event_id'],pick_id=p['pick_id'],instrument_id=instrument,phase=phase,
                          residual_s=float(b[1]),weight=float(b[2]),predicted_travel_time_s=float(b[0])))
    assert len(links)==len(expected)==row['n_phases'],f'Arrival count mismatch for {row["event_id"]}'
    assert len({r['pick_id'] for r in links})==len(links)
    assert all(r['weight']>0 for r in links),'An input arrival was not used'
    row['rms_unweighted_s']=float(np.sqrt(np.mean([r['residual_s']**2 for r in links])))
    row['gamma_rms_unweighted_s']=float(np.sqrt(np.mean([float(r['residual_s'])**2 for r in observations])))
    row['origin_time_shift_s']=(origin-pd.Timestamp(event['origin_time'])).total_seconds()
    row['n_stations']=len({p['station_id'] for p in observations})
    assert len(observations)==len(expected)
    assert np.isfinite([x,y,z,row['rms_unweighted_s'],row['posterior_sigma_depth_km']]).all()
    assert 0<=z<=25, 'Depth outside the fixed search interval'
    row['quality_flags']=';'.join(x for x,condition in [('near_depth_bound',z<.5 or z>24.5),('azimuth_gap_gt_180',float(q['Gap'])>180),('not_located',status!='LOCATED')] if condition)
    return row,links


def locate(event,observations,aliases,common,out,cfg,proj):
    start=time.monotonic();folder=out/'events_raw'/event['event_id'];folder.mkdir(parents=True,exist_ok=True)
    obs=folder/'input.obs';control=folder/'control.in'
    lines=[]
    for r in observations:
        t=pd.Timestamp(r['time_utc']);sec=t.second+t.microsecond/1e6
        lines.append(f"{aliases[r['instrument_id']]:6s} ? ? ? {r['phase']} ? {t:%Y%m%d} {t:%H%M} {sec:.4f} GAU {cfg['pick_error_s'][r['phase']]:.4f} -1 -1 -1")
    # Explicit terminators avoid the old C reader's char/EOF issue on this host.
    obs.write_text('\n'.join(lines)+'\n!END_EVENT\n!END_FILE\n')
    control.write_text(common+'\nLOCFILES input.obs NLLOC_OBS ../../grids/time solution\n')
    done=folder/'complete'
    paths=[p for p in folder.glob('solution.*.grid0.loc.hyp') if '.sum.' not in p.name]
    if not done.exists():
        execute(Path(cfg['binary_directory'])/'NLLoc',control,folder,folder/'run.log',cfg['per_event_timeout_s'])
        paths=[p for p in folder.glob('solution.*.grid0.loc.hyp') if '.sum.' not in p.name]
    if len(paths)!=1:raise RuntimeError(f'{event["event_id"]}: expected one .hyp, found {len(paths)}; inspect run.log')
    if done.exists() and done.read_text().strip()!=sha(paths[0]):raise ValueError('Cached hypocenter changed')
    row,links=parse_hyp(paths[0],event,observations,{v:k for k,v in aliases.items()},proj)
    checkpoint=folder/'complete.tmp'
    checkpoint.write_text(sha(paths[0])+'\n')
    checkpoint.replace(done)
    row['seconds']=round(time.monotonic()-start,3)
    return row,links


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--scope',choices=['pilot','full'],default='pilot');args=ap.parse_args()
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    source=HERE/'export/03_associate_gamma/full';out=HERE/'export/04_locate_nonlinloc';out.mkdir(exist_ok=True)
    import fcntl
    lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    dest=out/args.scope;dest.mkdir(exist_ok=True)
    e=pd.read_csv(source/'events.csv',keep_default_na=False);p=pd.read_csv(source/'picks.csv',keep_default_na=False);s=pd.read_csv(source/'stations.csv')
    p=p[p.association_status.eq('associated')]
    previous=json.loads((source/'inputs.json').read_text());ac=previous['settings'];grid_cfg=previous['gamma_config']
    proj=Proj(proj='aeqd',lon_0=ac['projection_center'][0],lat_0=ac['projection_center'][1],datum='WGS84',units='km')
    aliases={v:f'S{i:04d}' for i,v in enumerate(sorted(s.id),1)}
    s['nll_station']=s.id.map(aliases);s.to_csv(out/'stations.csv',index=False)
    fingerprint=dict(config=cfg,association_inputs=previous,source_sha256={f:sha(source/f) for f in ['events.csv','picks.csv','stations.csv']},
                     script_sha256=sha(__file__),binary_sha256={f:sha(Path(cfg['binary_directory'])/f) for f in ['NLLoc','Vel2Grid','Grid2Time']})
    text=json.dumps(fingerprint,sort_keys=True,indent=2);record=out/'inputs.json'
    if record.exists() and record.read_text()!=text:raise ValueError('Inputs/code changed; preserve previous output before restarting')
    record.write_text(text)
    grids=out/'grids';grids.mkdir(exist_ok=True)
    h=cfg['grid_spacing_km'];top=cfg['grid_top_km'];bottom=cfg['grid_bottom_km'];radius=grid_cfg['eikonal']['xlim'][1]+10
    model=previous['model_source']['rows'];layers=[f"LAYER {top} {model[0]['vp_km_s']} 0 {model[0]['vs_km_s']} 0 2.7 0"]
    for i,r in enumerate(model):
        gp=gs=0
        if i+1<len(model):
            nxt=model[i+1];dz=nxt['top_of_layer_km']-r['top_of_layer_km'];gp=(nxt['vp_km_s']-r['vp_km_s'])/dz;gs=(nxt['vs_km_s']-r['vs_km_s'])/dz
        layers.append(f"LAYER {r['top_of_layer_km']} {r['vp_km_s']:.10f} {gp:.10f} {r['vs_km_s']:.10f} {gs:.10f} 2.7 0")
    sources=[f"GTSRCE {r['nll_station']} XYZ {r['x(km)']:.8f} {r['y(km)']:.8f} {r['z(km)']:.8f} 0" for r in s.to_dict('records')]
    base='CONTROL 1 54321\nTRANS NONE\n'
    gridbase=base+f'VGOUT model\nVGGRID 2 {int(np.ceil(radius/h))+1} {int(round((bottom-top)/h))+1} 0 0 {top} {h} {h} {h} SLOW_LEN\n'+'\n'.join(layers)+'\n'
    if not (grids/'complete').exists():
        for phase in ['P','S']:
            control=grids/f'{phase}.in';control.write_text(gridbase+f'VGTYPE {phase}\nGTFILES model time {phase}\nGTMODE GRID2D ANGLES_NO\nGT_PLFD 1.e-3 0\n'+'\n'.join(sources)+'\n')
            execute(Path(cfg['binary_directory'])/'Vel2Grid',control,grids,grids/f'{phase}_velocity.log',300)
            execute(Path(cfg['binary_directory'])/'Grid2Time',control,grids,grids/f'{phase}_travel.log',300)
            assert len(list(grids.glob(f'time.{phase}.*.time.buf')))==len(s)
            print(f'{phase}: {len(s)} station-specific travel-time grids ready',flush=True)
        (grids/'complete').write_text('74 station/phase grids\n')
    bounds=grid_cfg['bfgs_bounds'][:3]
    # NLL 7 Octree uses (N-1)*spacing in x/y, but N*spacing in z.
    counts=[121,121,101];steps=[(b[1]-b[0])/(n if axis==2 else n-1) for axis,(b,n) in enumerate(zip(bounds,counts))]
    common=base+'\n'.join(sources)+'\nLOCSIG SeismoAgentBench expert\nLOCCOM Fixed GaMMA associations; Shelly linear profile\n'
    common+=f'LOCGRID {counts[0]} {counts[1]} {counts[2]} {bounds[0][0]} {bounds[1][0]} {bounds[2][0]} {steps[0]} {steps[1]} {steps[2]} PROB_DENSITY SAVE\n'
    common+=f'LOCSEARCH OCT 10 10 5 {cfg["search_min_node_km"]} {cfg["search_max_nodes"]} {cfg["posterior_samples"]} 0 0\n'
    common+='LOCMETH GAU_ANALYTIC 9999 10 -1 3 -1 100 -1 1\nLOCHYPOUT SAVE_NLLOC_ALL\n'
    common+=f'LOCGAU {cfg["model_error_s"]} 0\nLOCQUAL2ERR .1 .2 .5 1 999\nLOCPHASEID P P\nLOCPHASEID S S\nLOCANGLES ANGLES_NO 5\n'
    if args.scope=='pilot':
        chosen=set(pd.read_csv(source/'figures/example_events.csv').event_id)
        for mask in [e.depth_km<.5,e.depth_km>24.5,(e.depth_km>=.5)&(e.depth_km<=24.5),e.azimuth_gap_deg>180]:
            subset=e[mask].sort_values('origin_time')
            chosen.update(subset.iloc[np.linspace(0,len(subset)-1,4,dtype=int)].event_id)
        events=e[e.event_id.isin(chosen)]
    else:events=e
    events[['event_id']].to_csv(dest/'selection.csv',index=False)
    groups={k:g.to_dict('records') for k,g in p[p.event_id.isin(events.event_id)].groupby('event_id')}
    started=time.monotonic();results=[];links=[];failed=[]
    print(f'{args.scope}: {len(events)} events, {cfg["workers"]} CPU workers',flush=True)
    with ThreadPoolExecutor(max_workers=cfg['workers']) as pool:
        futures={pool.submit(locate,r,groups[r['event_id']],aliases,common,out,cfg,proj):r['event_id'] for r in events.to_dict('records')}
        for i,f in enumerate(as_completed(futures),1):
            try:
                row,phases=f.result();results.append(row);links+=phases
            except Exception as exc:
                failed.append(dict(event_id=futures[f],error=repr(exc)));print(f'FAILED {futures[f]}: {exc}',flush=True)
            if i%100==0 or args.scope=='pilot' or i==len(events):print(f'[{i}/{len(events)}] success={len(results)}, failed={len(failed)}, elapsed={time.monotonic()-started:.1f}s',flush=True)
    pd.DataFrame(failed,columns=['event_id','error']).to_csv(dest/'failures.csv',index=False)
    if results:
        result=pd.DataFrame(results).sort_values('event_id');phase=pd.DataFrame(links).sort_values('pick_id')
        assert phase.pick_id.is_unique and result.event_id.is_unique
        result.to_csv(dest/'events.csv',index=False);phase.to_csv(dest/'picks.csv',index=False)
        report=dict(status='complete' if not failed else 'incomplete',scope=args.scope,requested_events=len(events),located_events=int(result.status.eq('LOCATED').sum()),
                    parsed_events=len(result),rejected_events=int(result.status.ne('LOCATED').sum()),failed_events=len(failed),used_picks=len(phase),median_rms_s=float(result.rms_residual_s.median()),
                    median_horizontal_shift_km=float(result.horizontal_shift_km.median()),median_depth_shift_km=float(result.depth_shift_km.median()),
                    depth_bound_events=int(result.quality_flags.str.contains('near_depth_bound').sum()),seconds=round(time.monotonic()-started,2))
        (dest/'run.yaml').write_text(yaml.safe_dump(report,sort_keys=False));print(yaml.safe_dump(report),flush=True)
    if failed:raise RuntimeError(f'{len(failed)} events failed; successes are resumable')


if __name__=='__main__':main()
