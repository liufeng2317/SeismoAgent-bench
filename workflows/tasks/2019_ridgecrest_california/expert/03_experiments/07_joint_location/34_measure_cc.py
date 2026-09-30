#!/usr/bin/env python3
"""Measure frozen edges; explicitly retain historical window-boundary exclusions."""
from pathlib import Path
import importlib.util,json,hashlib
import pandas as pd
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/34_joint_confirmation';INPUT=OUT/'inputs';WORK=OUT/'cc_processing';WORK.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('cc34',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=pd.read_csv(INPUT/'picks.csv');e=pd.read_csv(INPUT/'differential_times.csv');t=pd.to_datetime(p.time_utc,utc=True,format='ISO8601');safe=(t>=pd.Timestamp('2019-07-04T00:00:10Z'))&(t<pd.Timestamp('2019-07-06T23:59:50Z'));bad=set(p.loc[~safe,'pick_id']);mask=~e.pick_id_a.isin(bad)&~e.pick_id_b.isin(bad)
p[safe].to_csv(WORK/'picks.csv',index=False);e[mask].to_csv(WORK/'differential_times.csv',index=False)
pd.DataFrame({'cc_processing_edge_index':range(int(mask.sum())),'frozen_edge_index':e.index[mask]}).to_csv(WORK/'edge_index_map.csv',index=False)
p.loc[~safe,['pick_id','event_id','time_utc']].to_csv(WORK/'boundary_picks.csv',index=False)
files=[Path(__file__),Path(m.__file__),INPUT/'picks.csv',INPUT/'differential_times.csv'];design={'reason':'Historical extractor demands 10 s padding within case time bounds. Unsupported windows are not a claim of absent archived waveforms. Original graph/absolute inputs preserved; no new pairing or substitute picks.','n_boundary_picks':len(bad),'n_unsupported_edges':int((~mask).sum()),'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
f=WORK/'design.json'
if f.exists():assert json.loads(f.read_text())==design
else:f.write_text(json.dumps(design,indent=2)+'\n')
print(json.dumps(design,indent=2),flush=True)
m.PRE=WORK;m.OUT=WORK;m.prepare_cc()
a=pd.read_csv(WORK/'cc_measurements.csv');a.index=e.index[mask];b=e[~mask].copy();b['accepted']=False;b['reason']='outside_historical_padded_window';b['lag_s']=float('nan');b['cc']=float('nan');b['cc_arrival_difference_s']=float('nan');result=pd.concat([a,b]).sort_index();assert len(result)==len(e)
for col in ['event_id_a','event_id_b','pick_id_a','pick_id_b']:assert result[col].equals(e[col])
result.to_csv(OUT/'cc_measurements.csv',index=False)
for f,h in design['source_sha256'].items():assert hashlib.sha256(Path(f).read_bytes()).hexdigest()==h
print('Completed frozen graph including',len(b),'explicit unsupported edges.',flush=True)
