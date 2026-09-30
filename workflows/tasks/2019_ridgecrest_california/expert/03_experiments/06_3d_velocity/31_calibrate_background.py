#!/usr/bin/env python3
"""Development-only nearest-station S-P selection among three frozen backgrounds."""
from pathlib import Path
import importlib.util,sys,json,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2];ROOT=HERE/'export/31_background_calibration';OUT=ROOT/'development';BASE=HERE/'export/04_locate_nonlinloc'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
C=load('crop_calibration31',Path(__file__).with_name('_cropped_times.py'))
S=load('native_calibration31',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
MODELS=['original','local_background','regional','midpoint']
def prepare():
 OUT.mkdir(parents=True,exist_ok=True)
 cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text());e=pd.read_csv(HERE/'export/12_relative_location_pilot/events.csv');p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False);p=p[p.event_id.isin(e.event_id)].copy();p['residual_s']=p.residual_s_gamma
 st=pd.read_csv(BASE/'stations.csv').set_index('id');selection=pd.read_csv(ROOT/'development_holdouts.csv');sel=json.loads((ROOT/'selection_design.json').read_text());assert C.sha(ROOT/'development_holdouts.csv')==sel['csv_sha256']
 assert len(e)==144 and set(e.event_id)==set(selection.event_id) and int(selection.eligible.sum())==138
 assert not p.duplicated(['event_id','instrument_id','phase']).any()
 files=[Path(__file__),Path(C.__file__),Path(S.__file__),Path(S.NLL.__file__),Path(S.DIAG.__file__),ROOT/'selection_design.json',ROOT/'development_holdouts.csv',ROOT/'grid_design.json',ROOT/'crop_check/run.json',HERE/'00_config/nonlinloc.yaml',HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/10_validate_catalog/phases.csv',BASE/'stations.csv',Path(cfg['binary_directory'])/'NLLoc']
 for eid in e.event_id:files.extend([BASE/'events_raw'/eid/'control.in',BASE/'events_raw'/eid/'input.obs'])
 design=dict(round=11,scope='Development calibration only; does not open transfer references or either confirmation outcome set.',selection_design=sel['design'],models=MODELS,expected_new_fits=552,gates='All 4x138 fits must LOCATE; identical remaining/held pick identities and native timing equations. Midpoint S-P RMS strictly lower than both endpoints and <=0.95 original control. Otherwise close calibration without alpha scans.',source_sha256={str(f):C.sha(f) for f in files})
 path=OUT/'design.json'
 if path.exists():assert json.loads(path.read_text())==design
 else:C.write_json(path,design)
 return cfg,e,p,st,selection

def verify_cache(st):
 assert json.loads((ROOT/'grid_run.json').read_text())['complete']
 verified=[]
 for model in MODELS[1:]:
  folder=ROOT/'crop_check/grids'/model
  for sid in st.nll_station:
   for phase in ['P','S']:
    buf=folder/f'time.{phase}.{sid}.time.buf';meta=json.loads(buf.with_suffix('.crop.json').read_text());assert C.sha(buf)==meta['cropped_sha256'] and C.sha(buf.with_suffix('.hdr'))==meta['cropped_header_sha256'];verified.append(dict(model=model,phase=phase,station=sid,sha256=meta['cropped_sha256']))
 pd.DataFrame(verified).to_csv(OUT/'verified_grids.csv',index=False)
 print('Verified',len(verified),'cropped grids.',flush=True)

def predict(model,p,st):
 if model=='original':return S.DIAG.predict(BASE/'grids',p,st)[0]
 return C.predict(ROOT/'crop_check/grids'/model,p,st)

def run(data,workers):
 cfg,e,p,st,selection=data;verify_cache(st)
 eligible=selection[selection.eligible].set_index('event_id');events=e[e.event_id.isin(eligible.index)];obs={eid:q.to_dict('records') for eid,q in p.groupby('event_id')};rows=[];links=[];failures=[]
 S.OUT=OUT;S.write_json=C.write_json
 for model in MODELS:
  if model=='original':S.BASE=BASE
  else:
   proxy=OUT/('input_'+model);proxy.mkdir(exist_ok=True)
   for name,target in [('events_raw',BASE/'events_raw'),('grids',ROOT/'crop_check/grids'/model)]:
    link=proxy/name
    if not link.exists():link.symlink_to(target,target_is_directory=True)
    assert link.resolve()==target.resolve()
   S.BASE=proxy
  with ThreadPoolExecutor(max_workers=workers) as pool:
   jobs={pool.submit(S.solve,event,obs[event['event_id']],model,{},st.nll_station.to_dict(),cfg,[eligible.loc[event['event_id'],'held_instrument']]):event['event_id'] for event in events.to_dict('records')}
   for i,f in enumerate(as_completed(jobs),1):
    try:r,l=f.result();rows.append(r);links.extend(l)
    except Exception as exc:failures.append(dict(model=model,event_id=jobs[f],error=repr(exc)));print('FAILED',failures[-1],flush=True)
    if i%30==0 or i==len(jobs):print(model,i,len(jobs),'failures',len(failures),flush=True)
  pd.DataFrame(rows).to_csv(OUT/'events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'fit_phases.csv',index=False);pd.DataFrame(failures,columns=['model','event_id','error']).to_csv(OUT/'failures.csv',index=False)
 assert not failures and len(rows)==552

def report(data):
 cfg,events,p,st,selection=data;e=pd.read_csv(OUT/'events.csv');fit=pd.read_csv(OUT/'fit_phases.csv');assert len(e)==552 and e.status.eq('LOCATED').all() and not e.duplicated(['branch','event_id']).any()
 sel=selection[selection.eligible].set_index('event_id');scores=[];held=[];timing=[]
 for model in MODELS:
  a=e[e.branch.eq(model)].set_index('event_id');f=fit[fit.branch.eq(model)]
  assert set(a.index)==set(sel.index)
  expected=p[p.event_id.isin(sel.index)].copy();expected['held_instrument']=expected.event_id.map(sel.held_instrument);expected=expected[expected.instrument_id!=expected.held_instrument]
  assert set(f.pick_id)==set(expected.pick_id) and f.pick_id.is_unique
  q=f.merge(p[['pick_id','time_utc']],on='pick_id',validate='one_to_one').merge(a.reset_index()[['event_id','origin_time']+S.XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
  tt=predict(model,q,st);elapsed=(pd.to_datetime(q.time_utc,utc=True,format='ISO8601')-pd.to_datetime(q.origin_time,utc=True,format='ISO8601')).dt.total_seconds()
  err=float(np.max(np.abs(elapsed-tt-q.residual_s)));assert err<.00035
  timing.append(dict(model=model,max_residual_equation_error_s=err))
  ids=set(sel.P_pick_id)|set(sel.S_pick_id);h=p[p.pick_id.isin(ids)].merge(a.reset_index()[['event_id','origin_time']+S.XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
  assert len(h)==276 and set(h.pick_id)==ids
  h['predicted_tt_s']=predict(model,h,st);h['model']=model
  h['residual_s']=(pd.to_datetime(h.time_utc,utc=True,format='ISO8601')-pd.to_datetime(h.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-h.predicted_tt_s
  held.append(h)
  pair=h.pivot(index='event_id',columns='phase',values='predicted_tt_s').loc[sel.index]
  delta=pair.S-pair.P-sel.observed_SP_s
  for eid,value in delta.items():scores.append(dict(model=model,event_id=eid,predicted_SP_s=float(pair.loc[eid,'S']-pair.loc[eid,'P']),observed_SP_s=float(sel.loc[eid,'observed_SP_s']),error_s=float(value)))
 scores=pd.DataFrame(scores);metrics=[]
 for model,q in scores.groupby('model'):metrics.append(dict(model=model,n=len(q),SP_rms_s=float(np.sqrt(np.mean(q.error_s**2))),SP_median_abs_s=float(q.error_s.abs().median())))
 metrics=pd.DataFrame(metrics);m=metrics.set_index('model').SP_rms_s
 qualifies=bool(m.midpoint<min(m.local_background,m.regional) and m.midpoint<=.95*m.original)
 decision='midpoint_qualifies_for_existing_transfer_gates' if qualifies else 'close_background_calibration_no_scan'
 result=dict(round=11,stage='development_selection',decision=decision,n_input_events=144,n_eligible_events=138,new_fits=552,SP_rms_s=m.to_dict(),midpoint_to_original_ratio=float(m.midpoint/m.original),confirmation_reserve_used=False,full_catalog_adopted=False)
 scores.to_csv(OUT/'SP_predictions.csv',index=False);metrics.to_csv(OUT/'metrics.csv',index=False);pd.concat(held,ignore_index=True).to_csv(OUT/'heldout_predictions.csv',index=False);pd.DataFrame(timing).to_csv(OUT/'timing_checks.csv',index=False);C.write_json(OUT/'run.json',result)
 (OUT/'README.md').write_text('# Development-only background selection\n\nDecision: **'+decision+'**. All 552 fits preserve their frozen input/held phase identities and pass independent timing checks. Six ineligible events remain in development_holdouts.csv; no replacement.\n\n```text\n'+metrics.to_string(index=False,float_format=lambda x:f'{x:.5f}')+'\n```\n\nEach event withholds the closest paired P/S instrument selected from original coordinates. Predicted S-P cancels origin time; the fitted origin is also retained for separate absolute-arrival predictions. All score residuals are untrimmed. No references are read by the selection/report code. Passing permits the previously fixed transfer comparison, not confirmation or adoption. A failed selection closes this bounded family without new alpha values. The second confirmation reserve remains unused.\n')
 print(json.dumps(result,indent=2),flush=True)

def main():
 a=argparse.ArgumentParser();a.add_argument('--stage',choices=['prepare','run','report','all'],default='all');a.add_argument('--workers',type=int,default=8);args=a.parse_args()
 import fcntl
 OUT.mkdir(parents=True,exist_ok=True)
 with (OUT/'run.lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);data=prepare()
  if args.stage in ['run','all']:run(data,args.workers)
  if args.stage in ['report','all']:report(data)
if __name__=='__main__':main()
