#!/usr/bin/env python3
"""Bounded raw-count screening: one table and a few diagnostic windows, no labels."""
import csv
import json
import math
from pathlib import Path
import warnings

import numpy as np
from obspy import read, UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_catalog_comparison import publication_style, save_figure

CASE=Path(__file__).resolve().parents[2]
ROOT=CASE/'data/waveforms'
OUT=CASE/'analysis/figures/waveform_quality'


def metrics(blocks, rate):
    """10-s blocks; rank near-flat elevated 0.2-s bins and isolated increments."""
    center=blocks.mean(axis=1)
    span=np.ptp(blocks,axis=1)
    bins=blocks.reshape(len(blocks),50,int(round(.2*rate)))
    elevated=np.abs(bins.mean(axis=2)-center[:,None]) >= .25*span[:,None]
    flat=np.ptp(bins,axis=2) <= .03*span[:,None]
    plateau=np.mean(elevated & flat,axis=1)
    plateau[span==0]=0  # Exact constant runs were checked in the prior full scan.
    delta=np.diff(blocks,axis=1)
    rms=np.sqrt(np.mean(delta*delta,axis=1))
    jump=np.divide(np.max(np.abs(delta),axis=1),rms,out=np.zeros_like(rms),where=rms>0)
    return plateau,jump


def draw_examples(rows):
    examples=[]
    for kind in ['plateau','jump']:
        chosen=set()
        for r in sorted(rows,key=lambda r:r[kind+'_score'],reverse=True):
            station='.'.join(r['seed_id'].split('.')[:2])
            if station in chosen:continue
            examples.append((r['seed_id'],r[kind+'_path'],r[kind+'_start_utc'],kind))
            chosen.add(station)
            if len(chosen)==2:break
    for day,time,label in [('20190704','2019-07-04T17:33:59Z','Mw 6.4'),('20190706','2019-07-06T03:20:03.04Z','Mw 7.1'),('20190704','2019-07-04T12:00:00Z','Background')]:
        nextday={'20190704':'20190705','20190706':'20190707'}[day]
        examples.append(('CI.CCC..HHZ',f'data/CI.CCC/CI.CCC..HHZ__{day}T000000Z__{nextday}T000000Z.mseed',time,label))
    with publication_style():
        fig,axes=plt.subplots(4,2,figsize=(7.09,7.5),layout='constrained')
        for ax,(seed,path,time,kind) in zip(axes.flat,examples):
            t=UTCDateTime(time)
            st=read(str(ROOT/path),starttime=t,endtime=t+10).select(id=seed)
            if kind=='jump':
                # Center the plotted window on the increment, including both sides.
                strongest=max((tr for tr in st if len(tr)>1),key=lambda tr:np.max(np.abs(np.diff(tr.data.astype(float)))))
                at=int(np.argmax(np.abs(np.diff(strongest.data.astype(float)))))+1
                t=strongest.stats.starttime+at/strongest.stats.sampling_rate-5
                st=read(str(ROOT/path),starttime=t,endtime=t+10).select(id=seed)
            for tr in st:
                ax.plot(tr.times(reftime=t),tr.data,color='#0072B2',lw=.65)
            ax.set(title=f'{seed} · {kind}',xlabel=f'Seconds since {str(t)[5:19]} UTC',ylabel='Counts',xlim=(0,10))
            ax.ticklabel_format(axis='y',style='sci',scilimits=(-2,3))
        axes.flat[-1].set_visible(False)
        save_figure(fig,OUT/'05_shape_screening');plt.close(fig)


