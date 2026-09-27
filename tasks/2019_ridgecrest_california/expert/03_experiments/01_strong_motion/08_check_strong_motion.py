#!/usr/bin/env python3
"""Six-station, short-window HN experiment; never updates the baseline catalog."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']: os.environ[key]='1'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import argparse
import importlib.util
import json
import subprocess
import numpy as np
import pandas as pd
import yaml
from obspy import read, read_inventory, UTCDateTime, Stream, Trace
from obspy.signal.rotate import rotate2zne
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pyproj import Proj

HERE = Path(__file__).resolve().parents[2]  # Expert root; independent of working directory.
OUT=HERE/'export/08_check_strong_motion'
OLD=HERE/'export/07_audit_mainshocks'
STATIONS=['CLC','SRT','WRC2','WBM','MPM','WOR']
START=UTCDateTime('2019-07-06T03:19:23.04');END=START+120
VARIANTS={'HH_raw':None,'HN_velocity_wide':[.1,.2,40.,45.], 'HN_velocity_band':[.2,.5,20.,25.]}


def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,HERE/filename)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def fetch(path,service,params):
    if path.exists():return
    import requests
    session=requests.Session();session.trust_env=False
    response=session.get(f'https://service.scedc.caltech.edu/fdsnws/{service}/1/query',params=params,timeout=60)
    response.raise_for_status()
    if response.status_code==204:raise ValueError(f'No data: {params}')
    temporary=path.with_suffix(path.suffix+'.part');temporary.write_bytes(response.content);temporary.replace(path)
    print('Downloaded',path.name,len(response.content),'bytes',flush=True)


def waveform(station,family):
    old=OLD/'windows'/f'M7.1_CI.{station}..{family}.mseed'
    return old if old.exists() else OUT/'raw'/f'CI.{station}..{family}.mseed'


def prepare():
    (OUT/'raw').mkdir(exist_ok=True)
    params=dict(network='CI',station=','.join(STATIONS),location='--',channel='HH?,HN?',
                starttime=str(START),endtime=str(END),level='response')
    xml=OUT/'responses.xml';fetch(xml,'station',params)
    def download(station):
        path=waveform(station,'HN')
        fetch(path,'dataselect',dict(network='CI',station=station,location='--',channel='HN?',starttime=str(START),endtime=str(END)))
    with ThreadPoolExecutor(3) as pool:list(pool.map(download,STATIONS))
    inv=read_inventory(str(xml));rows=[]
    for station in STATIONS:
        for family in ['HH','HN']:
            path=waveform(station,family);stream=read(str(path)).trim(START,END)
            assert len(stream)==3 and not stream.get_gaps()
            assert {t.stats.channel for t in stream}=={family+c for c in 'ENZ'}
            for tr in stream:
                epochs=inv.select(network='CI',station=station,location='',channel=tr.stats.channel,
                                  starttime=tr.stats.starttime,endtime=tr.stats.endtime)
                channels=[c for n in epochs for s in n for c in s]
                assert len(channels)==1, (tr.id,len(channels))
                channel=channels[0]
                assert channel.start_date<=tr.stats.starttime and (channel.end_date is None or channel.end_date>=tr.stats.endtime)
                assert channel.response and channel.response.response_stages
                assert tr.stats.sampling_rate==channel.sample_rate==100
                assert tr.stats.starttime-START<=tr.stats.delta+1e-5 and END-tr.stats.endtime<=tr.stats.delta+1e-5
                assert np.isfinite(tr.data).all()
                sensitivity=channel.response.instrument_sensitivity
                if family=='HN':assert sensitivity.input_units.upper().replace(' ','') in ['M/S**2','M/S/S','M/S^2']
                rows.append(dict(station=station,family=family,seed_id=tr.id,path=os.path.relpath(path,OUT),bytes=path.stat().st_size,
                                 npts=tr.stats.npts,sample_rate_hz=tr.stats.sampling_rate,start_utc=str(tr.stats.starttime),end_utc=str(tr.stats.endtime),
                                 epoch_start=str(channel.start_date),epoch_end=str(channel.end_date),latitude=channel.latitude,
                                 longitude=channel.longitude,elevation_m=channel.elevation,sensor_depth_m=channel.depth,
                                 azimuth=channel.azimuth,dip=channel.dip,input_units=sensitivity.input_units,
                                 sensitivity=sensitivity.value,response_stages=len(channel.response.response_stages)))
    pd.DataFrame(rows).to_csv(OUT/'inputs.csv',index=False)
    print('Validated 36 waveform channels and response epochs',flush=True)


PICKER=None


def init_picker():
    global PICKER
    PICKER=module('phasenet_stage','01_pipeline/02_pick_phasenet.py')
    cfg=yaml.safe_load((HERE/'00_config/config.yaml').read_text())
    os.environ['SEISBENCH_CACHE_ROOT']=str(OUT/'cache')
    PICKER.initialize_worker((HERE/cfg['tools']['trace_library']).resolve(),'original','2',1)


def pick_one(task):
    import torch
    station,variant=task;family='HH' if variant=='HH_raw' else 'HN'
    inv=read_inventory(str(OUT/'responses.xml'))
    stream=read(str(waveform(station,family))).trim(START,END)
    start=max(t.stats.starttime for t in stream);end=min(t.stats.endtime for t in stream)
    stream.trim(start,end,nearest_sample=False)
    assert max(t.stats.starttime for t in stream)-min(t.stats.starttime for t in stream)<1e-5
    assert len({t.stats.npts for t in stream})==1
    if VARIANTS[variant] is not None:
        for tr in stream:
            tr.detrend('linear')
            tr.remove_response(inventory=inv,output='VEL',pre_filt=VARIANTS[variant],water_level=None,
                               zero_mean=True,taper=True,taper_fraction=.05)
            assert np.isfinite(tr.data).all()
    args=[]
    for comp in 'ZNE':
        tr=stream.select(component=comp)[0];orientation=inv.get_orientation(tr.id,tr.stats.starttime)
        args.extend([tr.data.astype(float),orientation['azimuth'],orientation['dip']])
    arrays=rotate2zne(*args);prepared=Stream()
    for comp,data in zip('ZNE',arrays):
        header=dict(stream[0].stats);header['channel']=family+comp
        prepared+=Trace(np.asarray(data,dtype=np.float32),header)
    prepared.write(str(OUT/'prepared'/f'{station}_{variant}.mseed'),format='MSEED',encoding='FLOAT32')
    with torch.inference_mode():
        probabilities=PICKER._WORKER_MODEL.annotate(prepared,strict=True,flexible_horizontal_components=False,batch_size=32)
        result=PICKER._WORKER_MODEL.classify_aggregate(probabilities,dict(PICKER._WORKER_MODEL.default_args,P_threshold=.3,S_threshold=.3))
    # MiniSEED channels are three characters; avoid truncating PhaseNet_P/S/N.
    for tr in probabilities:
        phase=tr.stats.channel.rsplit('_',1)[-1]
        assert phase in 'NPS' and len(phase)==1
        tr.stats.channel='PN'+phase
    probabilities.write(str(OUT/'probabilities'/f'{station}_{variant}.mseed'),format='MSEED',encoding='FLOAT32')
    return [dict(pick_id=f'{station}_{variant}_{i:03d}',station=station,variant=variant,phase=p.phase,
                 time_utc=str(p.peak_time),onset_utc=str(p.start_time),probability=float(p.peak_value))
            for i,p in enumerate(result.picks) if START+20<=p.peak_time<=END-20]


def pick():
    for folder in ['prepared','probabilities']: (OUT/folder).mkdir(exist_ok=True)
    tasks=[(s,v) for s in STATIONS for v in VARIANTS];rows=[]
    with ProcessPoolExecutor(3,initializer=init_picker) as pool:
        for task,result in zip(tasks,pool.map(pick_one,tasks)):
            rows+=result;print('Picked',*task,len(result),flush=True)
    fields=['pick_id','station','variant','phase','time_utc','onset_utc','probability']
    frame=pd.DataFrame(rows,columns=fields)
    if (OUT/'picks.csv').exists():
        previous=pd.read_csv(OUT/'picks.csv')
        pd.testing.assert_frame_equal(frame.reset_index(drop=True),previous,check_exact=False,atol=1e-7,rtol=1e-6)
    frame.to_csv(OUT/'picks.csv',index=False)


def assess():
    depth=module('depth_stage','02_diagnostics/06_diagnose_depth.py');cfg,bounds,jobs=depth.setup()
    base=next(j for j in jobs if j['event_id']=='gamma_0005482')
    stations=pd.read_csv(depth.NLL/'stations.csv').set_index('id')
    metadata=pd.read_csv(OUT/'inputs.csv')
    hn=metadata[metadata.family.eq('HN')].groupby('station').first()
    proj=Proj(proj='aeqd',lon_0=-117.55,lat_0=35.75,datum='WGS84',units='km')
    coordinates={};keys={};geometry=[]
    for station in STATIONS:
        r=hn.loc[station];old=stations.loc[f'CI.{station}..HH']
        x,y=proj(r.longitude,r.latitude);z=.7-(r.elevation_m-r.sensor_depth_m)/1000
        dz=z-old['z(km)'];horizontal=np.hypot(x-old['x(km)'],y-old['y(km)'])
        coordinates[station]=[x,y,z];keys[station]=f'S.H{STATIONS.index(station)+1:04d}'
        geometry.append(dict(station=station,horizontal_offset_km=horizontal,depth_offset_km=dz,x_km=x,y_km=y,z_km=z))
    pd.DataFrame(geometry).to_csv(OUT/'receiver_geometry.csv',index=False)
    directories=hn_grids(depth,coordinates)
    depth.initialize(directories['linear'],cfg,bounds)
    travel_job=dict(base,keys=list(keys.values()),stations=list(coordinates.values()),phases=['S']*6,observed=[0.]*6)
    times=depth.Problem(travel_job).travel(np.array(base['nll_xyz']))[0]
    origin=UTCDateTime(base['anchor'])+base['nll_origin_offset']
    predictions=dict(zip(STATIONS,[origin+float(t) for t in times]))
    picks=pd.read_csv(OUT/'picks.csv');picks['epoch']=pd.to_datetime(picks.time_utc,format='ISO8601',utc=True).astype('int64')/1e9
    candidates=[]
    for station in STATIONS:
        for variant in VARIANTS:
            match=picks[picks.station.eq(station)&picks.variant.eq(variant)&picks.phase.eq('S')&picks.epoch.between(float(predictions[station])-3,float(predictions[station])+3)]
            row=dict(station=station,variant=variant,predicted_s_utc=str(predictions[station]),candidate_count=len(match),
                     status='unique' if len(match)==1 else 'missing' if not len(match) else 'ambiguous',
                     pick_id='',time_utc=None,probability=np.nan,delay_from_prediction_s=np.nan)
            stream=read(str(OUT/'probabilities'/f'{station}_{variant}.mseed'))
            samples=np.concatenate([t.copy().trim(predictions[station]-3,predictions[station]+3).data for t in stream if t.stats.channel.endswith('S')])
            row['window_s_probability_max']=float(np.nanmax(samples))
            if len(match)==1:
                r=match.iloc[0];row.update(pick_id=r.pick_id,time_utc=r.time_utc,probability=r.probability,delay_from_prediction_s=r.epoch-float(predictions[station]))
            candidates.append(row)
    candidates=pd.DataFrame(candidates);candidates.to_csv(OUT/'candidates.csv',index=False)
    stable=[]
    for station in STATIONS:
        rows=candidates[candidates.station.eq(station)].set_index('variant')
        wide=rows.loc['HN_velocity_wide'];band=rows.loc['HN_velocity_band']
        delta=float(UTCDateTime(wide.time_utc)-UTCDateTime(band.time_utc)) if wide.status==band.status=='unique' else np.nan
        stable.append(dict(station=station,wide_time_utc=wide.get('time_utc'),band_time_utc=band.get('time_utc'),wide_minus_band_s=delta,fit_eligible=bool(abs(delta)<=.2)))
    stable=pd.DataFrame(stable);stable.to_csv(OUT/'selection.csv',index=False)
    # Reference times first enter after candidate and consensus selection is saved.
    official=pd.read_csv(OLD/'official_38457511.csv')
    refs=official[official.phase.eq('S')&official.weight.gt(0)].copy();refs['station']=refs.station_id.str.split('.').str[-1]
    joined=candidates.merge(refs[['station','time_utc','channel']],on='station',suffixes=('','_official'),validate='many_to_one')
    joined['difference_s']=(pd.to_datetime(joined.time_utc,utc=True,format='ISO8601')-pd.to_datetime(joined.time_utc_official,utc=True,format='ISO8601')).dt.total_seconds()
    joined.to_csv(OUT/'reference_comparison.csv',index=False)
    plot_candidates(joined,predictions)

    results=[];profiles=[];exported=[]
    vector_fields=['observed','pick_ids','phases','instruments','keys','stations','native_tt']
    for model,directory in directories.items():
        depth.initialize(directory,cfg,bounds)
        for variant in ['baseline','HN_stable']:
            job=dict(base);changed=[]
            for field in vector_fields:job[field]=list(base[field])
            if variant=='HN_stable':
                for r in stable[stable.fit_eligible].itertuples():
                    station=r.station
                    keep=[i for i,(instrument,phase) in enumerate(zip(job['instruments'],job['phases'])) if not (instrument.startswith('CI.'+station+'.') and phase=='S')]
                    for field in vector_fields:job[field]=[job[field][i] for i in keep]
                    for field,value in dict(observed=float(UTCDateTime(r.wide_time_utc)-UTCDateTime(job['anchor'])),
                                            pick_ids=f'HN_{station}_S',phases='S',instruments=f'CI.{station}..HN',keys=keys[station],
                                            stations=coordinates[station],native_tt=0.).items():job[field].append(value)
                    changed.append(station)
            assert len(set(zip([i.rsplit('.',1)[0] for i in job['instruments']],job['phases'])))==len(job['phases'])
            result,profile,phases=depth.solve(job)
            result.update(model=model,variant=variant,hn_stations=';'.join(changed),
                          hn_observations_used=len(changed),
                          interpretation='HN diagnostic fit' if changed else 'baseline reproduction only')
            # New HN phases have no original native prediction to compare against.
            if changed:result['native_tt_max_difference_s']=np.nan
            results.append(result)
            for row in profile:row.update(model=model,variant=variant)
            for row in phases:row.update(model=model,variant=variant)
            profiles+=profile;exported+=phases
            print(model,variant,'depth',result['depth_km'],'picks',result['n_picks'],'HN',changed,flush=True)
    pd.DataFrame(results).to_csv(OUT/'location_comparison.csv',index=False)
    pd.DataFrame(profiles).to_csv(OUT/'depth_profiles.csv',index=False)
    pd.DataFrame(exported).to_csv(OUT/'location_picks.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
    for ax,model in zip(axes,['linear','layered']):
        for variant,color in [('baseline','#0072B2'),('HN_stable','#D55E00')]:
            pp=pd.DataFrame(profiles);pp=pp[pp.model.eq(model)&pp.variant.eq(variant)]
            fit=next(r for r in results if r['model']==model and r['variant']==variant)
            ax.plot(pp.depth_km,pp.chi2-fit['refined_chi2'],color=color,label=variant)
        ax.set(title=model,xlabel='Depth (km)',ylabel='Δχ² within each variant',xlim=(0,25));ax.set_yscale('symlog',linthresh=1);ax.set_ylim(bottom=0)
    axes[0].legend(frameon=False)
    for ext in ['png','pdf']:fig.savefig(OUT/'figures'/f'depth_comparison.{ext}',dpi=180)
    plt.close(fig)
    write_checks()


def write_checks():
    inputs=pd.read_csv(OUT/'inputs.csv');picks=pd.read_csv(OUT/'picks.csv')
    selection=pd.read_csv(OUT/'selection.csv');candidates=pd.read_csv(OUT/'candidates.csv')
    fits=pd.read_csv(OUT/'location_comparison.csv');profiles=pd.read_csv(OUT/'depth_profiles.csv')
    assert len(inputs)==36 and inputs.seed_id.is_unique and inputs.response_stages.gt(0).all()
    assert len(candidates)==18 and len(selection)==6
    assert np.isfinite(fits[['depth_km','refined_chi2','refined_rms_s']]).all().all()
    assert len(profiles)==204 and profiles.successful_starts.gt(0).all()
    for file in (OUT/'probabilities').glob('*.mseed'):
        stream=read(str(file));assert {t.stats.channel for t in stream}=={'PNN','PNP','PNS'}
        assert all(np.nanmin(t.data)>=0 and np.nanmax(t.data)<=1.000001 for t in stream)
    for model,group in fits[fits.variant.eq('baseline')].groupby('model'):
        prior=pd.read_csv(HERE/f'export/06_diagnose_depth/{model}/events.csv').set_index('event_id').loc['gamma_0005482']
        columns=['x_km','y_km','depth_km','refined_chi2']
        assert np.allclose(group[columns],prior[columns].astype(float).values,atol=1e-5)
    original=pd.read_csv(OLD/'M7.1_nearby_picks.csv')
    original=original[original.event_id.eq('gamma_0005482')&original.phase.eq('S')].copy()
    original['station']=original.station_id.str.split('.').str[-1]
    context=candidates[candidates.variant.eq('HH_raw')&candidates.status.eq('unique')].merge(
        original[['station','time_utc']],on='station',suffixes=('','_baseline'),validate='one_to_one')
    context['time_difference_s']=(pd.to_datetime(context.time_utc,utc=True,format='ISO8601')-
                                  pd.to_datetime(context.time_utc_baseline,utc=True,format='ISO8601')).dt.total_seconds()
    context[['station','time_utc','time_utc_baseline','time_difference_s']].to_csv(OUT/'hh_context_check.csv',index=False)
    eligible=int(selection.fit_eligible.sum())
    record=dict(stations=6,hn_channels=18,validated_channels_including_hh=36,
                new_waveform_bytes=sum(p.stat().st_size for p in (OUT/'raw').glob('*.mseed')),
                total_hn_waveform_bytes=int(inputs[inputs.family.eq('HN')].drop_duplicates('path').bytes.sum()),
                response_xml_bytes=(OUT/'responses.xml').stat().st_size,inference_tasks=18,
                central_window_picks=len(picks),stable_hn_s_candidates=eligible,
                hh_context_common_s=len(context),hh_context_max_abs_time_difference_s=float(context.time_difference_s.abs().max()),
                baseline_catalog_unchanged=True,
                location_rows_interpretation='HN diagnostic input changes present' if eligible else 'All four rows use the same 37 baseline observations; no fit incorporating HN observations was possible.',
                settings=dict(phase_threshold=.3,gate_half_width_s=3,hn_consensus_tolerance_s=.2,output='VEL',water_level=None,
                              pre_filters_hz={k:v for k,v in VARIANTS.items() if v is not None},workers=3,torch_threads_per_worker=1))
    (OUT/'run.yaml').write_text(yaml.safe_dump(record,sort_keys=False))
    print('Checks passed:',record,flush=True)


def hn_grids(depth,coordinates):
    """HN burial differs from HH at some sites; compute separate S receiver grids."""
    directories={}
    for model,source in [('linear',depth.NLL/'grids'),('layered',depth.OUT/'layered_grids')]:
        directory=OUT/'grids'/model;directory.mkdir(parents=True,exist_ok=True)
        for path in source.glob('time.*.time.*'):
            link=directory/path.name
            if not link.exists():link.symlink_to(path.resolve())
        lines=[line for line in (source/'S.in').read_text().splitlines() if not line.startswith('GTSRCE ')]
        for i,station in enumerate(STATIONS,1):
            x,y,z=coordinates[station];lines.append(f'GTSRCE H{i:04d} XYZ {x:.8f} {y:.8f} {z:.8f} 0')
        content='\n'.join(lines)+'\n';control=directory/'S.in'
        same=control.exists() and control.read_text()==content
        control.write_text(content)
        if not same or len(list(directory.glob('time.S.H*.time.buf')))!=6:
            for binary in ['Vel2Grid','Grid2Time']:
                with (directory/f'{binary}.log').open('w') as log:
                    subprocess.run(['/liufeng1afs/software/NLLoc/NLL7.00_src/src/'+binary,control.name],cwd=directory,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
        assert len(list(directory.glob('time.S.H*.time.buf')))==6
        directories[model]=directory
    return directories


def plot_candidates(comparison,predictions):
    (OUT/'figures').mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    for page in range(2):
        fig,axes=plt.subplots(3,3,figsize=(12,8),layout='constrained')
        for row,station in enumerate(STATIONS[page*3:(page+1)*3]):
            center=predictions[station]
            for column,(variant,title) in enumerate([('raw','HN raw counts'),('HN_velocity_wide','HN velocity'),('probability','S probability')]):
                ax=axes[row,column]
                if variant=='probability':
                    for v,color in [('HH_raw','#777777'),('HN_velocity_wide','#D55E00'),('HN_velocity_band','#009E73')]:
                        stream=read(str(OUT/'probabilities'/f'{station}_{v}.mseed'))
                        for tr in stream:
                            if tr.stats.channel.endswith('S'):ax.plot(tr.times(reftime=center),tr.data,color=color,label=v,lw=.9)
                    ax.set_ylim(0,1);ax.axhline(.3,c='black',ls=':',lw=.6)
                else:
                    stream=read(str(waveform(station,'HN'))) if variant=='raw' else read(str(OUT/'prepared'/f'{station}_{variant}.mseed'))
                    for k,comp in enumerate('EN'):
                        tr=stream.select(component=comp)[0].copy().trim(center-4,center+6).detrend('demean')
                        ax.plot(tr.times(reftime=center),k+.38*tr.data/max(np.max(np.abs(tr.data)),1e-20),color='black',lw=.5)
                    ax.set_yticks([0,1],['E','N'])
                cc=comparison[comparison.station.eq(station)]
                for r in cc.itertuples():
                    if r.status=='unique':ax.axvline(float(UTCDateTime(r.time_utc)-center),color={'HH_raw':'#777777','HN_velocity_wide':'#D55E00','HN_velocity_band':'#009E73'}[r.variant],lw=.8)
                ax.axvline(float(UTCDateTime(cc.iloc[0].time_utc_official)-center),color='black',ls='--',lw=.8)
                ax.set(title=f'CI.{station} — {title}',xlim=(-4,6),xlabel='Time from baseline S prediction (s)')
        fig.legend(handles=[Line2D([],[],c='#777777',label='HH context'),Line2D([],[],c='#D55E00',label='HN wide'),
                            Line2D([],[],c='#009E73',label='HN band'),Line2D([],[],c='black',ls='--',label='SCEDC S')],
                   loc='outside lower center',ncol=4,frameon=False)
        for ext in ['png','pdf']:fig.savefig(OUT/'figures'/f's_onsets_{page+1:02d}.{ext}',dpi=180)
        plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',choices=['prepare','pick','assess'],required=True)
    args=parser.parse_args();OUT.mkdir(exist_ok=True)
    if args.stage=='prepare':prepare()
    elif args.stage=='pick':pick()
    else:assess()


if __name__=='__main__':main()
