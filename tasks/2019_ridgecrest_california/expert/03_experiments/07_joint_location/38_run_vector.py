#!/usr/bin/env python3
"""Keep stage37 robust locator unchanged; use joint-horizontal S measurements."""
from pathlib import Path
import importlib.util,json,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('robust38',DIR/'37_robust_cc.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
M=R.M;HERE=M.HERE;SRC=HERE/'export/37_robust_cc';OBS=HERE/'export/35_cc_observation_selection';OUT=HERE/'export/38_vector_s';R.OUT=OUT;R.C.OUT=OUT;R.C.INPUT=OUT/'inputs';R.ENGINE.OUT=OUT
problem=R.problem

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('--stage',choices=['prepare','run'],default='run');args=parser.parse_args()
 for name in ['inputs','native_controls']:R.ENGINE.link(OBS/name,OUT/name)
 old=pd.read_csv(OBS/'cc_measurements.csv');new=pd.read_csv(OUT/'cc_measurements.csv');assert len(old)==len(new)
 for col in ['event_id_a','event_id_b','pick_id_a','pick_id_b','phase','training']:assert old[col].equals(new[col])
 assert old[old.phase.eq('P')].equals(new[new.phase.eq('P')])
 files=[Path(__file__),Path(R.__file__),Path(R.C.__file__),Path(M.__file__),Path(R.ENGINE.__file__),OUT/'design.json',OUT/'cc_measurements.csv',OBS/'execution_design.json']
 for source,digest in json.loads((OBS/'execution_design.json').read_text())['source_sha256'].items():assert M.sha(Path(source))==digest
 design={'round':17,'only_change':'S measurements from frozen joint-horizontal algorithm. Exact stage37 Huber objective and stage34 solver settings. P and absolute observations unchanged.','source_sha256':{str(p):M.sha(p) for p in files}}
 f=OUT/'location_design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 for branch in ['absolute_all','absolute_withheld']:
  for label in (['control'] if branch=='absolute_all' else M.SHIFTS):
   for suffix in ['npz','json']:R.ENGINE.link(SRC/(branch+'_'+label+'.'+suffix),OUT/(branch+'_'+label+'.'+suffix))
 template=M.Problem();primary=problem(template,False);aux=problem(template,True);print('Events',len(primary.e),'accepted edges',len(primary.c),'auxiliary edges',len(aux.c),flush=True)
 if args.stage=='prepare':return
 jobs=[(primary,'joint_all','control',(0,0,0))]+[(aux,'joint_withheld',label,shift) for label,shift in M.SHIFTS.items()]
 states=[]
 for branch in ['absolute_all','absolute_withheld']:
  for label in (['control'] if branch=='absolute_all' else M.SHIFTS):states.append(json.loads((OUT/(branch+'_'+label+'.json')).read_text()))
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for f in as_completed([pool.submit(R.ENGINE.solve,job) for job in jobs]):states.append(f.result())
 pd.DataFrame(states).sort_values(['branch','start']).to_csv(OUT/'solver_status.csv',index=False)
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
if __name__=='__main__':main()
