#!/usr/bin/env python3
"""Use unchanged qualified DPP P inference at recorded missing-P instruments."""
from pathlib import Path
import importlib.util,json,sys,multiprocessing,argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
Q=load('dpp44',DIR/'42_vertical_p.py');M=Q.M;HERE=M.HERE;OUT=HERE/'export/44_missing_p_observations';SRC=HERE/'export/42_vertical_p_observations';GRAPH=HERE/'export/39_support_aware_pairs';Q.OUT=OUT

def initialize():Q.initialize()
def pick_job(job):return Q.pick_job(job)
def predict(events,station):
 hdr=M.BASE/'grids'/f'time.P.{station.nll_station}.time.hdr';parts=hdr.read_text().splitlines()[0].split();ny,nz=int(parts[1]),int(parts[2]);h=float(parts[7]);top=float(parts[5]);v=np.fromfile(hdr.with_suffix('.buf'),np.float32,count=ny*nz).reshape(ny,nz).astype(float)
 r=np.hypot(events.x_km-station['x(km)'],events.y_km-station['y(km)']).to_numpy()/h;z=(events.depth_km.to_numpy()-top)/h;i=np.floor(r).astype(int);j=np.floor(z).astype(int);a=r-i;b=z-j;assert np.all((i>=0)&(i<ny-1)&(j>=0)&(j<nz-1))
 return (1-a)*((1-b)*v[i,j]+b*v[i,j+1])+a*((1-b)*v[i+1,j]+b*v[i+1,j+1])

