#!/usr/bin/env python3
"""Run the TRACE-1.1 PhaseNet on the expert pilot; preserve picks and probabilities."""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import importlib.metadata
import csv
import hashlib
import itertools
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
from obspy import read, Stream, Trace, UTCDateTime
from obspy.signal.rotate import rotate2zne
import yaml

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def table(path, rows, fields):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)


def prepare(rows, root, start, end):
    """Intersect real contiguous components, require common sample grid, rotate to ZNE."""
    by_component={}
    for r in rows:
        st=read(str(root/r['path']),starttime=start,endtime=end).select(id=r['seed_id'])
        if r['component'] in by_component:
            previous,existing=by_component[r['component']]
            if any(previous[k]!=r[k] for k in ['azimuth_deg','dip_deg','sample_rate_hz']):
                raise ValueError('Changing component metadata requires separate processing')
            existing+=st
        else:by_component[r['component']]=(r,st)
    for _,st in by_component.values():st.merge(method=-1)
    names=['Z','N','E'] if {'Z','N','E'}<=by_component.keys() else ['Z','1','2']
    if not set(names)<=by_component.keys():raise ValueError('Three real components required')
    aligned=Stream();duration=0.;segments=0
    for traces in itertools.product(*(by_component[k][1] for k in names)):
        a=max(t.stats.starttime for t in traces);b=min(t.stats.endtime for t in traces)
        if b-a<30.01:continue
        pieces=[t.copy().trim(a,b,nearest_sample=False) for t in traces]
        if any(t.stats.sampling_rate!=100 for t in pieces):raise ValueError('Expected 100 Hz')
        if max(t.stats.starttime for t in pieces)-min(t.stats.starttime for t in pieces)>1e-5:
            raise ValueError('Component sample grids differ; no implicit interpolation')
        n=min(len(t) for t in pieces)
        args=[]
        for k,tr in zip(names,pieces):
            r=by_component[k][0];x=tr.data[:n].astype(np.float64)
            if np.ma.isMaskedArray(x) or not np.isfinite(x).all():raise ValueError('Missing/nonfinite samples')
            args.extend([x,float(r['azimuth_deg']),float(r['dip_deg'])])
        z,north,east=rotate2zne(*args)
        for component,data in [('Z',z),('N',north),('E',east)]:
            header=dict(pieces[0].stats);header['channel']=rows[0]['family']+component
            aligned+=Trace(data.astype(np.float32),header=header)
        segments+=1;duration+=max(0,min(float(b)+.01,float(end))-max(float(a),float(start)))
    if not aligned:raise ValueError('No usable contiguous three-component segment')
    return aligned,segments,duration


def plot_example(out, prepared, picks, annotations, start):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    # One common window around a strong P pick, rather than unrelated per-station windows.
    candidates=[p for p in picks if p['station_id']=='CI.CCC' and p['phase']=='P'] or [p for p in picks if p['phase']=='P']
    center=UTCDateTime(max(candidates,key=lambda p:p['probability'])['time_utc']) if candidates else start+60
    lo=center-10;hi=center+30
    fig,axes=plt.subplots(3,2,figsize=(7.09,6.0),layout='constrained')
    for i,station in enumerate(['CI.CCC','CI.CLC','PB.B918']):
        net,sta=station.split('.')
        for j,comp in enumerate(['Z','N','E']):
            for tr in prepared.select(network=net,station=sta,component=comp).copy().trim(lo,hi):
                x=tr.data.astype(float);x-=x.mean();scale=np.max(np.abs(x)) or 1
                axes[i,0].plot(tr.times(reftime=lo),j-x/scale*.4,lw=.55,color='#343434')
        for p in picks:
            if p['station_id']==station and lo<=UTCDateTime(p['time_utc'])<=hi:
                axes[i,0].axvline(UTCDateTime(p['time_utc'])-lo,color='#0072B2' if p['phase']=='P' else '#D55E00',lw=.7)
        for tr in annotations.select(network=net,station=sta).copy().trim(lo,hi):
            phase=tr.stats.channel[-1]
            if phase in 'PS':axes[i,1].plot(tr.times(reftime=lo),tr.data,color='#0072B2' if phase=='P' else '#D55E00',lw=.8)
        axes[i,0].set(title=station,yticks=[0,1,2],yticklabels=['Z','N','E'],ylim=(2.5,-.5),xlim=(0,40))
        axes[i,1].set(ylim=(0,1),xlim=(0,40),ylabel='Probability')
        for ax in axes[i]:ax.spines[['top','right']].set_visible(False)
    axes[0,1].legend(handles=[Line2D([],[],color='#0072B2',label='P'),Line2D([],[],color='#D55E00',label='S')],frameon=False)
    for ax in axes[-1]:ax.set_xlabel(f'Seconds since {str(lo)[11:23]} UTC')
    fig.savefig(out/'pick_example.png',dpi=250);fig.savefig(out/'pick_example.pdf');plt.close(fig)
    return str(lo),str(hi)


