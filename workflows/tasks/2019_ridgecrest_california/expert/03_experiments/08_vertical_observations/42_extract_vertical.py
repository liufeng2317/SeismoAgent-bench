#!/usr/bin/env python3
"""Add only qualified, unambiguous vertical P candidates on a frozen cohort."""
from pathlib import Path
import importlib.util,json,sys,multiprocessing
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
from obspy import read_inventory,UTCDateTime
from pyproj import Proj
DIR=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
Q=load('qualifier42',DIR/'42_vertical_p.py');M=Q.M;HERE=Q.HERE;OUT=Q.OUT;SRC=HERE/'export/39_support_aware_pairs';BASE=M.BASE
N=load('native42',HERE/'01_pipeline/04_locate_nonlinloc.py')
STATIONS=['WNM','WRV2','WVP2']

def initialize():Q.initialize()
def pick_job(job):return Q.pick_job(job)

def grid_prediction(events,station):
 hdr=OUT/'generated_grids'/f'time.P.{station.nll_station}.time.hdr';parts=hdr.read_text().splitlines()[0].split();ny,nz=int(parts[1]),int(parts[2]);h=float(parts[7]);top=float(parts[5]);v=np.fromfile(hdr.with_suffix('.buf'),np.float32,count=ny*nz).reshape(ny,nz).astype(float)
 r=np.hypot(events.x_km-station['x(km)'],events.y_km-station['y(km)']).to_numpy()/h;z=(events.depth_km.to_numpy()-top)/h;i=np.floor(r).astype(int);j=np.floor(z).astype(int);a=r-i;b=z-j;assert np.all((i>=0)&(i<ny-1)&(j>=0)&(j<nz-1))
 return (1-a)*((1-b)*v[i,j]+b*v[i,j+1])+a*((1-b)*v[i+1,j]+b*v[i+1,j+1])

