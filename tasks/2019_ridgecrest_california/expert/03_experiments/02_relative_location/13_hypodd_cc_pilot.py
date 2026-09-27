#!/usr/bin/env python3
"""Native hypoDD catalog / catalog+CC experiment on the fixed stage12 cohort."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from obspy import read, UTCDateTime
from pyproj import CRS, Transformer
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

threadpool_limits(1)
HERE = Path(__file__).resolve().parents[2]  # Expert root; independent of working directory.
OUT=HERE/'export/13_hypodd_cc_pilot'
PRE=HERE/'export/12_relative_location_pilot'
LIB=Path('/liufeng1afs/project/03_LLM/Science_Discovery_Agenet/TRACE-1.1/seismoagent/library/basic_fun/HypoDD')
WAVE=HERE.parents[2]/'benchmark_source/2019_ridgecrest_california/data/waveforms'
TOP=[0.,1.,2.,3.,4.,5.,6.,7.,8.,30.]
VP=[4.74,5.01,5.35,5.71,6.07,6.17,6.27,6.34,6.39,7.8]
CONFIG=dict(sample_rate_hz=100,bands_hz=[[2,8],[2,12]],cc_min=.75,snr_min=2.,
            peak_margin_min=.08,peak_exclusion_s=.08,band_lag_tolerance_s=.02,
            horizontal_lag_tolerance_s=.03,P_window_s=[-.2,1.],S_window_s=[-.3,1.5],
            P_lag_limit_s=.3,S_lag_limit_s=.4,velocity_tops_km=TOP,vp_km_s=VP,vp_vs=1.73,
            native_iterations=[4,8],damping=[80,40],workers=4)


def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def build():
    dest=OUT/'native';dest.mkdir(parents=True,exist_ok=True)
    source=LIB/'hypodd_source'
    for part in ['include','src/hypoDD']:
        shutil.copytree(source/part,dest/part,dirs_exist_ok=True)
    # Change array capacities only; retain all scientific routines verbatim.
    (dest/'include/hypoDD.inc').write_text('''      integer*4 MAXEVE, MAXLAY, MAXDATA, MAXSTA, MAXEVE0,
     & MAXDATA0, MAXCL
      parameter(MAXEVE=200, MAXLAY=15, MAXDATA=50000,
     & MAXSTA=100, MAXEVE0=2, MAXDATA0=1, MAXCL=100)
''')
    cwd=dest/'src/hypoDD'
    with (dest/'build.log').open('w') as log:
        subprocess.run(['make','-j4','FC=gfortran','FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch'],cwd=cwd,stdout=log,stderr=subprocess.STDOUT,check=True)
    # Independent evaluator calls the SAME native ray tracer and geodesy routine.
    driver=dest/'evaluate.f90'
    driver.write_text('''program evaluate
implicit none
integer n,k,nl,j
real tops(15),v(15),z,tt,ain,dist,az,del,ratio
real vs(15)
double precision lat,lon
real slat,slon
read(*,*) nl,ratio
read(*,*) tops(1:nl)
read(*,*) v(1:nl)
vs=v/ratio
read(*,*) n
do k=1,n
 read(*,*) lat,lon,z,slat,slon,j
 call delaz2(lat,lon,slat,slon,del,dist,az)
 if(j.eq.1) then
  call ttime(dist,z,nl,v,tops,tt,ain)
 else
  call ttime(dist,z,nl,vs,tops,tt,ain)
 endif
 write(*,'(F16.8)') tt
enddo
end program
''')
    objs=['ttime','direct1','refract','tiddid','delaz2','vmodel']
    subprocess.run(['gfortran','-O2',str(driver),*[str(cwd/(v+'.o')) for v in objs],'-o',str(dest/'evaluate')],check=True)
    check=subprocess.run([str(dest/'evaluate')],input='2 1.73\n0 1\n5 6\n2\n35.75 -117.55 0.5 35.75 -117.55 1\n35.75 -117.55 0.5 35.75 -117.55 2\n',text=True,capture_output=True,check=True)
    numerical=np.fromstring(check.stdout,sep=' ')
    assert np.allclose(numerical,[.1,.173],atol=1e-5,rtol=0)
    (dest/'numerical_checks.json').write_text(json.dumps(dict(vertical_P_s=float(numerical[0]),vertical_S_s=float(numerical[1]),expected=[.1,.173]),indent=2)+'\n')
    return cwd/'hypoDD'


def extract_file(job):
    path,rows=job
    stream=read(str(WAVE/path)); result={}; audit=[]
    for row in rows:
        pid,seed,phase,time=row
        t=UTCDateTime(pd.Timestamp(time).isoformat())
        # Keep source gaps; require one contiguous trace spanning padded window.
        pieces=stream.select(id=seed).slice(t-10,t+10).copy()
        pieces.merge(method=-1)
        valid=[tr for tr in pieces if tr.stats.starttime<=t-9.9 and tr.stats.endtime>=t+9.9 and not np.ma.isMaskedArray(tr.data)]
        if len(valid)!=1:
            audit.append(dict(pick_id=pid,seed_id=seed,path=path,status='gap_or_missing'));continue
        tr=valid[0];fs=float(tr.stats.sampling_rate)
        if fs<50 or not np.isfinite(tr.data).all():
            audit.append(dict(pick_id=pid,seed_id=seed,path=path,status='invalid_samples'));continue
        arrays=[];snrs=[]
        begin,end=CONFIG[phase+'_window_s']; ts=np.arange(round(begin*100),round(end*100)+1)/100
        for lo,hi in CONFIG['bands_hz']:
            f=tr.copy().detrend('linear').taper(.05).filter('bandpass',freqmin=lo,freqmax=hi,corners=3,zerophase=True)
            x=np.arange(len(f.data))/fs+float(f.stats.starttime-t)
            signal=np.interp(ts,x,f.data)
            noise=np.interp(np.arange(-500,-100)/100,x,f.data)
            snrs.append(float(np.sqrt(np.mean(signal**2))/max(np.sqrt(np.mean(noise**2)),1e-20)))
            arrays.append(signal.astype('float32'))
        # Same raw channel is compared between events; no response removal/rotation.
        result[pid+'|'+seed]=np.stack(arrays)
        audit.append(dict(pick_id=pid,seed_id=seed,path=path,status='ok',snr_primary=snrs[0],snr_check=snrs[1],sample_rate_hz=fs))
    return result,audit


def prepare_cc():
    p=pd.read_csv(PRE/'picks.csv');edges=pd.read_csv(PRE/'differential_times.csv')
    index=pd.read_csv(HERE/'export/01_prepare_inputs/full/waveform_inputs.csv')
    files={}
    for r in index.itertuples():
        day=Path(r.path).name.split('__')[1][:8]
        files[(r.seed_id,day)]=r.path
    jobs={}
    for r in p.itertuples():
        t=pd.Timestamp(r.time_utc)
        assert pd.Timestamp('2019-07-04T00:00:10Z')<=t<pd.Timestamp('2019-07-06T23:59:50Z')
        for seed in r.source_channels.split(';'):
            if (r.phase=='P') != seed.endswith('Z'):continue
            path=files.get((seed,t.strftime('%Y%m%d')))
            if path: jobs.setdefault(path,[]).append((r.pick_id,seed,r.phase,r.time_utc))
    cache={};audit=[]
    with ThreadPoolExecutor(max_workers=CONFIG['workers']) as pool:
        pending=[pool.submit(extract_file,j) for j in sorted(jobs.items())]
        for done,future in enumerate(as_completed(pending),1):
            data,rows=future.result();cache.update(data);audit.extend(rows)
            if done%20==0 or done==len(pending):print(f'Waveforms: {done}/{len(pending)} files',flush=True)
    np.savez_compressed(OUT/'cc_windows.npz',**cache)
    audit=pd.DataFrame(audit);audit.to_csv(OUT/'waveform_windows.csv',index=False)
    core=load_module('old_cc_core',LIB/'backup/hypodd_autocc/cc_auto/xcorr_core.py')
    # Known-delay check: b has its pulse 0.07 s later than a within pick-aligned windows.
    t=np.arange(121)/100
    aa=np.exp(-((t-.4)/.05)**2)*np.cos(2*np.pi*6*(t-.4))
    bb=np.exp(-((t-.47)/.05)**2)*np.cos(2*np.pi*6*(t-.47))
    lags,curve=core.normalized_cc_curve(aa,bb,30)
    lag=float(lags[np.argmax(curve)])/100
    assert abs(lag-.07)<.0001
    # Example catalog travel times 10 and 8 s => true differential 2 - .07.
    assert abs((10.-8.-lag)-1.93)<1e-10
    meta={(r.pick_id,r.seed_id):r for r in audit.itertuples()}
    pr=p.set_index('pick_id');records=[];components=[]
    for rownum,r in enumerate(edges.itertuples()):
        pa,pb=pr.loc[r.pick_id_a],pr.loc[r.pick_id_b]
        seeds=sorted(set(pa.source_channels.split(';'))&set(pb.source_channels.split(';')))
        seeds=[s for s in seeds if (r.phase=='P')==s.endswith('Z')]
        comps=[]
        for seed in seeds:
            qa,qb=meta.get((r.pick_id_a,seed)),meta.get((r.pick_id_b,seed))
            cr=dict(edge_index=rownum,seed_id=seed,status='missing_window')
            if qa is None or qb is None or qa.status!='ok' or qb.status!='ok':components.append(cr);continue
            ma=cache[r.pick_id_a+'|'+seed];mb=cache[r.pick_id_b+'|'+seed]
            snr=min(qa.snr_primary,qa.snr_check,qb.snr_primary,qb.snr_check)
            limit=round(CONFIG[r.phase+'_lag_limit_s']*100)
            ls=[];peaks=[];margins=[];at_boundary=False
            for a,b in zip(ma,mb):
                lags,curve=core.normalized_cc_curve(a,b,limit)
                best=int(np.nanargmax(np.abs(curve)))
                # Reject reversed polarity rather than accepting |CC| silently.
                peaks.append(float(curve[best]));ls.append(float(lags[best])/100)
                other=curve[np.abs(lags-lags[best])>8]
                margins.append(float(curve[best]-np.max(np.abs(other))))
                at_boundary |= abs(lags[best])>=limit-1
            reasons=[]
            if snr<2:reasons.append('low_snr')
            if min(peaks)<.75:reasons.append('low_or_negative_cc')
            if min(margins)<.08:reasons.append('ambiguous_peak')
            if at_boundary:reasons.append('lag_boundary')
            if abs(ls[0]-ls[1])>.020001:reasons.append('band_instability')
            cr.update(status=';'.join(reasons) or 'accepted',snr=snr,cc=peaks[0],cc_check=peaks[1],lag_s=ls[0],check_lag_s=ls[1],peak_margin=min(margins))
            components.append(cr);comps.append(cr)
        expected=1 if r.phase=='P' else 2
        good=[c for c in comps if c['status']=='accepted']
        ok=len(good)==expected and len(seeds)==expected
        reason='accepted' if ok else 'component_quality'
        if ok and r.phase=='S' and abs(good[0]['lag_s']-good[1]['lag_s'])>.030001:ok=False;reason='horizontal_disagreement'
        lag=float(np.mean([c['lag_s'] for c in good])) if ok else np.nan
        records.append(dict(edge_index=rownum,accepted=ok,reason=reason,lag_s=lag,cc=min([c['cc'] for c in good]) if ok else np.nan))
        if (rownum+1)%3000==0:print(f'CC: {rownum+1}/{len(edges)} observations',flush=True)
    result=edges.join(pd.DataFrame(records).drop(columns='edge_index'))
    result['cc_arrival_difference_s']=result.observed_dt_s-result.lag_s
    result.to_csv(OUT/'cc_measurements.csv',index=False)
    pd.DataFrame(components).to_csv(OUT/'cc_components.csv',index=False)
    (OUT/'cc_checks.json').write_text(json.dumps(dict(known_lag_s=.07,synthetic_travel_time_difference_s=1.93,settings=CONFIG,legacy_issue='Old cc_auto/build_dt_cc.py writes only pick-window lag. Here dt.cc uses catalog travel-time difference minus measured lag; OTC=0.'),indent=2)+'\n')
    print(f'Accepted CC: {result.accepted.sum()} / {len(result)}; training: {(result.accepted & result.training).sum()}',flush=True)


def inputs():
    events=pd.read_csv(PRE/'events.csv').sort_values('event_id').reset_index(drop=True)
    events['native_id']=np.arange(1,len(events)+1)
    # HypoDD event.dat represents origin times at 0.01-s resolution.
    events['native_origin']=pd.to_datetime(events.origin_time,utc=True,format='ISO8601').dt.round('10ms')
    events.to_csv(OUT/'event_mapping.csv',index=False)
    picks=pd.read_csv(PRE/'picks.csv').set_index('pick_id')
    stations=pd.read_csv(HERE/'export/04_locate_nonlinloc/stations.csv').set_index('id')
    cc=pd.read_csv(OUT/'cc_measurements.csv')
    return events,picks,stations,cc


def run_native(binary):
    events,picks,stations,cc=inputs();ev=events.set_index('event_id')
    writer=load_module('native_cc_writer',LIB/'hypodd_runner/mk_cc.py')
    held=json.loads((PRE/'run.json').read_text())['held_out_stations']
    for variant in ['catalog_only','catalog_cc']:
        run=OUT/variant;run.mkdir(exist_ok=True)
        with (run/'event.dat').open('w') as f:
            for r in events.itertuples():
                t=r.native_origin
                stamp=t.strftime('%H%M%S')+f'{t.microsecond//10000:02d}'
                f.write(f'{t:%Y%m%d} {stamp} {r.latitude:.7f} {r.longitude:.7f} {r.depth_km:.5f} 0.0 0.0 0.0 0.0 {r.native_id}\n')
        with (run/'station.dat').open('w') as f:
            for s,r in stations.iterrows():
                f.write(f'{r.nll_station} {r.latitude:.7f} {r.longitude:.7f}\n')
        with (run/'dt.ct').open('w') as f:
            for (ea,eb),group in cc[cc.training].groupby(['event_id_a','event_id_b'],sort=True):
                f.write(f'# {ev.loc[ea,"native_id"]} {ev.loc[eb,"native_id"]}\n')
                for r in group.itertuples():
                    ta=(pd.Timestamp(picks.loc[r.pick_id_a,'time_utc'])-ev.loc[ea,'native_origin']).total_seconds()
                    tb=(pd.Timestamp(picks.loc[r.pick_id_b,'time_utc'])-ev.loc[eb,'native_origin']).total_seconds()
                    f.write(f'{stations.loc[r.instrument_id,"nll_station"]} {ta:.6f} {tb:.6f} 1.0 {r.phase}\n')
        blocks=[]
        for (ea,eb),group in cc[cc.training & cc.accepted].groupby(['event_id_a','event_id_b'],sort=True):
            od=(ev.loc[ea,'native_origin']-ev.loc[eb,'native_origin']).total_seconds()
            rows=[(stations.loc[r.instrument_id,'nll_station'],r.cc_arrival_difference_s-od,float(r.cc**2),r.phase) for r in group.itertuples()]
            blocks.append(dict(cusp1=int(ev.loc[ea,'native_id']),cusp2=int(ev.loc[eb,'native_id']),otc=0.,rows=rows))
        writer.write_dt_cc(str(run/'dt.cc'),blocks)
        assert blocks and cc.loc[cc.training,'instrument_id'].isin(held).sum()==0
        use=variant=='catalog_cc'
        # Same CT rows, weights, damping, model, initial locations, and iteration count.
        # CC is active from the start; nonpositive early weights can delete CC rows.
        text='\n'.join(['dt.cc','dt.ct','event.dat','station.dat','hypoDD.loc','hypoDD.reloc','hypoDD.sta','hypoDD.res','hypoDD.src',f'{3 if use else 2} 3 200','0 0','2 2 2',f'4 {1 if use else -9} {.5 if use else -9} -9 -9 1 .5 -9 -9 80',f'8 {1 if use else -9} {.5 if use else -9} -9 -9 1 .5 -9 -9 40','10 1.73',' '.join(map(str,TOP)),' '.join(map(str,VP)),'0',''])
        (run/'hypoDD.inp').write_text(text)
        with (run/'console.log').open('w') as log:
            subprocess.run([str(binary),'hypoDD.inp'],cwd=run,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
        if not (run/'hypoDD.reloc').exists() or (run/'hypoDD.reloc').stat().st_size==0:raise RuntimeError(f'No native relocations: {run}')
        res=pd.read_csv(run/'hypoDD.res',sep=r'\s+',skiprows=1,header=None)
        if use:
            if not ((res[4].isin([1,2])) & (res[7]>0)).any():
                raise RuntimeError('CC rows were not retained with positive weight')
        print(f'{variant}: {len(res)} retained observations; native output available',flush=True)


def evaluate_native(locations,picks,stations):
    rows=[];ids=[]
    for r in picks.itertuples():
        if r.event_id not in locations.index:continue
        e=locations.loc[r.event_id];s=stations.loc[r.instrument_id]
        rows.append(f'{e.latitude:.8f} {e.longitude:.8f} {e.depth_km:.6f} {s.latitude:.8f} {s.longitude:.8f} {1 if r.phase=="P" else 2}')
        ids.append(r.Index)
    txt=f'10 1.73\n'+ ' '.join(map(str,TOP))+'\n'+' '.join(map(str,VP))+f'\n{len(rows)}\n'+'\n'.join(rows)+'\n'
    result=subprocess.run([str(OUT/'native/evaluate')],input=txt,text=True,capture_output=True,check=True)
    times=np.array([float(v) for v in result.stdout.split()])
    assert len(times)==len(rows)
    origins=pd.to_datetime(locations.loc[picks.loc[ids,'event_id'],'origin_time'],utc=True,format='ISO8601').astype('int64').to_numpy()/1e9
    return pd.Series(times+origins,index=ids)


def report():
    events,picks,stations,cc=inputs();base=events.copy().set_index('event_id')
    # Evaluate baseline in the native model, not stage12's different grid model.
    base['origin_time']=base.native_origin.astype(str)
    solutions={'baseline':base[['latitude','longitude','depth_km','origin_time']].copy()}
    for variant in ['catalog_only','catalog_cc']:
        frame=pd.read_csv(OUT/variant/'hypoDD.reloc',sep=r'\s+',header=None)
        frame.columns=['native_id','latitude','longitude','depth_km','x_m','y_m','z_m','ex_m','ey_m','ez_m','year','month','day','hour','minute','second','magnitude_placeholder','nccp','nccs','nctp','ncts','rmscc','rmsct','cluster']
        frame['origin_time']=[(pd.Timestamp(year=int(r.year),month=int(r.month),day=int(r.day),hour=int(r.hour),minute=int(r.minute),tz='UTC')+pd.Timedelta(seconds=float(r.second))).isoformat() for r in frame.itertuples()]
        frame=frame.merge(events[['event_id','native_id']],on='native_id',validate='one_to_one').set_index('event_id')
        frame.to_csv(OUT/(variant+'_events.csv'));solutions[variant]=frame
    common=sorted(set.intersection(*[set(f.index) for f in solutions.values()]))
    membership=events[['event_id','native_id','period']].copy()
    for name,frame in solutions.items():
        membership[name+'_retained']=membership.event_id.isin(frame.index)
        if name!='baseline':
            log=(OUT/name/'hypoDD.log').read_text(errors='replace')
            negative=set(map(int,re.findall(r'negative depth -\s+(\d+)',log)))
            membership[name+'_negative_depth_rejection']=membership.native_id.isin(negative)
            assert set(membership.loc[~membership[name+'_retained'],'native_id'])==negative
    membership['common_comparison']=membership.event_id.isin(common);membership.to_csv(OUT/'cohort.csv',index=False)
    use=cc.event_id_a.isin(common)&cc.event_id_b.isin(common)
    pairs=cc[use].copy();metrics=[]
    for name,frame in solutions.items():
        pred=evaluate_native(frame,picks,stations)
        diff=pairs.pick_id_a.map(pred)-pairs.pick_id_b.map(pred)
        pairs[name+'_ct_residual_s']=pairs.observed_dt_s-diff
        pairs[name+'_cc_residual_s']=pairs.cc_arrival_difference_s-diff
        for data in ['ct','cc']:
            for train in [True,False]:
                mask=pairs.training.eq(train)&(pairs.accepted if data=='cc' else True)
                residual=pairs.loc[mask,name+'_'+data+'_residual_s']
                metrics.append(dict(variant=name,data=data,split='training' if train else 'held_out_stations',n=len(residual),rms_s=float(np.sqrt(np.mean(residual**2))),median_abs_s=float(residual.abs().median())))
    pairs.to_csv(OUT/'validation_pairs.csv',index=False)
    metrics=pd.DataFrame(metrics);metrics.to_csv(OUT/'metrics.csv',index=False)
    matched=pd.read_csv(PRE/'reference_comparison.csv');matched=matched[matched.event_id.isin(common)].copy()
    projection=CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km')
    project=Transformer.from_crs(4326,projection,always_xy=True)
    rx,ry=project.transform(matched.longitude_ref.to_numpy(),matched.latitude_ref.to_numpy())
    locations=[]
    for name,frame in solutions.items():
        loc=frame.loc[common].copy();loc['variant']=name
        loc['x_km'],loc['y_km']=project.transform(loc.longitude.to_numpy(),loc.latitude.to_numpy());locations.append(loc)
        xs,ys=project.transform(frame.loc[matched.event_id,'longitude'].to_numpy(),frame.loc[matched.event_id,'latitude'].to_numpy())
        matched[name+'_native_horizontal_km']=np.hypot(xs-rx,ys-ry)
        matched[name+'_native_depth_difference_km']=np.where(matched.catalog.eq('Shelly'),frame.loc[matched.event_id,'depth_km'].to_numpy()-matched.reference_depth_km,np.nan)
    matched.to_csv(OUT/'reference_comparison.csv',index=False)
    long=pd.concat(locations).reset_index();long.to_csv(OUT/'common_events.csv',index=False)
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(11,7),layout='constrained')
    xmin,xmax=long.x_km.min()-.3,long.x_km.max()+.3;ymin,ymax=long.y_km.min()-.3,long.y_km.max()+.3
    zmax=long.depth_km.max()+.3
    for col,(name,title) in enumerate([('baseline','NonLinLoc input'),('catalog_only','hypoDD: catalog'),('catalog_cc','hypoDD: catalog + CC')]):
        frame=long[long.variant.eq(name)].merge(events[['event_id','period']],on='event_id')
        for period,color in [('between_mainshocks','tab:blue'),('after_M7.1','tab:orange')]:
            group=frame[frame.period.eq(period)]
            axes[0,col].scatter(group.x_km,group.y_km,s=9,color=color,label=period.replace('_',' '))
            axes[1,col].scatter(group.x_km,group.depth_km,s=9,color=color)
        axes[0,col].set(title=title,xlim=(xmin,xmax),ylim=(ymin,ymax),xlabel='East (km)',ylabel='North (km)',aspect='equal')
        axes[1,col].set(xlim=(xmin,xmax),ylim=(zmax,0),xlabel='East (km)',ylabel='Depth (km)',aspect='equal')
    axes[0,0].legend(frameon=False,fontsize=8)
    fig.savefig(OUT/'01_hypodd_comparison.png',dpi=220);fig.savefig(OUT/'01_hypodd_comparison.pdf');plt.close(fig)
    cache=np.load(OUT/'cc_windows.npz');comp=pd.read_csv(OUT/'cc_components.csv')
    fig,axes=plt.subplots(3,2,figsize=(9,6),layout='constrained')
    # Deterministic representative quality tiers, not only the largest CC peaks.
    accepted=cc[cc.accepted].sort_values(['cc','edge_index']) if 'edge_index' in cc else cc[cc.accepted].sort_values('cc')
    choices=[accepted.iloc[int(q*(len(accepted)-1))] for q in [.1,.5,.9]]
    for row,r in enumerate(choices):
        edgeidx=int(r.name);seed=comp[(comp.edge_index==edgeidx)&comp.status.eq('accepted')].iloc[0].seed_id
        a,b=cache[r.pick_id_a+'|'+seed][0],cache[r.pick_id_b+'|'+seed][0]
        t=np.arange(len(a))/100+CONFIG[r.phase+'_window_s'][0]
        a=a/np.max(np.abs(a));b=b/np.max(np.abs(b))
        for col in range(2):
            axes[row,col].plot(t,a,color='black',lw=.8,label='Event A')
            axes[row,col].plot(t-(r.lag_s if col else 0),b,color='tab:blue',lw=.8,label='Event B')
            axes[row,col].set(xlabel='Time from pick (s)',ylabel='Normalized counts',title=('CC-aligned' if col else 'Pick-aligned')+f' | {seed} {r.phase}')
        for col in range(2): axes[row,col].text(.01,.97,chr(97+row*2+col),transform=axes[row,col].transAxes,va='top',fontweight='bold')
    axes[0,0].legend(frameon=False,fontsize=8)
    fig.savefig(OUT/'02_cc_alignment.png',dpi=220);fig.savefig(OUT/'02_cc_alignment.pdf');plt.close(fig)
    summary=dict(settings=CONFIG,retained={k:len(v) for k,v in solutions.items()},common_events=len(common),cc_total=int(cc.accepted.sum()),cc_training=int((cc.accepted&cc.training).sum()),cc_held_out=int((cc.accepted&~cc.training).sum()),cc_by_phase=cc[cc.accepted].groupby('phase').size().to_dict(),held_out_stations=json.loads((PRE/'run.json').read_text())['held_out_stations'])
    sources=[OUT/'native/src/hypoDD/hypoDD',OUT/'native/evaluate',OUT/'native/evaluate.f90',OUT/'native/include/hypoDD.inc',Path(__file__),PRE/'run.json',PRE/'events.csv',PRE/'picks.csv',PRE/'differential_times.csv',LIB/'hypodd_runner/mk_cc.py',LIB/'backup/hypodd_autocc/cc_auto/xcorr_core.py']+sorted((LIB/'hypodd_source/src/hypoDD').glob('*.f'))
    training_cc=cc[cc.training & cc.accepted]
    summary['training_cc_supported_events']=len(set(training_cc.event_id_a)|set(training_cc.event_id_b))
    summary['training_cc_event_pairs']=len(training_cc[['event_id_a','event_id_b']].drop_duplicates())
    summary['waveform_root']=str(WAVE.resolve())
    station_metrics=[]
    for station,group in pairs[~pairs.training].groupby('instrument_id'):
        for kind in ['ct','cc']:
            sub=group[group.accepted] if kind=='cc' else group
            if not len(sub):continue
            for variant in solutions:
                residual=sub[variant+'_'+kind+'_residual_s']
                station_metrics.append(dict(instrument_id=station,data=kind,variant=variant,n=len(sub),rms_s=float(np.sqrt(np.mean(residual**2)))))
    pd.DataFrame(station_metrics).to_csv(OUT/'held_out_station_metrics.csv',index=False)
    summary['source_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}
    (OUT/'run.json').write_text(json.dumps(summary,indent=2)+'\n')
    refsummary=matched.groupby('catalog')[[k+'_native_horizontal_km' for k in solutions]].median()
    depths=matched.loc[matched.catalog.eq('Shelly'),[k+'_native_depth_difference_km' for k in solutions]].abs().median()
    (OUT/'README.md').write_text(f'''# Native hypoDD catalog / CC pilot

Run `python -u 03_experiments/02_relative_location/13_hypodd_cc_pilot.py --stage all` in seismoagent.
Stages `cc`, `locate`, and `report` can also run separately. No expert-v1 outputs
or waveform files are modified. The starting cohort is the same 144 stage12 events.

## Implementation and controls

Use the existing local hypoDD Fortran source, `hypodd_runner/mk_cc.py` writer and
backup `cc_auto/xcorr_core.py` correlation curve. Build in this export directory;
only array capacities are changed. `native/build.log` records compilation.
Direct input writing preserves stage12 event-pair and withheld-station assignments;
ph2dt is not rerun, avoiding a change in the pair population. This pilot does not
run FDTCC; its travel-time-assisted candidate generation is a separate experiment.

Both native variants use the original Shelly layer-top CONSTANT interpretation,
Vp/Vs=1.73, the same inputs and 12 LSQR iterations. Stations lie on the common
nominal surface (0.7 km above sea level); this native version does not read elevation.
Thus comparisons between the two native variants isolate added CC; comparisons to
NonLinLoc or stage12 also include forward-model/elevation differences.
Catalog weights are identical in both variants. The CC variant adds positive
CC weights from the first iteration (P=1, S=0.5, quality=CC²). Nonpositive early
CC weights are avoided because this native code can remove those rows permanently.
Damping is 80 then 40. No residual or pair-distance reweighting is applied.
Input origins are rounded to native 0.01-s precision; output origins have the same
limitation. Placeholder event magnitudes are zero and must not be used scientifically.
Native negative-depth rejection/retention is reported, never silently imputed.

## CC measurements

Same raw channel between events; P uses Z, S requires both native horizontals.
P window [-0.2,1.0] s; S [-0.3,1.5] s, with 10-s filter padding. No gap filling.
Bandpass 2--8 Hz, check band 2--12 Hz; sample on a 100-Hz pick-relative grid.
Require RMS signal/noise >=2 in both bands and events, positive CC>=0.75,
peak margin >=0.08 outside +/-0.08 s, interior lag peak, band lag agreement <=0.02 s;
S horizontal lag agreement <=0.03 s. Lag limits are 0.3/0.4 s for P/S.
Noise [-5,-1] s may contain coda; this criterion is conservative, not proof of purity.
The inherited curve uses full-window normalization, not overlap renormalization.
No polarity reversal or instrument-response correction is applied.

**Time convention checked with a synthetic delayed pulse:** if B's waveform is
0.07 s later relative to its pick, dt.cc = (pickA-originA) - (pickB-originB) - 0.07.
OTC=0. The backup wrapper writes window lag alone; that wrapper is not used here.
CC is quantized at 0.01 s (S uses the mean of two accepted horizontal lags).

Accepted CC: {summary['cc_total']} ({summary['cc_training']} training,
{summary['cc_held_out']} withheld); phases: {summary['cc_by_phase']}.
Six stage12 withheld instruments remain excluded from BOTH native inversions.
Baseline selection already used these stations; holdout tests incremental change,
not independent absolute accuracy. Correlated pair rows are not independent samples.

## Results on identical retained events

Retained: {summary['retained']}; common comparison: {len(common)} events.
`cohort.csv` lists every original event and retention in both native variants.
Statistics below use only common events and identical observation rows per split.
All native-model predictions use the original Fortran ray tracer (`native/evaluate`).

```text
{metrics.to_string(index=False,float_format=lambda v:f'{v:.4f}')}
```

Fixed unambiguous reference pairs; median horizontal distance (km):

```text
{refsummary.to_string(float_format=lambda v:f'{v:.3f}')}
```

Shelly-only median absolute depth difference (km):

```text
{depths.to_string(float_format=lambda v:f'{v:.3f}')}
```

## Interpretation and next step

Adding CC yields only a small incremental change: withheld CC RMS is approximately
67.8 to 66.6 ms, while withheld catalog RMS is approximately 150.9 to 149.3 ms.
These millisecond-scale changes should not be called a decisive accuracy gain,
especially given the 0.01-s native origin-time output precision and shared picks.
Depth differences against Shelly do not improve further with CC (2.573 vs 2.578 km).
The same six events are removed by negative-depth rejection in both native runs.

Only {summary['training_cc_supported_events']}/144 events have accepted training CC,
across {summary['training_cc_event_pairs']} event pairs. Most large-scale changes are
already produced by catalog-only relocation; CC is a small additional constraint
at the current fixed weights. Maps alone do not establish a resolved fault structure.
Keep the existing v1 and these experimental products separate. A next bounded test
could examine CC support and fixed-weight sensitivity on the connected subcluster,
with the same withheld stations; do not immediately expand to the whole catalog or
switch pickers based on this result. FDTCC candidate generation has not been tested.

## Files

- `catalog_only/`, `catalog_cc/`: exact native inputs, logs, .loc/.reloc/.res files.
- `cc_measurements.csv`, `cc_components.csv`: accepted/rejected CC and reasons.
- `waveform_windows.csv`, `cc_windows.npz`: source-file record and extracted windows.
- `validation_pairs.csv`, `metrics.csv`: frozen-row training/withheld comparisons.
- `reference_comparison.csv`, `cohort.csv`, `common_events.csv`: comparison cohorts.
- `01_hypodd_comparison.png/pdf`: maps and east-depth projections, same events/axes.
- `02_cc_alignment.png/pdf`: lower/median/upper CC examples; left pick-aligned,
  right CC-aligned. These examples are not a census of waveform quality.
- `run.json`: settings, cohort counts and implementation/input fingerprints.

This is a bounded pilot, not an adopted final catalog. Native formal errors do not
include velocity, phase association, or waveform-lag uncertainty. Review withheld
CC and catalog residuals, event attrition, reference distances and depth stability
before any whole-catalog run. No tuning against reference locations is performed.
''')
    print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},indent=2),flush=True)
    print(metrics.to_string(index=False),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['all','cc','locate','report'],default='all');args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.stage in ['all','cc']:prepare_cc()
    if args.stage in ['all','locate']:run_native(build())
    if args.stage in ['all','report']:report()


if __name__=='__main__':main()