_WORKER_MODEL=None

def initialize_worker(library, weights, version, threads):
    global _WORKER_MODEL
    sys.path.insert(0,str(Path(library)/'ai_module'))
    import torch
    from phase_picking.model.phasenet import PhaseNet
    torch.set_num_threads(threads);torch.set_num_interop_threads(1)
    torch.manual_seed(0);np.random.seed(0);torch.use_deterministic_algorithms(True)
    base=Path(library)/'ai_module/phase_picking/pretrained/v3/phasenet'
    meta=json.loads((base/f'{weights}.json.v{version}').read_text())
    model=PhaseNet(**meta['model_args'])
    state=torch.load(base/f'{weights}.pt.v{version}',map_location='cpu',weights_only=True)
    model.load_state_dict(state.get('state_dict',state),strict=True)
    model.default_args.update(meta.get('default_args',{}));model.eval()
    _WORKER_MODEL=model


def pick_station(key, rows, root, start, end, cfg):
    import torch
    station,location,family=key
    pad=cfg['picking']['buffer_seconds']
    st,segments,seconds=prepare(rows,root,start-pad,end+pad)
    with torch.inference_mode():
        prediction=_WORKER_MODEL.annotate(st,strict=True,flexible_horizontal_components=False,batch_size=cfg['picking']['batch_size'])
        classified=_WORKER_MODEL.classify_aggregate(prediction,dict(_WORKER_MODEL.default_args,
            P_threshold=cfg['picking']['p_threshold'],S_threshold=cfg['picking']['s_threshold']))
    picks=[]
    for p in classified.picks:
        if start<=p.peak_time<end:
            picks.append(dict(pick_id='',station_id=station,location=location,channel_family=family,
                phase=p.phase,time_utc=str(p.peak_time),probability=float(p.peak_value),
                onset_utc=str(p.start_time),offset_utc=str(p.end_time),
                source_channels=';'.join(sorted({r['seed_id'] for r in rows}))))
    stats=dict(station_id=station,location=location,family=family,segments=segments,
        buffered_common_seconds=seconds,picks=len(picks),orientation='StationXML azimuth/dip to ZNE')
    return key,st,prediction,picks,stats


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,default=HERE/'00_config/config.yaml')
    ap.add_argument('--library',type=Path,help='TRACE-1.1 seismoagent/library; overrides config')
    ap.add_argument('--scope',choices=['pilot','full'],default='pilot')
    ap.add_argument('--workers',type=int,default=16,help='Full-run CPU processes')
    ap.add_argument('--chunk-hours',type=int,default=6,help='Full-run block length')
    args=ap.parse_args();config_path=args.config.resolve();cfg=yaml.safe_load(config_path.read_text())
    if args.scope=='full':
        run_full(args,config_path,cfg);return
    out=HERE/cfg['export_root']/'02_pick_phasenet';out.mkdir(parents=True,exist_ok=True)
    # Cache is local to this step; importing the library must not download weights.
    os.environ['SEISBENCH_CACHE_ROOT']=str((out/'cache').resolve())
    library=(args.library or HERE/cfg['tools']['trace_library']).resolve()
    for name in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']:
        os.environ[name]=str(cfg['picking']['cpu_threads'])
    import matplotlib
    matplotlib.rcParams.update({'font.size':7,'axes.titlesize':8,'pdf.fonttype':42})
    base=library/'ai_module/phase_picking/pretrained/v3/phasenet'
    model_path=base/f"{cfg['methods']['weights']}.pt.v{cfg['methods']['weight_version']}"
    meta_path=base/f"{cfg['methods']['weights']}.json.v{cfg['methods']['weight_version']}"
    meta=json.loads(meta_path.read_text())
    previous=HERE/cfg['export_root']/'01_prepare_inputs'
    if yaml.safe_load((previous/'config.yaml').read_text())!=cfg:raise ValueError('Run step 01 again after changing config')
    source=list(csv.DictReader((previous/'waveform_inputs.csv').open()))
    groups={}
    for r in source:
        if r['pilot_candidate']=='True':groups.setdefault((r['station_id'],r['location'],r['family']),[]).append(r)
    root=(HERE/cfg['data_root']).resolve()
    start,end=(UTCDateTime(cfg['pilot_window'][k]) for k in ['start_utc','end_utc'])
    pad=cfg['picking']['buffer_seconds'];picks=[];statistics=[];prepared=Stream();annotations=Stream();probs={}
    started=time.monotonic()
    workers=cfg['picking']['cpu_workers']
    if workers<1 or cfg['picking']['cpu_threads']<1:raise ValueError('CPU worker/thread counts must be positive')
    print(f'CPU-only: {workers} station workers, {cfg["picking"]["cpu_threads"]} compute threads per worker',flush=True)
    with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn'),
        initializer=initialize_worker,initargs=(str(library),cfg['methods']['weights'],cfg['methods']['weight_version'],cfg['picking']['cpu_threads'])) as pool:
        futures=[pool.submit(pick_station,key,rows,root,start,end,cfg) for key,rows in sorted(groups.items())]
        for i,future in enumerate(as_completed(futures),1):
            (station,location,family),st,prediction,station_picks,stats=future.result()
            picks.extend(station_picks);statistics.append(stats)
            for j,tr in enumerate(prediction):
                key=f'{station}_{family}_{location or "blank"}_{j}'
                probs[key+'_values']=tr.data;probs[key+'_start_utc']=str(tr.stats.starttime)
                probs[key+'_sample_rate_hz']=tr.stats.sampling_rate;probs[key+'_phase']=tr.stats.channel[-1]
            prepared+=st;annotations+=prediction
            print(f'[{i}/{len(groups)}] {station}.{family}: {len(station_picks)} picks',flush=True)
    statistics.sort(key=lambda r:(r['station_id'],r['location'],r['family']))
    prepared.sort();annotations.sort()
    picks.sort(key=lambda p:(p['time_utc'],p['station_id'],p['phase']))
    for i,p in enumerate(picks,1):p['pick_id']=f'pick_{i:07d}'
    fields=['pick_id','station_id','location','channel_family','phase','time_utc','probability','onset_utc','offset_utc','source_channels']
    table(out/'picks.csv',picks,fields);table(out/'station_summary.csv',statistics,list(statistics[0]))
    prepared.write(str(out/'prepared_waveforms.mseed'),format='MSEED',encoding='FLOAT32')
    np.savez_compressed(out/'probabilities.npz',**probs)
    window=plot_example(out,prepared,picks,annotations,start)
    provenance=dict(model_sha256=digest(model_path),model_metadata_sha256=digest(meta_path),
        implementation_sha256=digest(library/'ai_module/phase_picking/model/phasenet.py'),
        implementation_base_sha256=digest(library/'ai_module/phase_picking/model/base.py'),
        input_table_sha256=digest(previous/'waveform_inputs.csv'),script_sha256=digest(Path(__file__)),
        torch=str(importlib.metadata.version("torch")),seisbench=str(importlib.metadata.version("seisbench")),python=sys.version.split()[0],
        model_args=meta['model_args'],annotation_defaults=meta.get("default_args",{}),config=cfg,
        seconds=round(time.monotonic()-started,2),stations=len(groups),picks=len(picks),example_window=window)
    (out/'run.yaml').write_text(yaml.safe_dump(provenance,sort_keys=False))
    (out/'README.md').write_text(f'''# PhaseNet pilot results

Window: [{start}, {end}); {len(groups)} three-component HH/EH instruments. Produced {len(picks)} picks ({sum(p['phase']=='P' for p in picks)} P, {sum(p['phase']=='S' for p in picks)} S).

Uses TRACE-1.1 PhaseNet with local original v2 weights on CPU ({workers} worker processes, {cfg["picking"]["cpu_threads"]} compute threads each). The reference recommends classify or annotate; we run annotate once and its classify_aggregate to retain both probabilities and picks. Weight default overlap/blinding are applied. Thresholds P={cfg['picking']['p_threshold']}, S={cfg['picking']['s_threshold']} are initial pilot settings, not calibrated precision estimates. Inference uses strict simultaneous three-component coverage and {pad} s input buffers, retaining only picks inside the target interval. Raw counts are rotated to ZNE using station azimuth/dip; relative component responses are assumed compatible within each instrument. No response removal, extra filter, resampling, gap interpolation, copied components, or reference catalog input. Model window normalization follows the supplied weights.

- `picks.csv`: all thresholded arrivals with IDs, confidence scores and original channel identities. These are not associated events.
- `station_summary.csv`: per-instrument processing counts.
- `prepared_waveforms.mseed`: real contiguous, common-component segments after orientation conversion (float32 counts); derived data only.
- `probabilities.npz`: per-instrument phase probabilities and time axes; NaNs at blinded prediction edges are expected. Load with allow_pickle=False.
- `pick_example.png/pdf`: three stations in a common window around the strongest CCC P pick (fallback: strongest P elsewhere). Components normalized independently for display; P blue and S orange. Selection illustrates inference and does not validate pick accuracy.
- `run.yaml`: configuration, code/weight/input hashes and runtime versions.

Next: review the pilot pick/coverage outputs and pass these picks to GaMMA. No catalog, event location or magnitude has been inferred in this step. HN and vertical-only inputs remain deferred. Original waveform files are unchanged.
''')
    print(f'Completed: {len(picks)} picks; {time.monotonic()-started:.1f} s',flush=True)