def prepare():
 OUT.mkdir(exist_ok=True);(OUT/'inputs').mkdir(exist_ok=True)
 assert all(json.loads((SRC/'qualification.json').read_text())['qualification_gates'].values())
 for f,h in json.loads((SRC/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 ph=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);e=pd.read_csv(SRC/'inputs/events.csv');held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']);original_st=pd.read_csv(M.BASE/'stations.csv').set_index('id');p=ph[ph.phase.eq('P')&~ph.instrument_id.isin(held)&ph.instrument_id.isin(original_st.index)]
 present={k:set(g.instrument_id) for k,g in p.groupby('event_id')};strong={k:set(g.loc[g.probability.ge(.7),'instrument_id']) for k,g in p.groupby('event_id')};pairs=pd.read_csv(GRAPH/'inputs/differential_times.csv')[['event_id_a','event_id_b']].drop_duplicates();proposals=[]
 for ea,eb in pairs.itertuples(index=False,name=None):
  for seed,query in [(ea,eb),(eb,ea)]:
   for instrument in sorted(strong.get(seed,set())-present.get(query,set())):proposals.append(dict(event_id=query,instrument_id=instrument,seed_event_id=seed))
 proposals=pd.DataFrame(proposals);queries=proposals[['event_id','instrument_id']].drop_duplicates().sort_values(['instrument_id','event_id']);assert not queries.empty
 reserve=set(pd.read_csv(HERE/'docs/optimization_reserved_events_v3.csv').event_id);assert not set(e.event_id)&reserve and set(queries.event_id)<=set(e.event_id)
 gridfiles=[M.BASE/'grids'/f'time.P.{original_st.loc[sid,"nll_station"]}.time.{suffix}' for sid in queries.instrument_id.unique() for suffix in ['hdr','buf']]
 files=[Path(__file__),Path(Q.__file__),SRC/'design.json',SRC/'qualification.json',SRC/'target_design.json',SRC/'inputs/all_phases.csv',SRC/'inputs/events.csv',SRC/'cc_measurements.csv',GRAPH/'inputs/differential_times.csv',HERE/'docs/optimization_reserved_events_v3.csv',HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',HERE/'export/10_validate_catalog/events.csv',M.BASE/'stations.csv',HERE/'export/12_relative_location_pilot/run.json']+gridfiles
 design={'round':23,'intervention':'Add direct DPP P observations only where an existing training instrument lacks any associated P and at least one original stage39 neighbor has a PhaseNet P probability>=0.7 at that instrument. Keep stage42 observations and all 300 targets/2581 supports. No template-transfer times, stage43 measurements, new events, source reassignment or replacement of old picks.','picker':'Exactly stage42 single-component raw-Z inference and fixed waveform gates, qualified on disjoint existing P observations across these receiver families. Compatibility on observed P is not proof of validity on missing-P data; target association and full fixed held-location evaluation remain required.','association':'Centers from original v1 origins/1D TIME fields. Require the originally queried event to be the closest predicted P among ALL6520 v1 events within1s; second-best residual margin>=0.2s. Reject all different-event accepted onsets within0.100001s at one instrument. A missing old pick is never replaced by a model arrival.','cc':'Existing event graph only. Add scalar P edges with at least one newly admitted direct pick; the other endpoint must be a newly admitted pick or existing P probability>=0.7. Historical CC rows unchanged. No imported template-transfer measurement.','errors':'New direct P pick error0.20s plus original model error0.30s; stage42 new-P error retained; old P/S and CC Huber unchanged. DPP step scores separate from PhaseNet probability.','evaluation':'16 matched absolute/joint solves; same original targets/auxiliary eligibility/held stations and all original gates. Score old575 and1408 held CC against stage42 (ratio<=1.05); reference medians <=1.10 stage42 AND stage39. Reserve3 unopened. No gate relaxation if failed.','n_queries':len(queries),'n_instruments':queries.instrument_id.nunique(),'n_query_events':queries.event_id.nunique(),'n_neighbor_proposals':len(proposals),'source_sha256':{str(f):M.sha(f) for f in files}}
 dest=OUT/'target_design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 proposals.to_csv(OUT/'neighbor_proposals.csv',index=False);queries.to_csv(OUT/'requested_missing_p.csv',index=False)
 all_events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv');all_events=all_events[all_events.in_v1_working_catalog].copy();assert len(all_events)==6520;origins=pd.to_datetime(all_events.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9;metadata=pd.read_csv(HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',keep_default_na=False);competition=[];jobs=[]
 for instrument,g in queries.groupby('instrument_id'):
  station=original_st.loc[instrument];tt=origins+predict(all_events,station);table=pd.DataFrame({'event_id':all_events.event_id,'instrument_id':instrument,'predicted_epoch_s':tt});competition.append(table);selected=table[table.event_id.isin(g.event_id)];assert len(selected)==len(g)
  requests=[dict(pick_id='mp44_'+instrument.replace('.','_')+'_'+r.event_id,event_id=r.event_id,predicted_utc=pd.Timestamp(r.predicted_epoch_s,unit='s',tz='UTC').isoformat()) for r in selected.itertuples()];files=metadata[metadata.seed_id.eq(instrument+'Z')];assert len(files)==3;jobs.append((instrument,requests,files.to_dict('records')))
 pd.concat(competition).to_csv(OUT/'competition_predictions.csv',index=False);print({k:design[k] for k in ['n_queries','n_instruments','n_query_events','n_neighbor_proposals']},flush=True)
 return sorted(jobs,key=lambda j:len(j[1]),reverse=True)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=16);args=parser.parse_args();jobs=prepare();results=[];arrays={}
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn'),initializer=initialize) as pool:
  for n,f in enumerate(as_completed([pool.submit(pick_job,j) for j in jobs]),1):
   rows,data=f.result();results.extend(rows);arrays.update(data);print('Completed instrument',n,'/',len(jobs),'waveform-qualified',sum(r['accepted'] for r in rows),'/',len(rows),flush=True)
 q=pd.DataFrame(results).sort_values(['instrument_id','event_id']);q['waveform_accepted']=q.accepted;competition=pd.read_csv(OUT/'competition_predictions.csv')
 for instrument,g in q[q.accepted].groupby('instrument_id'):
  other=competition[competition.instrument_id.eq(instrument)].sort_values('predicted_epoch_s');times=other.predicted_epoch_s.to_numpy();ids=other.event_id.to_numpy()
  for index,row in g.iterrows():
   time=float(pd.Timestamp(row.candidate_utc).timestamp());lo,hi=np.searchsorted(times,[time-1,time+1]);residual=abs(times[lo:hi]-time);order=np.argsort(residual)
   if len(order)==0 or ids[lo+order[0]]!=row.event_id:q.loc[index,['accepted','reason']]=[False,'closer_competing_event'];continue
   if len(order)>1 and residual[order[1]]-residual[order[0]]<.2:q.loc[index,['accepted','reason']]=[False,'ambiguous_competing_event']
  remaining=q[q.accepted&q.instrument_id.eq(instrument)].copy();remaining['epoch']=remaining.candidate_utc.map(lambda v:float(pd.Timestamp(v).timestamp()));remaining=remaining.sort_values('epoch');near=remaining.epoch.diff().le(.100001)|remaining.epoch.diff(-1).abs().le(.100001);q.loc[remaining.index[near],['accepted','reason']]=[False,'duplicate_close_onsets']
 q.to_csv(OUT/'missing_p_candidates.csv',index=False);np.savez_compressed(OUT/'missing_p_windows.npz',**arrays);rows=[]
 for r in q[q.accepted].itertuples():
  station=r.instrument_id.split('.');rows.append(dict(pick_id=r.pick_id,station_id='.'.join(station[:2]),location=station[2],channel_family=station[3],phase='P',time_utc=r.candidate_utc,probability=np.nan,source_channels=r.source_seed_id,instrument_id=r.instrument_id,event_id=r.event_id,association_status='conditional_unambiguous',pick_method='DPP_SCEDC_vertical_step',picker_score=r.post_step_score,pick_error_s=.2))
 new=pd.DataFrame(rows,columns=['pick_id','station_id','location','channel_family','phase','time_utc','probability','source_channels','instrument_id','event_id','association_status','pick_method','picker_score','pick_error_s']);new.to_csv(OUT/'new_picks.csv',index=False);old=pd.read_csv(SRC/'inputs/all_phases.csv',low_memory=False);assert not len(new.merge(old[old.phase.eq('P')],on=['event_id','instrument_id']));combined=pd.concat([old,new],ignore_index=True);assert combined.pick_id.is_unique;combined.to_csv(OUT/'inputs/all_phases.csv',index=False);(OUT/'inputs/events.csv').write_bytes((SRC/'inputs/events.csv').read_bytes())
 M.save(OUT/'extraction_summary.json',{'requested':len(q),'waveform_accepted':int(q.waveform_accepted.sum()),'admitted_after_association':len(new),'station_counts':new.instrument_id.value_counts().to_dict(),'new_S_observations':0,'old_phase_rows':len(old),'all_phase_rows':len(combined),'rejections':q[~q.accepted].reason.value_counts().to_dict()})
 for f,h in json.loads((OUT/'target_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'extraction_summary.json').read_text(),flush=True)
if __name__=='__main__':main()
