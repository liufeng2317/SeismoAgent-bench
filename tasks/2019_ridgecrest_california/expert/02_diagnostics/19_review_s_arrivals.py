#!/usr/bin/env python3
"""Fixed 12-event visual S-arrival review at SRT/TOW2; no repicking or relocation."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, hashlib
import numpy as np
import pandas as pd
from obspy import read,Stream,UTCDateTime
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threadpool_limits(1)
HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'export/19_s_arrival_review'
ROOT=(HERE/'../../../data/2019_ridgecrest_california/data/waveforms').resolve()
STATIONS=['CI.SRT..HH','CI.TOW2..HH']


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def select():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
    source=HERE/'export/16_diagnose_systematics/pick_diagnostics.csv'
    p=pd.read_csv(source)
    focus=p[p.instrument_id.isin(STATIONS)].copy()
    counts=focus.groupby('event_id').apply(lambda g:len(set(zip(g.instrument_id,g.phase))),include_groups=False)
    eligible=counts[counts.eq(4)].index
    scores=focus[focus.event_id.isin(eligible)&focus.phase.eq('S')].groupby(['cohort','event_id']).linear_elevated_centered_s.mean().reset_index(name='mean_centered_s_residual_s')
    rows=[]
    for cohort,g in scores.groupby('cohort'):
        used=set()
        for category,target in [('small_residual',0.),('typical_residual',float(g.mean_centered_s_residual_s.median())),('large_positive_residual',None)]:
            q=g[~g.event_id.isin(used)].copy()
            q['selection_distance']=-q.mean_centered_s_residual_s if target is None else (q.mean_centered_s_residual_s-target).abs()
            chosen=q.sort_values(['selection_distance','event_id']).head(2)
            assert len(chosen)==2
            for row in chosen.to_dict('records'):
                row['category']=category;rows.append(row);used.add(row['event_id'])
    selection=pd.DataFrame(rows).sort_values(['cohort','category','event_id']).reset_index(drop=True)
    selection['review_number']=np.arange(1,13)
    assert len(selection)==12 and selection.event_id.is_unique
    frozen=dict(rule='Both stations have associated P and S. Per cohort select 2 closest to zero mean centered S residual, then 2 closest to cohort median, then 2 largest positive; no reuse; ties event_id. No waveform-based replacement.',window_s=[-12,8],detail_s=[-2.5,2.5],filter_hz=[1,12],padding_s=10,n_events=12,stations=STATIONS,source_sha256=sha(source))
    target=OUT/'selection.csv'
    if target.exists():assert target.read_text()==selection.to_csv(index=False),'Do not change fixed sample'
    else:selection.to_csv(target,index=False)
    (OUT/'design.json').write_text(json.dumps(frozen,indent=2)+'\n')
    return p,selection


def extract(job):
    number,eid,station,s_time,p_time=job
    anchor=UTCDateTime(s_time);start=anchor-22;end=anchor+18
    stream=Stream();sources=[]
    for path in sorted((ROOT/'data'/'.'.join(station.split('.')[:2])).glob(station+'?__*.mseed')):
        _,a,b=path.stem.split('__')
        if UTCDateTime(b)<=start or UTCDateTime(a)>=end:continue
        stream+=read(str(path),starttime=start,endtime=end)
        sources.append(dict(path=str(path.relative_to(ROOT)),bytes=path.stat().st_size))
    stream.merge(method=0,fill_value=None)
    traces=[]
    for comp in ['Z','N','E']:
        selected=stream.select(channel='HH'+comp)
        if len(selected)!=1:raise ValueError(f'{eid} {station}: missing/nonunique {comp}')
        tr=selected[0]
        if np.ma.isMaskedArray(tr.data) and np.ma.getmaskarray(tr.data).any():raise ValueError(f'{eid} {station}: gap')
        if tr.stats.starttime>start+.02 or tr.stats.endtime<end-.02:raise ValueError('Incomplete padding')
        raw=tr.copy().detrend('linear');filtered=raw.copy().taper(max_percentage=.05,max_length=1).filter('bandpass',freqmin=1,freqmax=12,corners=3,zerophase=True)
        t=raw.times(reftime=anchor);use=(t>=-12)&(t<=8)
        traces.append((comp,t[use],raw.data[use].astype(float),filtered.data[use].astype(float)))
    return dict(number=number,event_id=eid,instrument_id=station,s_time=s_time,p_relative_s=float(UTCDateTime(p_time)-anchor),traces=traces,sources=sources)


def main():
    if (OUT/'review.csv').exists():
        print('The fixed visual review is complete; preserve its figures and assessments. See export/19_s_arrival_review/README.md.')
        return
    p,selection=select()
    focus=p[p.event_id.isin(selection.event_id)&p.instrument_id.isin(STATIONS)]
    jobs=[]
    for r in selection.itertuples():
        for station in STATIONS:
            g=focus[focus.event_id.eq(r.event_id)&focus.instrument_id.eq(station)].set_index('phase')
            jobs.append((r.review_number,r.event_id,station,g.loc['S','time_utc'],g.loc['P','time_utc']))
    results=[];failures=[]
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[(job,pool.submit(extract,job)) for job in jobs]
        for job,f in futures:
            try:results.append(f.result())
            except Exception as exc:failures.append(dict(event_id=job[1],instrument_id=job[2],error=repr(exc)))
            print(f'[{len(results)+len(failures)}/24] windows; failures={len(failures)}',flush=True)
    pd.DataFrame(failures,columns=['event_id','instrument_id','error']).to_csv(OUT/'failures.csv',index=False)
    allp=pd.read_csv(HERE/'export/03_associate_gamma/full/picks.csv',keep_default_na=False)
    allp=allp[allp.instrument_id.isin(STATIONS)].copy()
    allp['epoch']=pd.to_datetime(allp.time_utc,utc=True,format='ISO8601').astype('int64')/1e9
    other=[];records=[];files={}
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    for r in selection.itertuples():
        fig,axes=plt.subplots(2,3,figsize=(12,4.7),layout='constrained')
        for row,station in enumerate(STATIONS):
            result=next((x for x in results if x['event_id']==r.event_id and x['instrument_id']==station),None)
            if result is None:
                for ax in axes[row]:ax.text(.5,.5,'Missing window',ha='center',transform=ax.transAxes)
                continue
            anchor=float(UTCDateTime(result['s_time']))
            q=allp[allp.instrument_id.eq(station)&allp.epoch.between(anchor-12,anchor+8)&~allp.event_id.eq(r.event_id)].copy()
            q['target_event_id']=r.event_id;q['relative_to_target_s_s']=q.epoch-anchor
            other.extend(q[['target_event_id','pick_id','event_id','instrument_id','phase','time_utc','probability','association_status','relative_to_target_s_s']].to_dict('records'))
            for f in result['sources']:files[f['path']]=f['bytes']
            for col,mode in enumerate(['raw','filtered','detail']):
                ax=axes[row,col]
                for j,(comp,t,raw,filt) in enumerate(result['traces']):
                    data=raw if mode=='raw' else filt
                    mask=(t>=(-2.5 if mode=='detail' else -12))&(t<=(2.5 if mode=='detail' else 8))
                    scale=max(float(np.max(np.abs(data[mask]))),1e-12)
                    ax.plot(t[mask],data[mask]/scale*.4+2-j,lw=.5,color='black')
                ax.axvline(0,color='#D65F24',lw=.9)
                if mode!='detail' or -2.5<=result['p_relative_s']<=2.5:ax.axvline(result['p_relative_s'],color='#2878B5',lw=.7,ls='--')
                for rr in q.itertuples():
                    if mode=='detail' and abs(rr.relative_to_target_s_s)>2.5:continue
                    ax.plot(rr.relative_to_target_s_s,2.55,marker='v' if rr.phase=='S' else '^',ms=3,color='#8B3FA8')
                ax.set_xlim((-2.5,2.5) if mode=='detail' else (-12,8));ax.set_ylim(-.55,2.7)
                ax.set_yticks([0,1,2],['E','N','Z']);ax.set_xlabel('Time from picked S (s)')
                if row==0:ax.set_title(['Detrended counts','1–12 Hz','1–12 Hz: S detail'][col])
                if col==0:ax.set_ylabel(station)
            records.append(dict(review_number=r.review_number,cohort=r.cohort,category=r.category,event_id=r.event_id,instrument_id=station,s_pick_utc=result['s_time'],p_relative_s=result['p_relative_s'],other_picks_in_window=len(q),figure=f'figures/{r.review_number:02d}_{r.event_id}.png'))
        fig.suptitle(f'{r.review_number:02d}  {r.event_id}  |  {r.cohort}',fontsize=10)
        for ext in ['png','pdf']:fig.savefig(OUT/f'figures/{r.review_number:02d}_{r.event_id}.{ext}',dpi=190)
        plt.close(fig)
    pd.DataFrame(records).to_csv(OUT/'windows.csv',index=False)
    pd.DataFrame(other).to_csv(OUT/'neighboring_picks.csv',index=False)
    (OUT/'waveform_sources.json').write_text(json.dumps(dict(files=[dict(path=k,bytes=v) for k,v in sorted(files.items())],root=str(ROOT)),indent=2)+'\n')
    (OUT/'README.md').write_text('''# Bounded SRT/TOW2 S-arrival review

Fixed 12 events, six per prior cohort, two stations, no sample expansion. Selection is frozen before waveform reading in selection.csv/design.json. Both P and S at both stations are required; this subset cannot measure catalog-wide errors. Failures stay visible and are not replaced.

Each event figure shows three native ENZ count components: detrended wide window, zero-phase 1–12 Hz wide window, and filtered ±2.5-s detail. Each trace/panel is independently normalized; amplitudes are not comparable across panels or components. No response correction is needed for this timing-only count inspection. Filtering is a display aid and may smear emergent onsets; raw views are retained. Orange line: existing target S pick. Blue dashed line: existing target P pick. Purple markers: other-event or unassociated picks, triangles up=P/down=S; these suggest possible interference, not proven event overlap. No theoretical S time or reference onset is plotted.

The task is to decide whether a clearly distinguishable onset precedes the target S pick systematically, whether another arrival competes, or whether onset identity remains ambiguous. Visible earlier energy alone is not proof of an earlier S phase. This is an assistant visual diagnostic, not expert manual truth annotation. No pick or catalog changes are authorized by the figure alone.

Reproduce from expert root: `python -u 02_diagnostics/19_review_s_arrivals.py`.
Use review.csv for the bounded visual assessment once completed. No repicking, relocation, model inversion or parameter search is run.
''')
    print(selection.to_string(index=False),flush=True)


if __name__=='__main__':main()
