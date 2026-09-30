#!/usr/bin/env python3
"""Add missing S only after separate S compatibility qualification; retain the failed joint trial."""
from pathlib import Path
import argparse,importlib.util,sys,json,multiprocessing
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('qualify46',DIR/'46_qualify_eqtransformer.py');Q=importlib.util.module_from_spec(s);sys.modules[s.name]=Q;s.loader.exec_module(Q)
HERE=Q.HERE;QUAL=Q.OUT;OUT=HERE/'export/47_missing_s_observations';SRC=HERE/'export/45_added_station';BASE=SRC/'base';M=Q.M

def prediction(events,station,phase):
 hdr=BASE/'grids'/f'time.{phase}.{station.nll_station}.time.hdr';p=hdr.read_text().splitlines()[0].split();ny,nz=int(p[1]),int(p[2]);h=float(p[7]);top=float(p[5]);v=np.fromfile(hdr.with_suffix('.buf'),np.float32,count=ny*nz).reshape(ny,nz).astype(float);r=np.hypot(events.x_km-station['x(km)'],events.y_km-station['y(km)']).to_numpy()/h;z=(events.depth_km.to_numpy()-top)/h;i=np.floor(r).astype(int);j=np.floor(z).astype(int);a=r-i;b=z-j;assert np.all((i>=0)&(i<ny-1)&(j>=0)&(j<nz-1))
 return (1-a)*((1-b)*v[i,j]+b*v[i,j+1])+a*((1-b)*v[i+1,j]+b*v[i+1,j+1])

def initialize():
 Q.OUT=OUT;Q.initialize()
def work(job):return Q.job(job)

