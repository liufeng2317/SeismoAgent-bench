#!/usr/bin/env python3
"""Apply the frozen observation recipe to committed confirmation events."""
import argparse,json,multiprocessing,os
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
import _confirmation as C
D=C.load('confirmation_dpp',C.HERE/'03_experiments/08_vertical_observations/42_vertical_p.py')
Q=C.load('confirmation_eqt',C.HERE/'03_experiments/11_alternative_picker/46_qualify_eqtransformer.py')
ROOT=C.OUT/'observations'

def initialize(kind):
 m=D if kind=='P' else Q;m.OUT=ROOT/('dpp' if kind=='P' else 'eqt');m.OUT.mkdir(parents=True,exist_ok=True);m.initialize()
def work(job,kind):
 if kind=='P':return D.pick_job(job)[0]
 return Q.job(job)
def epoch(s):return pd.to_datetime(s,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9

def inference(jobs,kind,stage,workers):
 dest=ROOT/stage;dest.mkdir(parents=True,exist_ok=True)
 C.freeze(dest/'requests.json',{'jobs':jobs})
 # Initialize the shared library cache once before spawned workers import it.
 os.environ['SEISBENCH_CACHE_ROOT']=str(ROOT/('dpp' if kind=='P' else 'eqt')/'cache')
 import sys
 sys.path.insert(0,str(D.LIB/'ai_module'))
 import seisbench
 rows=[];pending=[]
 for job in jobs:
  f=dest/(job[0]+'.json')
  if f.exists():rows.extend(json.loads(f.read_text()))
  else:pending.append(job)
 print(stage,'queries',sum(len(j[1]) for j in jobs),'pending instruments',len(pending),flush=True)
 if pending:
  with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn'),initializer=initialize,initargs=(kind,)) as pool:
   futures={pool.submit(work,j,kind):j[0] for j in pending}
   for future in as_completed(futures):
    result=future.result();C.save(dest/(futures[future]+'.json'),result);rows.extend(result);print(stage,futures[future],len(result),'waveform accepted',sum(r['accepted'] for r in result),flush=True)
 return pd.DataFrame(rows)

def admit(q,competition,available,phase,causal=False):
 q=q.copy();q['phase']=phase;q['waveform_accepted']=q.accepted
 for instrument,g in q[q.accepted].groupby('instrument_id'):
  tab=competition[competition.instrument_id.eq(instrument)].sort_values('predicted_epoch_s');tt=tab.predicted_epoch_s.to_numpy();ids=tab.event_id.to_numpy()
  for i,r in g.iterrows():
   t=pd.Timestamp(r.candidate_utc).timestamp()
   # P historical runner compares competitors inside its already enforced 1 s gate.
   ix=np.flatnonzero(abs(tt-t)<=1.) if phase=='P' else np.arange(len(tt));ix=ix[np.argsort(abs(tt[ix]-t))[:2]]
   if not len(ix) or ids[ix[0]]!=r.event_id:q.loc[i,['accepted','reason']]=[False,'closer_competing_event']
   elif len(ix)>1 and abs(tt[ix[1]]-t)-abs(tt[ix[0]]-t)<.2:q.loc[i,['accepted','reason']]=[False,'ambiguous_competing_event']
  # Historical P removes new/new collisions before old-onset admission; S does old first.
  def new_collisions():
   rem=q[q.accepted&q.instrument_id.eq(instrument)].copy();rem['epoch']=epoch(rem.candidate_utc);rem=rem.sort_values('epoch');near=rem.epoch.diff().le(.100001)|rem.epoch.diff(-1).abs().le(.100001);q.loc[rem.index[near],['accepted','reason']]=[False,'new_onset_collision']
  if phase=='P':new_collisions()
  prev=available[available.instrument_id.eq(instrument)&available.phase.eq(phase)].copy();prev['epoch']=epoch(prev.time_utc);prev=prev.sort_values('epoch');ts=prev.epoch.to_numpy()
  for i,r in q[q.accepted&q.instrument_id.eq(instrument)].iterrows():
   t=pd.Timestamp(r.candidate_utc).timestamp();lo=np.searchsorted(ts,t-.100001);hi=np.searchsorted(ts,t+.100001,side='right')
   if prev.iloc[lo:hi].event_id.ne(r.event_id).any():q.loc[i,['accepted','reason']]=[False,'old_onset_collision']
  if phase=='S':new_collisions()
 if causal:
  p=available[available.phase.eq('P')].copy();p['epoch']=epoch(p.time_utc);times=p.groupby(['event_id','instrument_id']).epoch.max()
  for i,r in q[q.accepted].iterrows():
   key=(r.event_id,r.instrument_id)
   if key in times.index and pd.Timestamp(r.candidate_utc).timestamp()<=times.loc[key]:q.loc[i,['accepted','reason']]=[False,'noncausal_new_phase']
 return q

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=16);args=ap.parse_args();C.verify_candidate();ROOT.mkdir(parents=True,exist_ok=True)
 events,original,available=C.source_data();events=events[events.in_v1_working_catalog];assert len(events)==6520
 cohort=pd.read_csv(C.OUT/'initial/events.csv');ids=set(cohort.event_id);stations=pd.read_csv(C.BASE/'stations.csv').set_index('id');metadata=pd.read_csv(C.HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',keep_default_na=False);origins=epoch(events.origin_time)
 sourcefiles=[__file__,C.__file__,D.__file__,Q.__file__,C.OUT/'design.json',C.OUT/'initial/events.csv',C.OUT/'initial/differential_times.csv',C.SELECTED/'inputs/all_phases.csv',D.WEIGHT,D.META]
 C.freeze(ROOT/'design.json',{'round':30,'candidate':'stage50 frozen; no reference outcomes used','source_sha256':{str(f):C.sha(f) for f in sourcefiles},'method':'Reuse original DPP and EQTransformer inference unchanged. Preserve cached admitted observations; missing cells only; original 6520-event competition; old/new collision guards; no predicted arrivals admitted as picks.'})
 for stage,kind in [('vertical','P'),('missing_p','P'),('missing_s','S')]:
  if stage=='missing_s':available=add_lb(events,cohort,available,stations,origins)
  present=set(map(tuple,available[['event_id','instrument_id','phase']].to_numpy()));queries=[]
  if stage=='vertical':
   queries=[(eid,s) for s in ['CI.WNM..EH','CI.WRV2..EH','CI.WVP2..EH'] for eid in sorted(ids) if (eid,s,'P') not in present]
  elif stage=='missing_p':
   original_st=set(pd.read_csv(C.HERE/'export/04_locate_nonlinloc/stations.csv').id);p=available[available.event_id.isin(ids)&available.phase.eq('P')&available.instrument_id.isin(original_st)&~available.instrument_id.isin(C.held())];strong={e:set(g.loc[g.probability.ge(.7),'instrument_id']) for e,g in p.groupby('event_id')};pairs=pd.read_csv(C.OUT/'initial/differential_times.csv')[['event_id_a','event_id_b']].drop_duplicates();proposals=[]
   for a,b in pairs.itertuples(index=False,name=None):
    for seed,query in [(a,b),(b,a)]:
     for s in sorted(strong.get(seed,set())):
      if (query,s,'P') not in present:proposals.append((query,s,seed))
   pd.DataFrame(proposals,columns=['event_id','instrument_id','seed_event_id']).to_csv(ROOT/'neighbor_proposals.csv',index=False);queries=sorted({(e,s) for e,s,_ in proposals})
  else:
   inv=metadata[metadata.pilot_candidate.astype(str).eq('True')].copy();inv['instrument_id']=inv.station_id+'.'+inv.location+'.'+inv.family;instruments=sorted(set(inv.instrument_id)-C.held());queries=[(eid,s) for s in instruments for eid in sorted(ids) if (eid,s,'S') not in present]
  query=pd.DataFrame(queries,columns=['event_id','instrument_id']);jobs=[];competition=[]
  for instrument,g in query.groupby('instrument_id'):
   tt=origins+C.prediction(events,stations.loc[instrument],kind);tab=pd.DataFrame({'event_id':events.event_id,'instrument_id':instrument,'predicted_epoch_s':tt});competition.append(tab);rs=[]
   for r in tab[tab.event_id.isin(g.event_id)].itertuples():
    prefix={'vertical':'vp42_','missing_p':'mp44_','missing_s':'eqs47_'}[stage];key=prefix+'c3_'+instrument.replace('.','_')+'_'+r.event_id;rs.append({('pick_id' if kind=='P' else 'query_id'):key,'event_id':r.event_id,'phase':kind,'predicted_utc':pd.Timestamp(r.predicted_epoch_s,unit='s',tz='UTC').isoformat()})
   files=metadata[metadata.seed_id.eq(instrument+'Z')] if kind=='P' else inv[inv.instrument_id.eq(instrument)].drop(columns='instrument_id');assert len(files)==(3 if kind=='P' else 9);jobs.append((instrument,rs,files.to_dict('records')))
  q=inference(jobs,kind,stage,args.workers);q=admit(q,pd.concat(competition),available,kind,causal=kind=='S');q.to_csv(ROOT/(stage+'_candidates.csv'),index=False);records=[];seeds={j[0]:';'.join(sorted({r['seed_id'] for r in j[2]})) for j in jobs}
  for r in q[q.accepted].itertuples():
   net,sta,loc,family=r.instrument_id.split('.');records.append(dict(pick_id=r.pick_id if kind=='P' else r.query_id,event_id=r.event_id,instrument_id=r.instrument_id,station_id=net+'.'+sta,location=loc,channel_family=family,phase=kind,time_utc=r.candidate_utc,probability=np.nan,picker_score=r.post_step_score if kind=='P' else r.phase_score,pick_method='DPP_SCEDC_vertical_step' if kind=='P' else 'EQTransformer_original_nonconservative_v1',pick_error_s=.2 if kind=='P' else .3,source_channels=seeds[r.instrument_id],association_status='conditional_unambiguous'))
  new=pd.DataFrame(records);new.to_csv(ROOT/(stage+'_new_picks.csv'),index=False);available=pd.concat([available,new],ignore_index=True);assert available.pick_id.is_unique;assert not available[available.event_id.isin(ids)].duplicated(['event_id','instrument_id','phase']).any();print(stage,'admitted',len(new),flush=True)
 available.to_csv(ROOT/'available_phases.csv',index=False);available[available.event_id.isin(ids)].to_csv(ROOT/'all_phases.csv',index=False)
 C.save(ROOT/'summary.json',{'round':30,'cohort_events':len(cohort),'cohort_phases':int(available.event_id.isin(ids).sum()),'new_picks':{stage:len(pd.read_csv(ROOT/(stage+'_new_picks.csv'))) for stage in ['vertical','missing_p','lb','missing_s']},'reference_outcomes_read':False})
 for f,h in json.loads((ROOT/'design.json').read_text())['source_sha256'].items():assert C.sha(f)==h
 print((ROOT/'summary.json').read_text(),flush=True)

def add_lb(events,cohort,available,stations,origins):
 picks=pd.read_csv(C.HERE/'export/45_added_station/picking/picks.csv',keep_default_na=False);picks['accepted']=False;picks['reason']='low_probability';picks['event_id']='';ids=set(cohort.event_id);present=set(map(tuple,available[['event_id','instrument_id','phase']].to_numpy()));oldids=set(available.pick_id)
 for phase,gate in [('P',1.),('S',1.2)]:
  tt=origins+C.prediction(events,stations.loc['LB.DAC..HH'],phase);ee=events.event_id.to_numpy()
  for i,r in picks[picks.phase.eq(phase)&picks.probability.ge(.7)].iterrows():
   t=pd.Timestamp(r.time_utc).timestamp();ix=np.argsort(abs(tt-t))[:2];eid=ee[ix[0]];reason=None
   if abs(tt[ix[0]]-t)>gate:reason='outside_association_gate'
   elif abs(tt[ix[1]]-t)-abs(tt[ix[0]]-t)<.2:reason='ambiguous_competing_event'
   elif eid not in ids:reason='outside_working_cohort'
   elif r.pick_id in oldids or (eid,'LB.DAC..HH',phase) in present:reason='previously_observed_cell'
   if reason:picks.loc[i,'reason']=reason;continue
   picks.loc[i,['event_id','accepted','reason']]=[eid,True,'accepted']
 good=picks[picks.accepted].sort_values(['probability','time_utc'],ascending=[False,True]);picks.loc[good.index[good.duplicated(['event_id','phase'])],['accepted','reason']]=[False,'duplicate_event_phase']
 for phase,g in picks[picks.accepted].groupby('phase'):
  g=g.copy();g['epoch']=epoch(g.time_utc);g=g.sort_values('epoch');near=g.epoch.diff().le(.100001)|g.epoch.diff(-1).abs().le(.100001);picks.loc[g.index[near],['accepted','reason']]=[False,'duplicate_close_onsets']
 both=pd.concat([available[available.instrument_id.eq('LB.DAC..HH')][['event_id','phase','time_utc']],picks[picks.accepted][['event_id','phase','time_utc']]],ignore_index=True)
 for eid,g in both.groupby('event_id'):
  if set(g.phase)=={'P','S'} and min(epoch(g[g.phase.eq('S')].time_utc))<=max(epoch(g[g.phase.eq('P')].time_utc)):picks.loc[picks.accepted&picks.event_id.eq(eid)&picks.phase.eq('S'),['accepted','reason']]=[False,'noncausal_S']
 picks.to_csv(ROOT/'lb_candidates.csv',index=False);new=picks[picks.accepted].drop(columns=['accepted','reason']);new=new.copy();new['instrument_id']='LB.DAC..HH';new['association_status']='conditional_unambiguous';new['pick_method']='PhaseNet_original_v2';new['pick_error_s']=new.phase.map({'P':.1,'S':.2});new.to_csv(ROOT/'lb_new_picks.csv',index=False);print('LB admitted',len(new),flush=True);return pd.concat([available,new],ignore_index=True)
if __name__=='__main__':main()
