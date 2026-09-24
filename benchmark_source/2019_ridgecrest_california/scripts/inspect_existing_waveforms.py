#!/usr/bin/env python3
"""Read-only comparison of the legacy Ridgecrest waveform directories and examples."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np
from obspy import read, UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_catalog_comparison import publication_style, save_figure, WIDTH_INCHES

CASE = Path(__file__).resolve().parents[1]
OUT = CASE/'analysis/figures/waveform_examples'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def signature(stream):
    return [(t.id, str(t.stats.starttime), t.stats.sampling_rate, t.stats.npts) for t in stream]


def stats(stream):
    gaps = stream.get_gaps()
    return dict(segments=len(stream), npts=sum(t.stats.npts for t in stream),
                start=str(min(t.stats.starttime for t in stream)),
                end=str(max(t.stats.endtime for t in stream)),
                sample_rates=sorted({t.stats.sampling_rate for t in stream}),
                zeros=sum(int(np.count_nonzero(t.data == 0)) for t in stream),
                gap_samples=sum(g[-1] for g in gaps if g[-1]>0),
                overlap_samples=-sum(g[-1] for g in gaps if g[-1]<0))


def same(a,b):
    return signature(a)==signature(b) and all(np.array_equal(x.data,y.data) for x,y in zip(a,b))


def file_key(station, channel, day):
    start=UTCDateTime(day);end=start+86400
    return f'{station}/{station}..{channel}__{start.strftime("%Y%m%dT%H%M%SZ")}__{end.strftime("%Y%m%dT%H%M%SZ")}.mseed'


def draw(ax, stream, origin, color, label, **kw):
    for i,tr in enumerate(stream):
        # Short excerpts only, no downsampling/filtering/normalization.
        t=tr.times()+float(tr.stats.starttime-origin)
        ax.plot(t,tr.data,color=color,lw=.65,label=label if i==0 else None,**kw)
    ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
    ax.set_ylabel('Counts')


def excerpt(base,folder,station,channel,day,start,end):
    return read(str(base/folder/file_key(station,channel,day)),starttime=start,endtime=end)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('data_root',type=Path)
    args=ap.parse_args();base=args.data_root.resolve()
    inventory={}
    for folder in ['waveforms_raw','waveforms']:
        inventory[folder]={str(p.relative_to(base/folder)):p.stat().st_size
                           for p in (base/folder).rglob('*.mseed')}
    a=inventory['waveforms'];r=inventory['waveforms_raw'];common=sorted(a.keys()&r.keys())
    added=sorted(a.keys()-r.keys());changed=[k for k in common if a[k]!=r[k]]
    report=dict(data_root=str(base),script_sha256=sha(Path(__file__)),
                scope='Full filename/size inventory; all added horizontal files compared against same-day processed Z; common-file content comparison is a stratified sample, not exhaustive.',
                folders={name:dict(files=len(v),bytes=sum(v.values()),stations=len({k.split('/')[0] for k in v}),
                         channels=dict(sorted(Counter(Path(k).name.split('__')[0].split('.')[-1] for k in v).items())),
                         nominal_start=min(k.split('__')[1] for k in v),nominal_end=max(k.split('__')[2].removesuffix('.mseed') for k in v)) for name,v in inventory.items()},
                common_files=len(common),same_size_files=len(common)-len(changed),changed_size_files=len(changed),
                only_raw=sorted(r.keys()-a.keys()),added_files=added,added_by_station=dict(Counter(k.split('/')[0] for k in added)),
                changed_size_by_station=dict(sorted(Counter(k.split('/')[0] for k in changed).items())))
    # All added files: compare full daily samples to the corresponding Z, preserving time/rate checks.
    copies=[]
    for k in added:
        station,filename=k.split('/');prefix,suffix=filename.split('__',1)
        z=station+'/'+prefix[:-1]+'Z__'+suffix
        x=read(str(base/'waveforms'/k));y=read(str(base/'waveforms'/z))
        samples_equal=len(x)==len(y) and all(np.array_equal(t.data,u.data) and t.stats.starttime==u.stats.starttime and t.stats.sampling_rate==u.stats.sampling_rate for t,u in zip(x,y))
        copies.append(dict(path=k,z_path=z,equals_z_samples_and_timing=samples_equal,sha256=sha(base/'waveforms'/k),z_sha256=sha(base/'waveforms'/z)))
        if len(copies)%22==0:print('Checked added files:',len(copies),flush=True)
    report['added_component_checks']=copies
    # One changed-size file per affected station; one equal-size file per network, plus plotted examples.
    selected={}
    for k in changed:selected.setdefault(('changed',k.split('/')[0]),k)
    for k in common:
        if a[k]==r[k]:selected.setdefault(('equal_size',k.split('.')[0]),k)
    for st,ch,day in [('CI.CCC','HHZ','2019-07-06'),('CI.MPM','HHZ','2019-07-06'),('CI.WBP','HHE','2019-07-12')]:
        selected[('explicit',st)]=file_key(st,ch,day)
    checks=[]
    for k in sorted(set(selected.values())):
        raw=read(str(base/'waveforms_raw'/k));work=read(str(base/'waveforms'/k))
        row=dict(path=k,raw=stats(raw),waveforms=stats(work),raw_sha256=sha(base/'waveforms_raw'/k),waveforms_sha256=sha(base/'waveforms'/k),same_samples_and_timing=same(raw,work))
        try:row['matches_raw_merge_fill_zero']=same(raw.copy().merge(method=0,fill_value=0),work)
        except Exception as e:row['merge_comparison_error']=type(e).__name__
        checks.append(row)
    report['common_file_sample']=checks
    print('Common file samples:',len(checks),flush=True)
    OUT.mkdir(parents=True,exist_ok=True)
    with publication_style():
        fig,axes=plt.subplots(3,2,figsize=(WIDTH_INCHES,6.4),layout='constrained')
        events=[('Mw 6.4',UTCDateTime('2019-07-04T17:33:49')),('Mw 7.1',UTCDateTime('2019-07-06T03:19:53.04'))]
        for col,(label,origin) in enumerate(events):
            for row,(station,ch) in enumerate([('CI.CCC','HHZ'),('CI.CLC','HHZ'),('PB.B918','EHZ')]):
                ax=axes[row,col];s=excerpt(base,'waveforms_raw',station,ch,str(origin.date),origin-20,origin+150)
                draw(ax,s,origin,'#0072B2',station);ax.axvline(0,color='k',ls=':',lw=.6)
                ax.set_title(f'{chr(97+row*2+col)}  {station} {ch} · {label}',loc='left');ax.set_xlim(-20,150)
                if row==2:ax.set_xlabel('Time since origin (s)')
        save_figure(fig,OUT/'01_raw_event_waveforms');plt.close(fig)
        fig,axes=plt.subplots(3,1,figsize=(WIDTH_INCHES,6.2),layout='constrained')
        cases=[('CI.CCC','HHZ','2019-07-06T03:19:53.04',-5,35),('CI.WBP','HHE','2019-07-12T03:58:45',0,75)]
        for ax,(station,ch,origin,lo,hi),title in zip(axes,cases,['a  Shared waveform','b  Gap handling']):
            t=UTCDateTime(origin)
            for folder,color,label,ls in [('waveforms','#D55E00','waveforms','-'),('waveforms_raw','#0072B2','waveforms_raw','--')]:
                s=excerpt(base,folder,station,ch,str(t.date),t+lo,t+hi)
                draw(ax,s,t,color,label,ls=ls)
            ax.set_title(f'{title} · {station} {ch}',loc='left');ax.set_xlim(lo,hi);ax.legend(loc='upper right')
            ax.set_xlabel(f'Seconds from {t.strftime("%Y-%m-%d %H:%M:%S")} UTC')
        ax=axes[2];t=UTCDateTime('2019-07-06T03:19:53.04')
        for ch,color,ls in [('EHZ','#34383C','-'),('EHN','#D55E00','--'),('EHE','#0072B2',':')]:
            s=excerpt(base,'waveforms','CI.WNM',ch,str(t.date),t-5,t+35)
            draw(ax,s,t,color,ch,ls=ls)
        ax.set_title('c  Added horizontal channels · CI.WNM',loc='left');ax.legend(loc='upper right');ax.set_xlim(-5,35);ax.set_xlabel('Time since Mw 7.1 origin (s)')
        save_figure(fig,OUT/'02_directory_comparison');plt.close(fig)
    # Plot inputs include excerpts not otherwise represented by the daily comparison sample.
    plot_paths=set()
    for _,origin in events:
        for st,ch in [('CI.CCC','HHZ'),('CI.CLC','HHZ'),('PB.B918','EHZ')]:plot_paths.add('waveforms_raw/'+file_key(st,ch,str(origin.date)))
    for st,ch,origin,_,_ in cases:
        for folder in ['waveforms_raw','waveforms']:plot_paths.add(folder+'/'+file_key(st,ch,str(UTCDateTime(origin).date)))
    for ch in ['EHZ','EHN','EHE']:plot_paths.add('waveforms/'+file_key('CI.WNM',ch,'2019-07-06'))
    report['plot_inputs']={k:sha(base/k) for k in sorted(plot_paths)}
    report['plot_conventions']='Native digital counts; no response removal, filtering, detrending or normalization. Raw gaps drawn as separate segments; dashed overlays distinguish coincident traces. UTC event origin marks are not phase picks.'
    report['figures']={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(OUT.glob('*')) if p.suffix in ['.png','.pdf']}
    (OUT/'waveform_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print('Added equals Z:',sum(x['equals_z_samples_and_timing'] for x in copies),'/',len(copies),flush=True)
    print('Zero merge matches:',sum(x.get('matches_raw_merge_fill_zero',False) for x in checks),'/',len(checks),flush=True)


if __name__=='__main__':
    main()