def prepare():
 result=json.loads((QUAL/'qualification.json').read_text());assert result['decision']=='do_not_add_eqt_observations' and all(result['qualification_gates']['S_'+k] for k in ['size','coverage','timing'])
 OUT.mkdir(exist_ok=True)
 for name in ['target_chunks','inputs']:(OUT/name).mkdir(exist_ok=True)
 for path,h in json.loads((QUAL/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(path))==h
 old=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);cohort=pd.read_csv(SRC/'inputs/events.csv');all_events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');all_events=all_events[all_events.in_v1_working_catalog].copy();assert len(all_events)==6520
 manifest=HERE/'export/01_prepare_inputs/full/waveform_inputs.csv';inv=pd.read_csv(manifest,keep_default_na=False);inv=inv[inv.pilot_candidate.astype(str).eq('True')];inv['instrument_id']=inv.station_id+'.'+inv.location+'.'+inv.family
 held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'];inv=inv[~inv.instrument_id.isin(held)];stations=pd.read_csv(BASE/'stations.csv').set_index('id');origins=pd.to_datetime(all_events.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9
 observed=set(map(tuple,old[['event_id','instrument_id','phase']].to_numpy()));jobs=[];competition=[];requests=[]
 for instrument,g in inv.groupby('instrument_id'):
  rs=[]
  for phase in ['S']:
   predicted=origins+prediction(all_events,stations.loc[instrument],phase);table=pd.DataFrame({'event_id':all_events.event_id,'instrument_id':instrument,'phase':phase,'predicted_epoch_s':predicted});competition.append(table)
   for r in table[table.event_id.isin(cohort.event_id)].itertuples():
    if (r.event_id,instrument,phase) in observed:continue
    request={'query_id':f'eqs47_{len(requests):07d}','event_id':r.event_id,'phase':phase,'predicted_utc':pd.Timestamp(r.predicted_epoch_s,unit='s',tz='UTC').isoformat()};rs.append(request);requests.append(dict(request,instrument_id=instrument))
  if rs:jobs.append((instrument,rs,g.drop(columns=['instrument_id']).to_dict('records')))
 # Competitors are used only for admission; do not write linked reserve outcomes.
 pd.DataFrame(requests).to_csv(OUT/'target_requests.csv',index=False)
 files=[Path(__file__),Path(Q.__file__),QUAL/'design.json',QUAL/'qualification.json',OUT/'target_requests.csv',SRC/'inputs/all_phases.csv',SRC/'inputs/events.csv',HERE/'export/10_validate_catalog/events.csv',manifest,BASE/'stations.csv']+list((BASE/'grids').glob('time.*.time.*'))
 Q.freeze(OUT/'target_design.json',{'round':26,'intervention':'S-only observation augmentation after the joint P/S candidate failed P coverage. This is a separate candidate, not a retrospective pass for round25. Reuse unchanged qualified S inference; preserve all stage45 old data, event identities, original locator and catalog gates.','source_sha256':{str(f):M.sha(f) for f in files},'queries':len(requests),'instruments':len(jobs),'admission':'Missing cells only. Keep queried identity only if uniquely closest among all6520 original v1 events, margin>=0.2s, within original phase gate. Reject old or new different-event same-phase onsets within0.100001s and noncausal new phase. Preserve all old data.','new_errors':'Pick error0.2sP/0.3sS plus old model0.3s; model scores kept separately, not treated as calibrated probabilities.'})
 return jobs,pd.concat(competition),old

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=16);args=ap.parse_args();jobs,competition,old=prepare();rows=[];pending=[]
 for job in jobs:
  file=OUT/'target_chunks'/(job[0]+'.json')
  if file.exists():rows.extend(json.loads(file.read_text()))
  else:pending.append(job)
 print('Target queries',sum(len(j[1]) for j in jobs),'stations',len(jobs),'pending',len(pending),flush=True)
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn'),initializer=initialize) as pool:
  futures={pool.submit(work,j):j[0] for j in pending}
  for future in as_completed(futures):
   r=future.result();M.save(OUT/'target_chunks'/(futures[future]+'.json'),r);rows.extend(r)
 q=pd.DataFrame(rows).sort_values('query_id').reset_index(drop=True);q['waveform_accepted']=q.accepted
 for (instrument,phase),g in q[q.accepted].groupby(['instrument_id','phase']):
  other=competition[competition.instrument_id.eq(instrument)&competition.phase.eq(phase)].sort_values('predicted_epoch_s');ts=other.predicted_epoch_s.to_numpy();ids=other.event_id.to_numpy()
  for i,r in g.iterrows():
   t=pd.Timestamp(r.candidate_utc).timestamp();ix=np.argsort(abs(ts-t))[:2]
   if ids[ix[0]]!=r.event_id:q.loc[i,['accepted','reason']]=[False,'closer_competing_event']
   elif abs(ts[ix[1]]-t)-abs(ts[ix[0]]-t)<.2:q.loc[i,['accepted','reason']]=[False,'ambiguous_competing_event']
 pool=pd.concat([pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',low_memory=False),old],ignore_index=True).drop_duplicates('pick_id');pool=pool[pool.event_id.notna()].copy();pool['epoch']=pd.to_datetime(pool.time_utc,utc=True,format='ISO8601').astype('int64')/1e9
 for (instrument,phase),g in q[q.accepted].groupby(['instrument_id','phase']):
  prev=pool[pool.instrument_id.eq(instrument)&pool.phase.eq(phase)].sort_values('epoch');ts=prev.epoch.to_numpy()
  for i,r in g.iterrows():
   t=pd.Timestamp(r.candidate_utc).timestamp();lo=np.searchsorted(ts,t-.100001);hi=np.searchsorted(ts,t+.100001,side='right')
   if prev.iloc[lo:hi].event_id.ne(r.event_id).any():q.loc[i,['accepted','reason']]=[False,'old_onset_collision']
  rem=q[q.accepted&q.instrument_id.eq(instrument)&q.phase.eq(phase)].copy();rem['epoch']=pd.to_datetime(rem.candidate_utc,utc=True,format='ISO8601').astype('int64')/1e9;rem=rem.sort_values('epoch');near=rem.epoch.diff().le(.100001)|rem.epoch.diff(-1).abs().le(.100001);q.loc[rem.index[near],['accepted','reason']]=[False,'new_onset_collision']
 both=pd.concat([old[['event_id','instrument_id','phase','time_utc']],q[q.accepted][['event_id','instrument_id','phase','candidate_utc']].rename(columns={'candidate_utc':'time_utc'})],ignore_index=True);both['epoch']=pd.to_datetime(both.time_utc,utc=True,format='ISO8601').astype('int64')/1e9;phase_times=both.groupby(['event_id','instrument_id','phase']).epoch.agg(['min','max'])
 for i,r in q[q.accepted].iterrows():
  opposite='S' if r.phase=='P' else 'P';key=(r.event_id,r.instrument_id,opposite)
  if key not in phase_times.index:continue
  t=pd.Timestamp(r.candidate_utc).timestamp();bad=t>=phase_times.loc[key,'min'] if r.phase=='P' else t<=phase_times.loc[key,'max']
  if bad:q.loc[i,['accepted','reason']]=[False,'noncausal_new_phase']
 q.to_csv(OUT/'target_candidates.csv',index=False);records=[];seeds={j[0]:';'.join(sorted({r['seed_id'] for r in j[2]})) for j in jobs}
 for r in q[q.accepted].itertuples():
  net,sta,loc,family=r.instrument_id.split('.');records.append({'pick_id':r.query_id,'event_id':r.event_id,'instrument_id':r.instrument_id,'station_id':net+'.'+sta,'location':loc,'channel_family':family,'phase':r.phase,'time_utc':r.candidate_utc,'probability':np.nan,'picker_score':r.phase_score,'detection_score':r.detection_score,'pick_method':'EQTransformer_original_nonconservative_v1','pick_error_s':{'P':.2,'S':.3}[r.phase],'source_channels':seeds[r.instrument_id],'association_status':'conditional_unambiguous'})
 new=pd.DataFrame(records);new.to_csv(OUT/'new_picks.csv',index=False);combined=pd.concat([old,new],ignore_index=True);assert combined.pick_id.is_unique;combined.to_csv(OUT/'inputs/all_phases.csv',index=False);(OUT/'inputs/events.csv').write_bytes((SRC/'inputs/events.csv').read_bytes())
 targets=set(pd.read_csv(SRC/'inputs/events.csv').query("role=='reserve'").event_id);M.save(OUT/'extraction_summary.json',{'requested':len(q),'waveform_accepted':int(q.waveform_accepted.sum()),'new_picks':len(new),'phase_counts':new.phase.value_counts().to_dict(),'events_with_new_observations':new.event_id.nunique(),'targets_with_new_observations':len(set(new.event_id)&targets),'old_rows_preserved':len(old),'rejections':q[~q.accepted].reason.value_counts().to_dict(),'reserve3_used':False})
 for f,h in json.loads((OUT/'target_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'extraction_summary.json').read_text(),flush=True)
if __name__=='__main__':main()
