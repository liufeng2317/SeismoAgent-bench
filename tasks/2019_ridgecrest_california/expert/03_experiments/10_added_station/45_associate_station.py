#!/usr/bin/env python3
"""Generate native LB.DAC P/S tables and associate independently detected arrivals."""
from pathlib import Path
import argparse,importlib.util,json
import numpy as np
import pandas as pd
from pyproj import Proj
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/45_added_station';SRC=HERE/'export/44_missing_p_observations';BASE=HERE/'export/42_vertical_p_observations/base';ORIGINAL=HERE/'export/04_locate_nonlinloc'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('engine45a',HERE/'03_experiments/07_joint_location/33_joint_location.py');N=load('native45a',HERE/'01_pipeline/04_locate_nonlinloc.py')
def freeze(path,data):
 if path.exists():assert json.loads(path.read_text())==data
 else:M.save(path,data)
def prediction(events,station,phase):
 hdr=OUT/'generated_grids'/f'time.{phase}.D0045.time.hdr';parts=hdr.read_text().splitlines()[0].split();ny,nz=int(parts[1]),int(parts[2]);h=float(parts[7]);top=float(parts[5]);v=np.fromfile(hdr.with_suffix('.buf'),np.float32,count=ny*nz).reshape(ny,nz).astype(float)
 r=np.hypot(events.x_km-station['x(km)'],events.y_km-station['y(km)']).to_numpy()/h;z=(events.depth_km.to_numpy()-top)/h;i=np.floor(r).astype(int);j=np.floor(z).astype(int);a=r-i;b=z-j;assert np.all((i>=0)&(i<ny-1)&(j>=0)&(j<nz-1))
 return (1-a)*((1-b)*v[i,j]+b*v[i,j+1])+a*((1-b)*v[i+1,j]+b*v[i+1,j+1])
