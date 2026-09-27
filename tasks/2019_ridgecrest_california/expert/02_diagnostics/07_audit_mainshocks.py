#!/usr/bin/env python3
"""Bounded mainshock arrival audit. Reference arrivals are diagnostic inputs only."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import argparse
import importlib.util
import json
import re
import numpy as np
import pandas as pd
from obspy import read, read_events, Stream, UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
CASE = HERE.parents[2] / 'benchmark_source/2019_ridgecrest_california'
OUT = HERE / 'export/07_audit_mainshocks'
EVENTS = [('M6.4', 'gamma_0000046', '38443183'), ('M7.1', 'gamma_0005482', '38457511')]
spec = importlib.util.spec_from_file_location('depth_audit', HERE / '02_diagnostics/06_diagnose_depth.py')
depth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(depth)
BLUE, RED = '#0072B2', '#D55E00'


def inputs():
    gp = pd.read_csv(depth.GAMMA / 'picks.csv', keep_default_na=False)
    gp['epoch'] = pd.to_datetime(gp.time_utc, utc=True, format='ISO8601').astype('int64') / 1e9
    gp['onset_epoch'] = pd.to_datetime(gp.onset_utc, utc=True, format='ISO8601').astype('int64') / 1e9
    stations = pd.read_csv(depth.NLL / 'stations.csv', keep_default_na=False).set_index('id')
    return gp, stations


def official(number):
    path = OUT / 'sources' / f'ci{number}.xml'
    if not path.exists():
        import requests
        session = requests.Session(); session.trust_env = False
        url = f'https://service.scedc.caltech.edu/fdsnws/event/1/query?eventid={number}&includearrivals=true&format=xml'
        response = session.get(url, timeout=60); response.raise_for_status()
        path.write_bytes(response.content)
    event = read_events(str(path))[0]
    origin = event.preferred_origin() or event.origins[0]
    # SCEDC reuses IDs for Arrival and Pick. Resolve explicitly within event.picks.
    picks = {str(p.resource_id): p for p in event.picks}
    rows = []
    for arrival in origin.arrivals:
        pick = picks[str(arrival.pick_id)]; wave = pick.waveform_id
        location = wave.location_code or ''
        if location == '--': location = ''
        instrument = '.'.join([wave.network_code, wave.station_code, location, wave.channel_code[:2]])
        rows.append(dict(reference_pick_id=str(pick.resource_id), station_id=wave.network_code + '.' + wave.station_code,
                         instrument_id=instrument, channel=wave.channel_code, location=location,
                         phase=arrival.phase, time_utc=str(pick.time), epoch=float(pick.time),
                         weight=arrival.time_weight, residual_s=arrival.time_residual,
                         time_correction_s=arrival.time_correction, evaluation_mode=pick.evaluation_mode))
    metadata = dict(event_id='ci'+number, origin_time=str(origin.time), latitude=origin.latitude,
                    longitude=origin.longitude, depth_km=origin.depth / 1000, depth_type=origin.depth_type,
                    depth_uncertainty_km=(origin.depth_errors.uncertainty or 0) / 1000,
                    origin_method=str(origin.method_id), arrivals=len(rows))
    return pd.DataFrame(rows), metadata


def tables(gp, stations):
    comparisons = []; coverage = []; metadata = []
    for name, eid, number in EVENTS:
        ref, meta = official(number); meta['expert_event_id'] = eid; metadata.append(meta)
        ref.assign(event_id=eid).to_csv(OUT / f'official_{number}.csv', index=False)
        assigned = gp[gp.event_id.eq(eid)]
        for pick in assigned.to_dict('records'):
            candidates = ref[ref.station_id.eq(pick['station_id']) & ref.phase.eq(pick['phase'])]
            exact = candidates[candidates.instrument_id.eq(pick['instrument_id'])]
            chosen = exact if len(exact) else candidates
            row = dict(event_id=eid, **{k: pick[k] for k in ['pick_id', 'instrument_id', 'station_id', 'phase', 'time_utc', 'probability', 'onset_utc']},
                       match_level='same_instrument' if len(exact) else 'station_only', reference_candidates=len(chosen))
            if len(chosen) == 1:
                r = chosen.iloc[0]
                row.update(reference_channel=r.channel, reference_time_utc=r.time_utc, reference_weight=r.weight,
                           peak_minus_reference_s=pick['epoch']-r.epoch,
                           threshold_start_minus_reference_s=pick['onset_epoch']-r.epoch)
            else: row['match_level'] = 'unmatched' if len(chosen)==0 else 'ambiguous'
            comparisons.append(row)
        # Audit each preferred-origin arrival at a station used by this pipeline.
        for r in ref[ref.station_id.isin(stations.station_id) & ref.phase.isin(['P','S'])].to_dict('records'):
            local = gp[gp.station_id.eq(r['station_id']) & gp.phase.eq(r['phase']) & gp.epoch.between(r['epoch']-5, r['epoch']+5)]
            exact = local[local.instrument_id.eq(r['instrument_id'])]
            if r['instrument_id'] in stations.index: local = exact
            row = dict(event_id=eid, **r, native_instrument_available=r['instrument_id'] in stations.index)
            if len(local):
                nearest = local.iloc[np.argmin(np.abs(local.epoch.to_numpy()-r['epoch']))]
                delta = float(nearest.epoch-r['epoch'])
                row.update(nearest_pick_id=nearest.pick_id, nearest_instrument=nearest.instrument_id,
                           nearest_event_id=nearest.event_id, nearest_delta_s=delta,
                           association=('target' if nearest.event_id==eid else 'other_event' if nearest.event_id else 'unassigned')
                           if abs(delta)<=1 else 'no_pick_within_1s')
            else: row['association']='no_pick_within_5s'
            coverage.append(row)
        window = gp[gp.epoch.between(float(UTCDateTime(meta['origin_time']))-30, float(UTCDateTime(meta['origin_time']))+120)]
        window.to_csv(OUT / f'{name}_nearby_picks.csv', index=False)
    pd.DataFrame(comparisons).to_csv(OUT/'assigned_arrival_comparison.csv', index=False)
    pd.DataFrame(coverage).to_csv(OUT/'reference_arrival_coverage.csv', index=False)
    (OUT/'origins.json').write_text(json.dumps(metadata, indent=2))
    return pd.DataFrame(comparisons)


def load_window(task):
    name, ins, rows, anchor = task
    cache = OUT / 'windows' / f'{name}_{ins}.mseed'
    if cache.exists(): return ins, read(str(cache))
    root = (CASE/'data/waveforms').resolve(); start=anchor-40; end=anchor+130
    stream = Stream()
    for r in rows:
        times = re.findall(r'(\d{8}T\d{6})Z', r['path'])
        if len(times)!=2: raise ValueError(r['path'])
        a,b = map(UTCDateTime,times)
        if b<=start or a>=end: continue
        stream += read(str(root/r['path']),starttime=start,endtime=end).select(id=r['seed_id'])
    stream.merge(method=-1)
    assert len(stream)>0, ins
    stream.write(str(cache), format='MSEED')
    return ins, stream


def plots(gp, stations, comparison):
    index = pd.read_csv(HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',keep_default_na=False)
    (OUT/'windows').mkdir(exist_ok=True); (OUT/'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':8, 'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    for name,eid,number in EVENTS:
        ref,meta=official(number);anchor=UTCDateTime(meta['origin_time']);assigned=gp[gp.event_id.eq(eid)]
        instruments=sorted(set(assigned.instrument_id) | set(ref.instrument_id).intersection(stations.index))
        tasks=[]
        for ins in instruments:
            net,sta,loc,fam=ins.split('.')
            rows=index[index.station_id.eq(net+'.'+sta)&index.location.eq(loc)&index.family.eq(fam)]
            tasks.append((name,ins,rows.to_dict('records'),anchor))
        with ThreadPoolExecutor(6) as pool: streams=dict(pool.map(load_window,tasks))
        for phase in ['P','S']:
            picks=assigned[assigned.phase.eq(phase)].sort_values('time_utc').to_dict('records')
            for page in range((len(picks)+8)//9):
                group=picks[page*9:(page+1)*9]
                fig,axes=plt.subplots(3,3,figsize=(12,8),layout='constrained')
                for ax,pick in zip(axes.flat,group):
                    c=comparison[comparison.pick_id.eq(pick['pick_id'])].iloc[0]
                    has_ref=pd.notna(c.get('reference_time_utc'))
                    center=UTCDateTime(c.reference_time_utc) if has_ref else UTCDateTime(pick['time_utc'])
                    stream=streams[pick['instrument_id']]
                    selected=stream.select(component='Z') if phase=='P' else stream
                    for k,tr in enumerate(sorted(selected,key=lambda t:t.stats.channel)):
                        # Raw detrended counts are the onset evidence; no zero-phase filtering.
                        segment=tr.copy().trim(center-2,center+4).detrend('demean')
                        if not segment.stats.npts: continue
                        scale=max(float(np.max(np.abs(segment.data))),1.)
                        ax.plot(segment.times(reftime=center),k+segment.data*.38/scale,color='black',lw=.5)
                        if phase=='P': ax.text(.01,.95,tr.stats.channel,transform=ax.transAxes,fontsize=7,va='top')
                    for _,r in gp[gp.instrument_id.eq(pick['instrument_id']) & gp.epoch.between(float(center)-2,float(center)+4)].iterrows():
                        ax.axvline(r.epoch-float(center),color=RED if r.phase=='P' else BLUE,
                                   ls='-' if r.event_id==eid else ':',lw=1.1 if r.pick_id==pick['pick_id'] else .55)
                    ax.axvline(float(UTCDateTime(pick['onset_utc'])-center),color='#009E73',ls=':',lw=.8)
                    if has_ref: ax.axvline(0,color='black',ls='--',lw=.8)
                    suffix='' if not has_ref else f"  Δt={c.peak_minus_reference_s:+.2f}s"
                    ax.set(title=pick['station_id']+suffix,xlim=(-2,4),yticks=[],xlabel='Time from reference pick (s)' if has_ref else 'Time from PhaseNet pick (s)')
                    if phase=='S': ax.set_yticks(range(len(selected)),[tr.stats.channel for tr in sorted(selected,key=lambda t:t.stats.channel)],fontsize=7)
                for ax in list(axes.flat)[len(group):]: ax.set_visible(False)
                fig.suptitle(f'{name} {phase} arrivals — {page+1}',fontsize=11)
                fig.legend(handles=[Line2D([],[],color=RED,label='P'),Line2D([],[],color=BLUE,label='S'),
                            Line2D([],[],color='black',ls='--',label='SCEDC'),Line2D([],[],color='#009E73',ls=':',label='Threshold start')],
                           loc='outside lower center',ncol=4,frameon=False)
                for ext in ['png','pdf']: fig.savefig(OUT/'figures'/f'{name}_{phase}_{page+1:02d}.{ext}',dpi=180)
                plt.close(fig)
        print(name,'waveform pages ready',flush=True)
        if name=='M7.1':
            coverage=pd.read_csv(OUT/'reference_arrival_coverage.csv',keep_default_na=False)
            missing=coverage[coverage.event_id.eq(eid)&coverage.weight.gt(0)&coverage.association.ne('target')]
            assert len(missing)<=9
            fig,axes=plt.subplots(3,3,figsize=(12,8),layout='constrained')
            for ax,r in zip(axes.flat,missing.itertuples()):
                ins=r.instrument_id if r.instrument_id in streams else next(s for s in streams if s.startswith(r.station_id+'.'))
                center=UTCDateTime(r.time_utc)
                selected=streams[ins].select(component='Z') if r.phase=='P' else streams[ins]
                selected=sorted(selected,key=lambda t:t.stats.channel)
                for k,tr in enumerate(selected):
                    segment=tr.copy().trim(center-2,center+4).detrend('demean')
                    scale=max(float(np.max(np.abs(segment.data))),1.)
                    ax.plot(segment.times(reftime=center),k+.38*segment.data/scale,c='black',lw=.5)
                for p in gp[gp.instrument_id.eq(ins)&gp.epoch.between(float(center)-2,float(center)+4)].itertuples():
                    ax.axvline(p.epoch-float(center),c=RED if p.phase=='P' else BLUE,ls='-' if p.event_id==eid else ':',lw=.8)
                ax.axvline(0,c='black',ls='--',lw=.8)
                ax.set(title=f'{r.station_id} {r.phase} (reference {r.channel})',xlim=(-2,4),xlabel='Time from SCEDC pick (s)')
                ax.set_yticks(range(len(selected)),[tr.stats.channel for tr in selected],fontsize=7)
            for ax in list(axes.flat)[len(missing):]:ax.set_visible(False)
            fig.suptitle('M7.1 arrivals without a target pick within 1 s',fontsize=11)
            for ext in ['png','pdf']:fig.savefig(OUT/'figures'/f'{name}_missing_or_delayed.{ext}',dpi=180)
            plt.close(fig)


def fit_one(task):
    job,model,variant,changed=task
    result,profile,_=depth.solve(job)
    result.update(model=model,variant=variant,changed_times=changed)
    for row in profile: row.update(model=model,variant=variant)
    return result,profile


def strong_motion(gp):
    """Two short HN windows, isolated from the benchmark's frozen waveform inputs."""
    import requests
    from io import BytesIO
    from datetime import datetime, timezone
    ref,meta=official('38457511');anchor=UTCDateTime(meta['origin_time'])
    fig,axes=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    download_path=OUT/'sources/downloads.json'
    records=json.loads(download_path.read_text()) if download_path.exists() else []
    for i,station in enumerate(['CLC','WRC2']):
        path=OUT/'windows'/f'M7.1_CI.{station}..HN.mseed'
        if not path.exists():
            session=requests.Session();session.trust_env=False
            params=dict(network='CI',station=station,location='--',channel='HN?',
                        starttime=str(anchor-30),endtime=str(anchor+90))
            response=session.get('https://service.scedc.caltech.edu/fdsnws/dataselect/1/query',params=params,timeout=60)
            response.raise_for_status();stream=read(BytesIO(response.content))
            assert {tr.stats.channel for tr in stream}=={'HNE','HNN','HNZ'}
            path.write_bytes(response.content)
            records.append(dict(file=str(path.relative_to(OUT)),url=response.url,bytes=len(response.content),
                                status=response.status_code,retrieved_utc=datetime.now(timezone.utc).isoformat(),purpose='two-minute diagnostic window only'))
            download_path.write_text(json.dumps(records,indent=2))
        reference=ref[ref.station_id.eq('CI.'+station)&ref.phase.eq('S')&ref.weight.gt(0)].iloc[0]
        center=UTCDateTime(reference.time_utc)
        for j,family in enumerate(['HH','HN']):
            stream=read(str(OUT/'windows'/f'M7.1_CI.{station}..{family}.mseed'))
            ax=axes[i,j]
            for k,tr in enumerate(sorted(stream,key=lambda t:t.stats.channel)):
                segment=tr.copy().trim(center-3,center+5).detrend('demean')
                ax.plot(segment.times(reftime=center),k+.4*segment.data/max(np.max(np.abs(segment.data)),1.),c='black',lw=.5)
            ax.axvline(0,c='black',ls='--',lw=.9)
            for p in gp[gp.station_id.eq('CI.'+station)&gp.event_id.eq('gamma_0005482')].itertuples():
                ax.axvline(p.epoch-float(center),color=RED if p.phase=='P' else BLUE,lw=.9)
            ax.set(title=f'CI.{station} — {family}',xlabel='Time from SCEDC S pick (s)',xlim=(-3,5))
            ax.set_yticks(range(len(stream)),[t.stats.channel for t in sorted(stream,key=lambda t:t.stats.channel)])
        print(station,'HN comparison complete',flush=True)
    fig.legend(handles=[Line2D([],[],color='black',ls='--',label='SCEDC S (HN)'),
                        Line2D([],[],color=RED,label='PhaseNet P (HH)'),Line2D([],[],color=BLUE,label='PhaseNet S (HH)')],
               loc='outside lower center',ncol=3,frameon=False)
    for ext in ['png','pdf']:fig.savefig(OUT/'figures'/f'M7.1_HH_HN_comparison.{ext}',dpi=180)
    plt.close(fig)