def main():
    index=json.loads((ROOT/'waveform_inventory.json').read_text())
    start=UTCDateTime(index['candidate']['start_utc']);end=UTCDateTime(index['candidate']['end_utc'])
    files=[r for r in index['files'] if r['in_candidate_window']]
    results={};warnings_seen=[];states=[]
    for i,record in enumerate(files,1):
        path=ROOT/record['path'];stat=path.stat();states.append((path,stat.st_size,stat.st_mtime_ns))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');stream=read(str(path),format='MSEED')
        warnings_seen.extend(str(w.message) for w in caught)
        # Join exactly adjacent compatible traces only, preserving gaps.
        stream.merge(method=-1)
        for tr in stream:
            rate=tr.stats.sampling_rate
            if rate!=100:raise ValueError('This case diagnostic expects the verified 100 Hz inputs')
            n=int(rate*10)
            lo=max(0,math.ceil((start-tr.stats.starttime)*rate-1e-7))
            hi=min(len(tr),math.ceil((end-tr.stats.starttime)*rate-1e-7))
            count=max(0,(hi-lo)//n)
            r=results.setdefault(tr.id,dict(seed_id=tr.id,windows=0,screened_samples=0,
                plateau_score=-1.,plateau_start_utc='',plateau_path='',jump_score=-1.,jump_start_utc='',jump_path=''))
            # Bound temporary-array memory even for a full-day contiguous trace.
            for offset in range(0,count,300):
                k=min(300,count-offset)
                blocks=tr.data[lo+offset*n:lo+(offset+k)*n].astype(float).reshape(k,n)
                if not np.isfinite(blocks).all():raise ValueError(f'Nonfinite input {tr.id}')
                p,j=metrics(blocks,rate)
                r['windows']+=k;r['screened_samples']+=blocks.size
                for name,values in [('plateau',p),('jump',j)]:
                    at=int(np.argmax(values))
                    if float(values[at])>r[name+'_score']:
                        r[name+'_score']=float(values[at]);r[name+'_path']=record['path']
                        r[name+'_start_utc']=str(tr.stats.starttime+(lo+(offset+at)*n)/rate)
        if i%30==0 or i==len(files):print(f'Shape screening {i}/{len(files)} files',flush=True)
    for path,size,mtime in states:
        st=path.stat()
        if (size,mtime)!=(st.st_size,st.st_mtime_ns):raise RuntimeError('Input changed during scan')
    rows=sorted(results.values(),key=lambda r:r['seed_id'])
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'shape_screening.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    draw_examples(rows)
    covered=sum(r['screened_samples'] for r in rows)
    note=f'''# Minimal raw-waveform shape screening

Internal source diagnostic only; not ground-truth labels and not intended as agent input.

Scanned {len(files)} files / {len(rows)} channels in [{start}, {end}). Scored {sum(r['windows'] for r in rows):,} contiguous non-overlapping 10-second windows ({covered:,} samples). Short tails and fragments under 10 s are omitted; prior full-sample integrity checks still apply. No response removal, filtering, resampling, padding, repair or raw-file writes. Decode warnings: {len(warnings_seen)}.

[Seven diagnostic windows](05_shape_screening.png) ([PDF](05_shape_screening.pdf)) and [one row per channel](shape_screening.csv). The table retains only each channel's strongest candidate for each statistic, with exact source path and time; it is not an exhaustive anomaly inventory.

- Plateau score: fraction of 0.2-s bins whose range is at most 3% of the containing 10-s range and whose mean is at least 25% of that range away from the 10-s mean. Constant windows score zero because prior QC checks exact constant runs. This detects approximate elevated platforms, but pulses, steps and genuine signal shapes can also score highly.
- Jump score: largest absolute sample increment divided by RMS increment within the same 10 s. It ranks isolated changes, including legitimate sharp arrivals; it is not a timing-error or corruption verdict.
- These dimensionless scores rank within-channel morphology. No universal pass/fail threshold or cross-instrument physical-amplitude comparison is used. Scores depend on window alignment and do not prove absence of saturation.
- The figure takes the two highest-ranked distinct stations per metric, plus fixed CI.CCC..HHZ windows for both large earthquakes and a background comparison. The background window is a comparison, not a certified noise-only interval. Jump plots are centered on the strongest increment (CSV times remain the original scoring-window starts). Axes use independent raw-count scales.

This bounded screen is sufficient for a first source review. Keep the established gap and saturation concerns available internally; do not delete stations or synthesize labels from these scores. Further processing choices remain part of the agent task.
'''
    (OUT/'shape_screening.md').write_text(note)
    print('Wrote shape_screening.csv, shape_screening.md and 05_shape_screening PNG/PDF',flush=True)


if __name__=='__main__':main()