def grids():
 for p in ['generated_grids','base/grids','inputs']:(OUT/p).mkdir(parents=True,exist_ok=True)
 metadata=pd.read_csv(OUT/'new_waveform_inputs.csv');r=metadata.iloc[0];assert metadata[['latitude','longitude','elevation_m']].drop_duplicates().shape[0]==1
 proj=Proj(proj='aeqd',lat_0=35.75,lon_0=-117.55,datum='WGS84',units='km');x,y=proj(r.longitude,r.latitude)
 station={'id':'LB.DAC..HH','station_id':'LB.DAC','latitude':r.latitude,'longitude':r.longitude,'elevation_m':r.elevation_m,'sensor_depth_m':0.,'x(km)':x,'y(km)':y,'z(km)':.7-r.elevation_m/1000,'nll_station':'D0045'}
 old=pd.read_csv(BASE/'stations.csv');pd.concat([old,pd.DataFrame([station])[old.columns]],ignore_index=True).to_csv(OUT/'base/stations.csv',index=False)
 check=old[old.id.eq('CI.CLC..HH')].iloc[0].copy();alias=check.nll_station;check.nll_station='Q0000';grid=OUT/'generated_grids';identity={}
 # Use the original stage04 P and S controls, never the later generated P-only control.
 for phase in ['P','S']:
  template=ORIGINAL/'grids'/f'{phase}.in';assert template.exists(),template
  text='\n'.join(l for l in template.read_text().splitlines() if not l.startswith('GTSRCE '))+'\n'
  text+='\n'.join(f"GTSRCE {s['nll_station']} XYZ {s['x(km)']:.8f} {s['y(km)']:.8f} {s['z(km)']:.8f} 0" for s in [station,check.to_dict()])+'\n';control=grid/f'{phase}.in';control.write_text(text)
  if not (grid/f'time.{phase}.Q0000.time.buf').exists():
   for binary in ['Vel2Grid','Grid2Time']:N.execute(Path('/liufeng1afs/software/NLLoc/NLL7.00_src/src')/binary,control,grid,DIR/'logs'/f'45_{phase}_{binary}.log',300)
  assert M.sha(grid/f'time.{phase}.Q0000.time.buf')==M.sha(BASE/'grids'/f'time.{phase}.{alias}.time.buf')
  identity[phase]=True
 for source in list((BASE/'grids').glob('time.*.time.*'))+list(grid.glob('time.*.D0045.time.*')):
  dest=OUT/'base/grids'/source.name
  if not dest.exists():dest.symlink_to(source)
  assert dest.resolve()==source.resolve()
 freeze(OUT/'new_grid_checks.json',{'repeated_receiver':'CI.CLC..HH','bitwise_TIME_control':identity,'receiver':station,'grid_sha256':{str(f):M.sha(f) for f in grid.glob('time.*.time.*')}})
 return station

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--grids-only',action='store_true');args=ap.parse_args();station=grids()
 if args.grids_only:return
 assert json.loads((OUT/'picking/run.json').read_text())['status']=='complete'
 files=[Path(__file__),OUT/'design.json',OUT/'picking/picks.csv',OUT/'new_grid_checks.json',SRC/'inputs/all_phases.csv',SRC/'inputs/events.csv',HERE/'export/10_validate_catalog/events.csv',HERE/'docs/optimization_reserved_events_v3.csv']
 freeze(OUT/'target_design.json',{'round':24,'source_sha256':{str(f):M.sha(f) for f in files}})
 events=pd.read_csv(files[-2]);events=events[events.in_v1_working_catalog];assert len(events)==6520
 cohort=pd.read_csv(SRC/'inputs/events.csv');reserved=pd.read_csv(files[-1]);assert not set(cohort.event_id)&set(reserved.event_id)
 times=pd.to_datetime(events.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9
 picks=pd.read_csv(OUT/'picking/picks.csv',keep_default_na=False);picks['accepted']=False;picks['reason']='low_probability';picks['event_id']='';picks['model_residual_s']=np.nan;predictions=[]
 for phase,gate in [('P',1.),('S',1.2)]:
  predicted=times+prediction(events,station,phase);order=np.argsort(predicted);epochs=predicted[order];ids=events.event_id.to_numpy()[order]
  predictions.append(pd.DataFrame({'event_id':events.event_id,'phase':phase,'predicted_epoch_s':predicted}))
  for i,r in picks[picks.phase.eq(phase)&picks.probability.ge(.7)].iterrows():
   t=pd.Timestamp(r.time_utc).timestamp();nearest=np.argsort(abs(epochs-t))[:2];j=nearest[0];residual=abs(epochs[j]-t)
   if residual>gate:picks.loc[i,'reason']='outside_association_gate';continue
   if abs(epochs[nearest[1]]-t)-residual<.2:picks.loc[i,'reason']='ambiguous_competing_event';continue
   # Do not emit linked reserve/noncohort arrivals.
   if ids[j] not in set(cohort.event_id):picks.loc[i,'reason']='outside_working_cohort';continue
   picks.loc[i,['event_id','model_residual_s','accepted','reason']]=[ids[j],t-epochs[j],True,'accepted']
 # Highest confidence per event/phase; retain the complete rejection audit.
 good=picks[picks.accepted].sort_values(['probability','time_utc'],ascending=[False,True]);dup=good.duplicated(['event_id','phase']);picks.loc[good.index[dup],['accepted','reason']]=[False,'duplicate_event_phase']
 for phase,g in picks[picks.accepted].groupby('phase'):
  g=g.copy();g['epoch']=pd.to_datetime(g.time_utc,utc=True,format='ISO8601').astype('int64')/1e9;g=g.sort_values('epoch');near=g.epoch.diff().le(.100001)|g.epoch.diff(-1).abs().le(.100001);picks.loc[g.index[near],['accepted','reason']]=[False,'duplicate_close_onsets']
 for event,g in picks[picks.accepted].groupby('event_id'):
  if set(g.phase)=={'P','S'} and g[g.phase.eq('S')].time_utc.iloc[0]<=g[g.phase.eq('P')].time_utc.iloc[0]:picks.loc[g[g.phase.eq('S')].index,['accepted','reason']]=[False,'noncausal_S']
 picks.to_csv(OUT/'association_audit.csv',index=False)
 # Preserve predictions only for this working cohort, not reserve3.
 pd.concat(predictions).query('event_id in @cohort.event_id').to_csv(OUT/'cohort_predictions.csv',index=False)
 new=picks[picks.accepted].drop(columns=['accepted','reason']).copy();new['instrument_id']='LB.DAC..HH';new['association_status']='conditional_unambiguous';new['pick_method']='PhaseNet_original_v2';new['pick_error_s']=new.phase.map({'P':.1,'S':.2});new.to_csv(OUT/'new_picks.csv',index=False)
 old=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);combined=pd.concat([old,new],ignore_index=True);assert combined.pick_id.is_unique;combined.to_csv(OUT/'inputs/all_phases.csv',index=False);(OUT/'inputs/events.csv').write_bytes((SRC/'inputs/events.csv').read_bytes())
 result={'new_picks':len(new),'phase_counts':new.phase.value_counts().to_dict(),'events_with_new_observations':new.event_id.nunique(),'targets_with_new_observations':len(set(new.event_id)&set(cohort[cohort.role.eq('reserve')].event_id)),'rejections':picks[~picks.accepted].reason.value_counts().to_dict(),'old_rows_preserved':len(old),'reserve3_used':False}
 M.save(OUT/'extraction_summary.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