PICK_FIELDS=['pick_id','station_id','location','channel_family','phase','time_utc','probability','onset_utc','offset_utc','source_channels']


def pick_chunk(job_id,key,rows,root,start,end,cfg,out):
    """Save only picks; large waveform/probability arrays remain inside the worker."""
    began=time.monotonic()
    _,st,prediction,picks,stats=pick_station(key,rows,root,UTCDateTime(start),UTCDateTime(end),cfg)
    target=Path(out)/'chunks'/f'{job_id}.csv'
    temporary=target.with_suffix('.tmp')
    table(temporary,picks,PICK_FIELDS);temporary.replace(target)
    stats.update(job_id=job_id,start_utc=start,end_utc=end,seconds=round(time.monotonic()-began,2),
                 csv_sha256=digest(target))
    return stats


def run_full(args,config_path,cfg):
    """Resume independently completed blocks with an input/code/model fingerprint."""
    from collections import Counter
    out=HERE/cfg['export_root']/'02_pick_phasenet/full'
    (out/'chunks').mkdir(parents=True,exist_ok=True)
    previous=HERE/cfg['export_root']/'01_prepare_inputs/full'
    if yaml.safe_load((previous/'config.yaml').read_text())!=cfg:
        raise ValueError('Run 01_pipeline/01_prepare_inputs.py --scope full first')
    if args.workers<1 or args.chunk_hours<1:raise ValueError('Positive workers/chunk hours required')
    root=(HERE/cfg['data_root']).resolve()
    library=(args.library or HERE/cfg['tools']['trace_library']).resolve()
    os.environ['SEISBENCH_CACHE_ROOT']=str(out/'cache')
    for name in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS']:
        os.environ[name]=str(cfg['picking']['cpu_threads'])
    import seisbench  # Initialize shared cache before workers import it concurrently.
    source=list(csv.DictReader((previous/'waveform_inputs.csv').open()))
    groups={};identities=[]
    for r in source:
        f=root/r['path'];stat=f.stat()
        if stat.st_size!=int(r['bytes']):raise ValueError(f'Stale source size: {f}')
        identities.append((r['path'],stat.st_size,stat.st_mtime_ns))
        if r['pilot_candidate']=='True':groups.setdefault((r['station_id'],r['location'],r['family']),[]).append(r)
    start,end=(UTCDateTime(cfg['candidate_window'][k]) for k in ['start_utc','end_utc'])
    base=library/'ai_module/phase_picking'
    fingerprint=dict(config=cfg,chunk_hours=args.chunk_hours,input_table_sha256=digest(previous/'waveform_inputs.csv'),
        source_stat_sha256=hashlib.sha256(json.dumps(identities).encode()).hexdigest(),
        script_sha256=digest(Path(__file__)),
        model_sha256=digest(base/f"pretrained/v3/phasenet/{cfg['methods']['weights']}.pt.v{cfg['methods']['weight_version']}"),
        metadata_sha256=digest(base/f"pretrained/v3/phasenet/{cfg['methods']['weights']}.json.v{cfg['methods']['weight_version']}"),
        implementation_sha256=digest(base/'model/phasenet.py'),base_sha256=digest(base/'model/base.py'),
        versions={k:str(importlib.metadata.version(k)) for k in ['torch','seisbench','obspy','numpy']})
    # A process lock prevents simultaneous writers to this output directory.
    import fcntl
    lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    signature=out/'inputs.yaml'
    if signature.exists() and yaml.safe_load(signature.read_text())!=fingerprint:
        raise ValueError('Existing full-run inputs/code changed; use a separate export root')
    signature.write_text(yaml.safe_dump(fingerprint,sort_keys=False))
    jobs=[];a=start
    while a<end:
        b=min(a+args.chunk_hours*3600,end)
        for key,rows in sorted(groups.items()):
            job_id='_'.join([key[0],key[1] or 'blank',key[2],a.strftime('%Y%m%dT%H%M%S')])
            jobs.append((job_id,key,rows,root,str(a),str(b),cfg,str(out)))
        a=b
    journal=out/'completed.jsonl';done={}
    if journal.exists():
        for line in journal.read_text().splitlines():
            try:record=json.loads(line)
            except json.JSONDecodeError:continue # incomplete final journal write
            f=out/'chunks'/f"{record['job_id']}.csv"
            if f.exists() and digest(f)==record['csv_sha256']:done[record['job_id']]=record
    expected={j[0] for j in jobs};done={k:v for k,v in done.items() if k in expected}
    pending=[job for job in jobs if job[0] not in done];began=time.monotonic();failures=[]
    print(f'Full CPU picking: {len(groups)} instruments, {len(jobs)} blocks, {len(done)} resumed; {args.workers} workers x {cfg["picking"]["cpu_threads"]} threads',flush=True)
    with journal.open('a') as log, ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn'),
        initializer=initialize_worker,initargs=(str(library),cfg['methods']['weights'],cfg['methods']['weight_version'],cfg['picking']['cpu_threads'])) as pool:
        futures={pool.submit(pick_chunk,*job):job[0] for job in pending}
        for future in as_completed(futures):
            job_id=futures[future]
            try:
                record=future.result();done[job_id]=record
                log.write(json.dumps(record)+'\n');log.flush();os.fsync(log.fileno())
                elapsed=time.monotonic()-began
                print(f'[{len(done)}/{len(jobs)}] {job_id}: {record["picks"]} picks; block {record["seconds"]:.1f}s; elapsed {elapsed/60:.1f}min',flush=True)
            except Exception as exc:
                failures.append(dict(job_id=job_id,error=repr(exc)))
                print(f'FAILED {job_id}: {exc!r}',flush=True)
    if failures:
        (out/'failures.yaml').write_text(yaml.safe_dump(failures))
        raise RuntimeError(f'{len(failures)} blocks failed; successful blocks are resumable')
    picks=[]
    for job in jobs:picks.extend(csv.DictReader((out/'chunks'/f'{job[0]}.csv').open()))
    picks.sort(key=lambda p:(p['time_utc'],p['station_id'],p['location'],p['channel_family'],p['phase']))
    unique=[];seen=set();duplicates=0
    for p in picks:
        identity=tuple(p[k] for k in ['station_id','location','channel_family','phase','time_utc'])
        if identity in seen:duplicates+=1;continue
        seen.add(identity)
        assert start<=UTCDateTime(p['time_utc'])<end and p['phase'] in ['P','S']
        assert cfg['picking'][p['phase'].lower()+'_threshold']<=float(p['probability'])<=1
        p['pick_id']=f'pick_{len(unique)+1:09d}';unique.append(p)
    table(out/'picks.csv',unique,PICK_FIELDS)
    statistics=sorted(done.values(),key=lambda r:r['job_id'])
    table(out/'chunk_summary.csv',statistics,list(statistics[0]))
    counts=Counter((p['station_id'],p['location'],p['channel_family'],p['phase']) for p in unique)
    summary=[dict(station_id=k[0],location=k[1],family=k[2],p_picks=counts[(*k,'P')],s_picks=counts[(*k,'S')],
                  completed_blocks=sum(r['station_id']==k[0] and r['location']==k[1] and r['family']==k[2] for r in statistics)) for k in sorted(groups)]
    table(out/'station_summary.csv',summary,list(summary[0]))
    # Report near-coincident picks across block boundaries; do not delete plausible arrivals.
    close=[];last={};boundaries=[start+i*args.chunk_hours*3600 for i in range(1,int((end-start-1)//(args.chunk_hours*3600))+1)]
    for p in unique:
        k=tuple(p[x] for x in ['station_id','location','channel_family','phase']);t=UTCDateTime(p['time_utc'])
        if k in last:
            prev,pt=last[k]
            if t-pt<=.1 and any(pt<b<=t for b in boundaries):
                close.append(dict(first_pick_id=prev['pick_id'],second_pick_id=p['pick_id'],separation_seconds=t-pt))
        last[k]=(p,t)
    table(out/'boundary_review.csv',close,['first_pick_id','second_pick_id','separation_seconds'])
    result=dict(status='complete',start_utc=str(start),end_utc=str(end),stations=len(groups),
        expected_blocks=len(jobs),completed_blocks=len(done),picks=len(unique),p_picks=sum(p['phase']=='P' for p in unique),
        s_picks=sum(p['phase']=='S' for p in unique),exact_duplicates_removed=duplicates,boundary_pairs_for_review=len(close),
        workers=args.workers,threads_per_worker=cfg['picking']['cpu_threads'],wall_seconds_this_invocation=round(time.monotonic()-began,2))
    (out/'run.yaml').write_text(yaml.safe_dump(result,sort_keys=False))
    (out/'README.md').write_text(f'''# Full PhaseNet picks

Window: [{start}, {end}). {len(unique)} arrivals from {len(groups)} three-component HH/EH instruments; {len(done)}/{len(jobs)} blocks completed.

`picks.csv` is the merged downstream arrival table (UTC, P/S, probability, station/location/family and original channels). These are unassociated thresholded arrivals, not earthquake events. `station_summary.csv` and `chunk_summary.csv` record counts and processing. `inputs.yaml` records configuration, versions, source size/mtime fingerprint and code/model hashes; `run.yaml` records completion. `chunks/` plus `completed.jsonl` support restart. `boundary_review.csv` lists same-phase arrivals separated by <=0.1 s across block boundaries; only exact duplicates are removed.

Local TRACE-1.1 PhaseNet original v2 weights, CPU only, {args.workers} processes. Blocks are {args.chunk_hours} h with {cfg['picking']['buffer_seconds']} s input buffers from indexed candidate files, clipped to half-open output intervals. P/S thresholds are {cfg['picking']['p_threshold']}/{cfg['picking']['s_threshold']}; scores are not calibrated accuracy estimates. Real simultaneous contiguous components are rotated using StationXML azimuth/dip. Model normalization is retained. No response removal, added filtering, interpolation, invented channels or reference catalog input. Original data are unchanged.

CI.APL (HN), CI.WNM/CI.WRV2/CI.WVP2 (vertical only) remain outside this three-component baseline. Gaps and segments shorter than 30.01 s are not filled; blind margins near real gaps and candidate edges can lose picks. Candidate files supply buffers across internal day boundaries, but no data outside the three-day input manifest are loaded. Buffered common seconds include overlap and must not be summed as unique coverage. Full waveform/probability arrays are not exported. Pilot outputs remain in the parent directory.
''')
    print(yaml.safe_dump(result,sort_keys=False),flush=True)


if __name__=='__main__':main()
