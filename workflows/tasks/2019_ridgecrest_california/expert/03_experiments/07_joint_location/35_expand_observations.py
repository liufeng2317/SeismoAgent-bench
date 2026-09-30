#!/usr/bin/env python3
"""One fixed intervention: remove model-residual filtering of CC candidates."""
from pathlib import Path
import importlib.util,hashlib,json,shutil
import pandas as pd
HERE=Path(__file__).resolve().parents[2];SRC=HERE/'export/34_joint_confirmation';OUT=HERE/'export/35_cc_observation_selection';INPUT=OUT/'inputs';WORK=OUT/'cc_processing'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 INPUT.mkdir(parents=True,exist_ok=True);WORK.mkdir(exist_ok=True)
 p=pd.read_csv(SRC/'inputs/all_phases.csv');q=p[p.probability.ge(.5)].copy();q=q[~q.duplicated(['event_id','instrument_id','phase'],keep=False)];q['key']=q.instrument_id+':'+q.phase
 lookup={eid:g.set_index('key') for eid,g in q.groupby('event_id')};pairs=pd.read_csv(SRC/'inputs/pair_status.csv');held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']);rows=[]
 for a,b in pairs[['event_id_a','event_id_b']].itertuples(index=False,name=None):
  aa=lookup.get(a);bb=lookup.get(b);keys=[] if aa is None or bb is None else sorted(set(aa.index)&set(bb.index))
  if len(keys)<6 or len({k.split(':')[0] for k in keys})<4:continue
  for key in keys:
   x,y=aa.loc[key],bb.loc[key];rows.append(dict(event_id_a=a,event_id_b=b,pick_id_a=x.pick_id,pick_id_b=y.pick_id,instrument_id=x.instrument_id,phase=x.phase,observed_dt_s=(pd.Timestamp(x.time_utc)-pd.Timestamp(y.time_utc)).total_seconds(),training=x.instrument_id not in held))
 edges=pd.DataFrame(rows);ids=set(edges.pick_id_a)|set(edges.pick_id_b);pick=p[p.pick_id.isin(ids)].copy();t=pd.to_datetime(pick.time_utc,utc=True,format='ISO8601');safe=(t>=pd.Timestamp('2019-07-04T00:00:10Z'))&(t<pd.Timestamp('2019-07-06T23:59:50Z'));bad=set(pick.loc[~safe,'pick_id']);mask=~edges.pick_id_a.isin(bad)&~edges.pick_id_b.isin(bad)
 files=[Path(__file__),SRC/'design.json',SRC/'inputs/events.csv',SRC/'inputs/all_phases.csv',SRC/'inputs/pair_status.csv',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py',HERE/'export/33_joint_location/frozen_candidate.json']
 design={'round':14,'intervention':'Remove only NLL absolute-residual <=0.5 s prefilter before CC. Keep probability >=0.5, pair common-phase/station requirements, frozen neighbor pairs, waveform quality thresholds, 50 ms CC error, absolute model/errors and solver unchanged.','cohort':'Exposed stage34 300 targets +1970 supports, now DEVELOPMENT ONLY. No independent confirmation claim. No new neighbor selection.','n_candidate_edges':len(edges),'n_boundary_excluded':int((~mask).sum()),'selection_gates':'Apply stage34 coverage, prediction, reference, boundary and start-stability criteria without relaxing them. Compare on identical held observations; report old/new CC intersection separately from expanded set. Even passing permits only a fresh confirmation, never full adoption. No further cutoff/probability/CC threshold scans.','source_sha256':{str(f):sha(f) for f in files}}
 f=OUT/'design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:f.write_text(json.dumps(design,indent=2)+'\n')
 for name in ['events.csv','all_phases.csv']:
  target=INPUT/name
  if target.exists():assert target.read_bytes()==(SRC/'inputs'/name).read_bytes()
  else:shutil.copy2(SRC/'inputs'/name,target)
 for target,frame in [(INPUT/'differential_times.csv',edges),(INPUT/'picks.csv',pick),(WORK/'differential_times.csv',edges[mask]),(WORK/'picks.csv',pick[safe])]:
  data=frame.to_csv(index=False)
  if target.exists():assert target.read_text()==data
  else:target.write_text(data)
 pd.DataFrame({'cc_processing_edge_index':range(int(mask.sum())),'frozen_edge_index':edges.index[mask]}).to_csv(WORK/'edge_index_map.csv',index=False);pick[~safe].to_csv(WORK/'boundary_picks.csv',index=False)
 (WORK/'design.json').write_text(json.dumps({'parent_design_sha256':sha(OUT/'design.json'),'boundary_handling':'Same historical 10-second case padding; explicit unsupported edges retained.'},indent=2)+'\n')
 (OUT/'README.md').write_text('# Round14: model-independent CC candidate eligibility\n\nDevelopment experiment on the already-exposed stage34 cohort. Only the old absolute-residual CC prefilter is removed. All probability, waveform, pairing, weighting and location criteria stay fixed. More candidates do not imply more valid CC or better depth. No original catalog or previous output is replaced.\n\n```json\n'+json.dumps({k:v for k,v in design.items() if k!='source_sha256'},indent=2)+'\n```\n\nStatus: waveform measurement running; no outcome available. This cohort cannot be relabeled independent confirmation.\n')
 print(json.dumps({k:v for k,v in design.items() if k!='source_sha256'},indent=2),flush=True)
 spec=importlib.util.spec_from_file_location('cc35',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.PRE=WORK;m.OUT=WORK;m.prepare_cc()
 result=pd.read_csv(WORK/'cc_measurements.csv');result.index=edges.index[mask];excluded=edges[~mask].copy();excluded['accepted']=False;excluded['reason']='outside_historical_padded_window'
 for col in ['lag_s','cc','cc_arrival_difference_s']:excluded[col]=float('nan')
 result=pd.concat([result,excluded]).sort_index();assert len(result)==len(edges)
 for col in ['event_id_a','event_id_b','pick_id_a','pick_id_b']:assert result[col].equals(edges[col])
 result.to_csv(OUT/'cc_measurements.csv',index=False)
 for f,h in design['source_sha256'].items():assert sha(Path(f))==h
 print('Expanded observation measurement complete.',flush=True)
if __name__=='__main__':main()