def experiments(gp):
    cfg,bounds,jobs=depth.setup();results=[];profiles=[]
    for model,directory in [('linear',depth.NLL/'grids'),('layered',depth.OUT/'layered_grids')]:
        tasks=[]
        for name,eid,number in EVENTS:
            original=next(j for j in jobs if j['event_id']==eid); ref,_=official(number)
            own=gp.set_index('pick_id')
            for variant in ['original','threshold_start','official_exact_times','official_station_times','P_only',
                            'original_exact_subset','official_exact_subset']:
                job=dict(original);job['observed']=list(original['observed']);changed=0; matched=[]
                for i,(ins,phase,pid) in enumerate(zip(job['instruments'],job['phases'],job['pick_ids'])):
                    time=None
                    if variant=='threshold_start': time=own.loc[pid,'onset_utc']
                    if variant.startswith('official') or variant=='original_exact_subset':
                        rr=ref[ref.station_id.eq('.'.join(ins.split('.')[:2])) & ref.phase.eq(phase) & ref.weight.gt(0)]
                        if variant!='official_station_times': rr=rr[rr.instrument_id.eq(ins)]
                        if len(rr)==1:
                            matched.append(i)
                            if variant!='original_exact_subset': time=rr.iloc[0].time_utc
                    if time is not None:
                        job['observed'][i]=(pd.Timestamp(time)-pd.Timestamp(job['anchor'])).total_seconds();changed+=1
                if variant=='P_only' or variant.endswith('_subset'):
                    ids=matched if variant.endswith('_subset') else [i for i,p in enumerate(job['phases']) if p=='P']
                    for key in ['observed','pick_ids','phases','instruments','keys','stations','native_tt']:job[key]=[job[key][i] for i in ids]
                tasks.append((job,model,variant,changed))
        with ProcessPoolExecutor(8,initializer=depth.initialize,initargs=(directory,cfg,bounds)) as pool:
            for result,profile in pool.map(fit_one,tasks):
                results.append(result);profiles+=profile
                print(model,result['event_id'],result['variant'],round(result['depth_km'],3),flush=True)
    table=pd.DataFrame(results);assert len(table)==28 and table.successful_starts.gt(0).all()
    table.to_csv(OUT/'controlled_fits.csv',index=False)
    pd.DataFrame(profiles).to_csv(OUT/'depth_profiles.csv',index=False)
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    profiles=pd.DataFrame(profiles)
    for i,(_,eid,_) in enumerate(EVENTS):
        for j,model in enumerate(['linear','layered']):
            ax=axes[i,j]
            for variant,color in [('original',BLUE),('threshold_start','#009E73'),('official_exact_times',RED),('P_only','#CC79A7')]:
                p=profiles[profiles.event_id.eq(eid)&profiles.model.eq(model)&profiles.variant.eq(variant)]
                minimum=table[table.event_id.eq(eid)&table.model.eq(model)&table.variant.eq(variant)].refined_chi2.iloc[0]
                ax.plot(p.depth_km,p.chi2-minimum,label=variant.replace('_',' '),color=color)
            ax.set(title=f'{EVENTS[i][0]} — {model}',xlabel='Depth (km)',ylabel='Δχ² within each variant',xlim=(0,25))
            ax.set_yscale('symlog',linthresh=1);ax.set_ylim(bottom=0)
    axes[0,0].legend(frameon=False,fontsize=7)
    for ext in ['png','pdf']:fig.savefig(OUT/'figures'/f'controlled_depth_profiles.{ext}',dpi=180)
    plt.close(fig)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--stage',choices=['audit','fit','strong_motion'],required=True)
    args=ap.parse_args();OUT.mkdir(exist_ok=True);(OUT/'sources').mkdir(exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    gp,stations=inputs()
    if args.stage=='audit': plots(gp,stations,tables(gp,stations))
    elif args.stage=='fit': experiments(gp)
    else: strong_motion(gp)


if __name__=='__main__':main()