def prepare():
 qualification=json.loads((OUT/'qualification.json').read_text());assert all(qualification['qualification_gates'].values())
 (OUT/'generated_grids').mkdir(exist_ok=True);(OUT/'base/grids').mkdir(parents=True,exist_ok=True);(OUT/'inputs').mkdir(exist_ok=True);(DIR/'logs').mkdir(exist_ok=True)
 old=pd.read_csv(BASE/'stations.csv');inventory_path=Q.WAVE/'stations/earthscope.stationxml';inventory=read_inventory(str(inventory_path));proj=Proj(proj='aeqd',lat_0=35.75,lon_0=-117.55,datum='WGS84',units='km');rows=[]
 for number,sta in enumerate(STATIONS,1):
  channels=[c for net in inventory.select(network='CI',station=sta,channel='EHZ') for station in net for c in station if (c.start_date is None or c.start_date<=UTCDateTime('2019-07-04')) and (c.end_date is None or c.end_date>=UTCDateTime('2019-07-07')) and c.location_code==''];assert len(channels)==1;c=channels[0];assert c.sample_rate==100 and abs(c.dip+90)<.01
  x,y=proj(c.longitude,c.latitude);rows.append({'id':'CI.'+sta+'..EH','station_id':'CI.'+sta,'latitude':c.latitude,'longitude':c.longitude,'elevation_m':c.elevation,'sensor_depth_m':c.depth,'x(km)':x,'y(km)':y,'z(km)':.7-(c.elevation-c.depth)/1000,'nll_station':f'V{number:04d}','epoch_start':str(c.start_date),'epoch_end':str(c.end_date)})
 new=pd.DataFrame(rows);new.to_csv(OUT/'new_stations.csv',index=False);pd.concat([old,new[old.columns]],ignore_index=True).to_csv(OUT/'base/stations.csv',index=False)
 files=[Path(__file__),Path(Q.__file__),OUT/'design.json',OUT/'qualification.json',Q.WEIGHT,inventory_path,BASE/'stations.csv',BASE/'grids/P.in',SRC/'inputs/events.csv',SRC/'inputs/all_phases.csv',SRC/'cc_measurements.csv',SRC/'inputs/differential_times.csv',HERE/'export/10_validate_catalog/events.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py']
 design={'round':21,'intervention':'Add qualified vertical P observations from CI.WNM/WRV2/WVP2 to the fixed stage39 original-1D joint experiment. Same 300 targets and 2581 supports; same old phases/CC, Huber, model and solver. No stage40 regional-model or stage41 static corrections mixed in.','new_observation_error':'0.20 s new-P pick error plus unchanged 0.30 s model error; old P/S errors unchanged. DPP step scores are not PhaseNet phase probabilities: preserve a separate picker_score, with probability unset.','association':'Qualified fixed DPP rules unchanged. Each candidate must belong to its originally queried event and be the unique closest predicted P among ALL 6520 v1 events within 1 s; second-best absolute-residual margin >=0.20 s. Reject all remaining different-event onsets within 0.10 s. No reassignment or reference timing input. Preserve all rejected requests.','new_cc':'Only event pairs already present among stage39 candidate phase pairs; add P rows when both endpoints have admitted new-station picks. Use unchanged scalar P correlation/quality rules, including historical padded-window exclusions. All existing CC rows retained unchanged.','comparisons':'Recompute 16 absolute/joint solves with new observations; compare with frozen stage39 and original NLL on same targets, original held 1394 absolute/1408 CC and all old575 CC. Six held instruments and auxiliary-eligibility flags remain fixed. New stations are training-only. Preserve stage34 coverage/reference/boundary/anchor gates; old575 and old1408 CC RMS <=1.05 stage39, reference medians <=1.10 stage39 joint as additional gates. No gain claim from increased observation count alone.','receiver_handling':'One StationXML epoch must cover all three days; use channel elevation minus burial and benchmark +0.7 km plane. Three new native radial P tables use exact original model/control settings. Repeat one existing receiver as a bitwise numerical control.','source_sha256':{str(f):M.sha(f) for f in files}}
 dest=OUT/'target_design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 grid=OUT/'generated_grids';control_station=old[old.id.eq('CI.CLC..HH')].iloc[0].copy();control_alias=control_station.nll_station;control_station.nll_station='Q0000';sources=pd.concat([new,control_station.to_frame().T],ignore_index=True)
 text='\n'.join(line for line in (BASE/'grids/P.in').read_text().splitlines() if not line.startswith('GTSRCE '))+'\n'
 text+='\n'.join(f"GTSRCE {r['nll_station']} XYZ {r['x(km)']:.8f} {r['y(km)']:.8f} {r['z(km)']:.8f} 0" for r in sources.to_dict('records'))+'\n';control=grid/'P.in';control.write_text(text)
 if not (grid/'time.P.Q0000.time.buf').exists():
  for binary in ['Vel2Grid','Grid2Time']:N.execute(Path('/liufeng1afs/software/NLLoc/NLL7.00_src/src')/binary,control,grid,DIR/'logs'/('42_'+binary+'.log'),300)
 assert M.sha(grid/'time.P.Q0000.time.buf')==M.sha(BASE/'grids'/f'time.P.{control_alias}.time.buf')
 for source in list((BASE/'grids').glob('time.*.time.*'))+[f for r in new.itertuples() for f in [grid/f'time.P.{r.nll_station}.time.hdr',grid/f'time.P.{r.nll_station}.time.buf']]:
  dest=OUT/'base/grids'/source.name
  if not dest.exists():dest.symlink_to(source)
  assert dest.resolve()==source.resolve()
 M.save(OUT/'new_grid_checks.json',{'repeated_receiver':'CI.CLC..HH','bitwise_TIME_control':True,'receivers':new[['id','sensor_depth_m','z(km)']].to_dict('records'),'grid_sha256':{str(f):M.sha(f) for f in grid.glob('time.*.time.*')}})
 all_events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');all_events=all_events[all_events.in_v1_working_catalog].copy();assert len(all_events)==6520
 cohort=pd.read_csv(SRC/'inputs/events.csv');all_origins=pd.to_datetime(all_events.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9;metadata=pd.read_csv(HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',keep_default_na=False);jobs=[];competition=[]
 for _,station in new.iterrows():
  prediction=all_origins+grid_prediction(all_events,station);table=pd.DataFrame({'event_id':all_events.event_id,'instrument_id':station.id,'predicted_epoch_s':prediction});competition.append(table);q=table[table.event_id.isin(cohort.event_id)];assert len(q)==len(cohort)
  requests=[dict(pick_id='vp42_'+station.station_id.replace('.','_')+'_'+r.event_id,event_id=r.event_id,predicted_utc=pd.Timestamp(r.predicted_epoch_s,unit='s',tz='UTC').isoformat()) for r in q.itertuples()];files=metadata[metadata.seed_id.eq(station.id+'Z')];assert len(files)==3;jobs.append((station.id,requests,files.to_dict('records')))
 pd.concat(competition).to_csv(OUT/'competition_predictions.csv',index=False)
 return jobs

def main():
 jobs=prepare();results=[];arrays={}
 with ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'),initializer=initialize) as pool:
  for i,f in enumerate(as_completed([pool.submit(pick_job,j) for j in jobs]),1):
   rows,data=f.result();results.extend(rows);arrays.update(data);print('Vertical station',i,'/3; waveform-qualified',sum(r['accepted'] for r in rows),'/',len(rows),flush=True)
 q=pd.DataFrame(results).sort_values(['instrument_id','event_id']);q['waveform_accepted']=q.accepted;competition=pd.read_csv(OUT/'competition_predictions.csv')
 for instrument,g in q[q.accepted].groupby('instrument_id'):
  other=competition[competition.instrument_id.eq(instrument)].sort_values('predicted_epoch_s');times=other.predicted_epoch_s.to_numpy();ids=other.event_id.to_numpy()
  for index,row in g.iterrows():
   time=float(pd.Timestamp(row.candidate_utc).timestamp());lo,hi=np.searchsorted(times,[time-1,time+1]);residual=abs(times[lo:hi]-time);order=np.argsort(residual)
   if len(order)==0 or ids[lo+order[0]]!=row.event_id:q.loc[index,['accepted','reason']]=[False,'closer_competing_event'];continue
   if len(order)>1 and residual[order[1]]-residual[order[0]]<.2:q.loc[index,['accepted','reason']]=[False,'ambiguous_competing_event']
  remaining=q[q.accepted&q.instrument_id.eq(instrument)].copy();remaining['epoch']=remaining.candidate_utc.map(lambda v:float(pd.Timestamp(v).timestamp()));remaining=remaining.sort_values('epoch');near=remaining.epoch.diff().le(.100001)|remaining.epoch.diff(-1).abs().le(.100001);q.loc[remaining.index[near],['accepted','reason']]=[False,'duplicate_close_onsets']
 q.to_csv(OUT/'vertical_candidates.csv',index=False);np.savez_compressed(OUT/'vertical_windows.npz',**arrays)
 rows=[]
 for r in q[q.accepted].itertuples():
  station=r.instrument_id.split('.');rows.append({'pick_id':r.pick_id,'station_id':'.'.join(station[:2]),'location':station[2],'channel_family':station[3],'phase':'P','time_utc':r.candidate_utc,'probability':np.nan,'source_channels':r.source_seed_id,'instrument_id':r.instrument_id,'event_id':r.event_id,'association_status':'conditional_unambiguous','pick_method':'DPP_SCEDC_vertical_step','picker_score':r.post_step_score,'pick_error_s':.2})
 new=pd.DataFrame(rows);new.to_csv(OUT/'new_picks.csv',index=False);old=pd.read_csv(SRC/'inputs/all_phases.csv');combined=pd.concat([old,new],ignore_index=True);assert combined.pick_id.is_unique;combined.to_csv(OUT/'inputs/all_phases.csv',index=False)
 (OUT/'inputs/events.csv').write_bytes((SRC/'inputs/events.csv').read_bytes())
 M.save(OUT/'extraction_summary.json',{'requested':len(q),'waveform_accepted':int(q.waveform_accepted.sum()),'admitted_after_association':len(new),'station_counts':new.instrument_id.value_counts().to_dict() if len(new) else {},'new_station_S_observations':0,'old_phase_rows':len(old),'all_phase_rows':len(combined),'rejections':q[~q.accepted].reason.value_counts().to_dict()})
 for f,h in json.loads((OUT/'target_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'extraction_summary.json').read_text(),flush=True)
if __name__=='__main__':main()
