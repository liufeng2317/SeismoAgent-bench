#!/usr/bin/env python3
"""Original NLL six-station omissions for eligible frozen reserve events."""
from pathlib import Path
import importlib.util,json
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2];ROOT=HERE/'export/34_joint_confirmation';OUT=ROOT/'native_controls'
spec=importlib.util.spec_from_file_location('native34',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py');S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S);S.OUT=OUT
OUT.mkdir(exist_ok=True);e=pd.read_csv(ROOT/'inputs/events.csv');e=e[e.role.eq('reserve')&e.auxiliary_eligible];assert len(e)==290
p=pd.read_csv(ROOT/'inputs/all_phases.csv',keep_default_na=False);p=p[p.event_id.isin(e.event_id)].copy();p['residual_s']=p.residual_s_gamma
cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text());st=pd.read_csv(S.BASE/'stations.csv').set_index('id');held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
files=[Path(__file__),Path(S.__file__),Path(S.NLL.__file__),ROOT/'design.json',ROOT/'inputs/events.csv',ROOT/'inputs/all_phases.csv',HERE/'00_config/nonlinloc.yaml',S.BASE/'stations.csv',Path(cfg['binary_directory'])/'NLLoc']
for eid in e.event_id:files.extend([S.BASE/'events_raw'/eid/'input.obs',S.BASE/'events_raw'/eid/'control.in'])
files+=sorted((S.BASE/'grids').glob('time.*.time.*'))
design={'n':290,'purpose':'Original model/errors/search, fixed six-station omission; no corrections. Same eligible reserve events as joint auxiliary scoring.','source_sha256':{str(f):S.sha(f) for f in files}}
f=OUT/'design.json'
if f.exists():assert json.loads(f.read_text())==design
else:S.write_json(f,design)
obs={eid:g.to_dict('records') for eid,g in p.groupby('event_id')};rows=[];links=[];fail=[]
with ThreadPoolExecutor(max_workers=8) as pool:
 jobs={pool.submit(S.solve,r,obs[r['event_id']],'withheld_control',{},st.nll_station.to_dict(),cfg,held):r['event_id'] for r in e.to_dict('records')}
 for i,future in enumerate(as_completed(jobs),1):
  try:r,l=future.result();rows.append(r);links.extend(l)
  except Exception as exc:fail.append({'event_id':jobs[future],'error':repr(exc)});print('FAILED',fail[-1],flush=True)
  if i%25==0 or i==len(jobs):print('Native controls',i,len(jobs),'failures',len(fail),flush=True)
pd.DataFrame(rows).to_csv(OUT/'events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'fit_phases.csv',index=False);pd.DataFrame(fail,columns=['event_id','error']).to_csv(OUT/'failures.csv',index=False)
for f,h in design['source_sha256'].items():assert S.sha(f)==h
assert not fail and len(rows)==290 and all(r['status']=='LOCATED' for r in rows)
expected=p[~p.instrument_id.isin(held)];fit=pd.DataFrame(links);assert set(fit.pick_id)==set(expected.pick_id) and fit.pick_id.is_unique
print('All native controls and pick identities verified.',flush=True)
