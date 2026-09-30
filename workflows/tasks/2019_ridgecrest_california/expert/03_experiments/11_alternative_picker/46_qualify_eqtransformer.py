#!/usr/bin/env python3
"""Qualify a fixed independent EQTransformer inference recipe before target admission."""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
from pathlib import Path
import argparse,importlib.util,hashlib,json,sys,multiprocessing,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
from obspy import read,Stream,UTCDateTime
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/46_alternative_picker';DIR=Path(__file__).resolve().parent
LIB=HERE.parents[2].parent/'TRACE-1.1/seismoagent/library';WAVE=HERE.parents[2]/'data/2019_ridgecrest_california/data/waveforms'
WEIGHTS=LIB/'ai_module/phase_picking/pretrained/v3/eqtransformer/original_nonconservative.pt.v1';META=WEIGHTS.with_name('original_nonconservative.json.v1');MODEL=None

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
P=load('prepare46',HERE/'01_pipeline/02_pick_phasenet.py');M=load('engine46',HERE/'03_experiments/07_joint_location/33_joint_location.py')

def initialize():
 global MODEL
 os.environ['SEISBENCH_CACHE_ROOT']=str(OUT/'cache');sys.path.insert(0,str(LIB/'ai_module'))
 import torch
 from phase_picking.model.eqtransformer import EQTransformer
 torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.manual_seed(0);np.random.seed(0);torch.use_deterministic_algorithms(True)
 meta=json.loads(META.read_text());MODEL=EQTransformer(**meta['model_args']);w=torch.load(WEIGHTS,map_location='cpu',weights_only=True);MODEL.load_state_dict(w.get('state_dict',w),strict=True);MODEL.default_args.update(meta.get('default_args',{}));MODEL.eval()
 assert MODEL.sampling_rate==100 and MODEL.in_samples==6000 and MODEL.phases=='PS'

def job(work):
 import torch
 instrument,requests,files=work;began=time.monotonic();cache={}
 for r in files:
  f=WAVE/r['path'];assert f.stat().st_size==int(r['bytes']);cache[str(f)]=read(str(f))
 def cached(path,starttime,endtime):
  return Stream([tr.slice(starttime,endtime,nearest_sample=False).copy() for tr in cache[str(path)] if tr.stats.endtime>=starttime and tr.stats.starttime<=endtime])
 P.read=cached;results=[]
 for request in requests:
  row=dict(request,instrument_id=instrument,accepted=False,reason='missing_contiguous_window');center=UTCDateTime(float(pd.Timestamp(request['predicted_utc']).timestamp()));phase=request['phase'];gate={'P':1.,'S':1.2}[phase];candidate=[]
  for offset in [-5.,5.]:
   try:st,_,_=P.prepare(files,WAVE,center-45+offset,center+45+offset)
   except (ValueError,AssertionError):break
   # Two real 90 s contexts; only the central association interval is admitted.
   assert all(t.stats.sampling_rate==100 and abs(t.stats.delta-.01)<1e-12 for t in st)
   with torch.inference_mode():
    annotations=MODEL.annotate(st,strict=True,flexible_horizontal_components=False,batch_size=8)
    output=MODEL.classify_aggregate(annotations,dict(MODEL.default_args,P_threshold=.3,S_threshold=.3,detection_threshold=.3))
   picks=[p for p in output.picks if p.phase==phase and abs(p.peak_time-center)<=gate]
   if not picks:row['reason']='no_qualified_peak';break
   pick=sorted(picks,key=lambda p:(-p.peak_value,float(p.peak_time)))[0]
   detection=annotations.select(channel='EQTransformer_Detection');scores=[]
   for tr in detection:
    i=round((pick.peak_time-tr.stats.starttime)*tr.stats.sampling_rate)
    if 0<=i<len(tr) and np.isfinite(tr.data[i]):scores.append(float(tr.data[i]))
   if not scores or max(scores)<.3:row['reason']='low_detection_at_pick';break
   candidate.append((float(pick.peak_time),float(pick.peak_value),max(scores)))
  if len(candidate)==2:
   first,second=candidate;row.update(candidate_utc=str(UTCDateTime(first[0])),phase_score=min(first[1],second[1]),detection_score=min(first[2],second[2]),context_difference_s=second[0]-first[0],model_residual_s=first[0]-float(center))
   stable=abs(second[0]-first[0])<=({'P':.1,'S':.2}[phase]+1e-6);row['accepted']=bool(stable);row['reason']='accepted' if stable else 'context_instability'
   if 'reference_pick_utc' in request:row['difference_from_existing_pick_s']=first[0]-pd.Timestamp(request['reference_pick_utc']).timestamp()
  results.append(row)
 print(instrument,len(results),'queries',sum(r['accepted'] for r in results),'accepted',round(time.monotonic()-began,1),'seconds',flush=True)
 return results

def freeze(path,data):
 if path.exists():assert json.loads(path.read_text())==data,f'Frozen design changed: {path}'
 else:M.save(path,data)

def prepare():
 OUT.mkdir(exist_ok=True);(OUT/'qualification_chunks').mkdir(exist_ok=True)
 p=M.Problem();tt,_=p.prediction(p.start.ravel());ph=p.p.copy();ph['predicted_utc']=pd.to_datetime(p.t0[p.ei]+tt,unit='s',utc=True).astype(str);ph=ph[ph.probability.ge(.7)].copy()
 ph['hash']=ph.pick_id.map(lambda s:hashlib.sha256(('eqt46:'+s).encode()).hexdigest());ph=ph.sort_values('hash').groupby(['instrument_id','phase'],sort=True).head(20).sort_values(['instrument_id','phase','pick_id'])
 target=pd.read_csv(HERE/'export/45_added_station/inputs/events.csv');reserve=pd.read_csv(HERE/'docs/optimization_reserved_events_v3.csv');assert not set(ph.event_id)&(set(target.event_id)|set(reserve.event_id))
 manifest=HERE/'export/01_prepare_inputs/full/waveform_inputs.csv';inventory=pd.read_csv(manifest,keep_default_na=False);jobs=[]
 for instrument,g in ph.groupby('instrument_id'):
  seeds={s for v in g.source_channels for s in v.split(';')};files=inventory[inventory.seed_id.isin(seeds)];assert len(files)>0 and files.component.nunique()==3 and files.sample_rate_hz.astype(float).eq(100).all()
  requests=[dict(query_id=r.pick_id,event_id=r.event_id,phase=r.phase,predicted_utc=r.predicted_utc,reference_pick_utc=r.time_utc,existing_probability=float(r.probability)) for r in g.itertuples()];jobs.append((instrument,requests,files.to_dict('records')))
 files=[Path(__file__),Path(P.__file__),Path(M.__file__),WEIGHTS,META,LIB/'ai_module/phase_picking/model/eqtransformer.py',LIB/'ai_module/phase_picking/model/base.py',manifest,HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/45_added_station/inputs/events.csv',HERE/'docs/optimization_reserved_events_v3.csv']+p.gridfiles
 design={'round':25,'intervention':'Alternative direct P/S picker for missing observations, not replacement or averaging of old picks. Qualification first; no target waveform requests before it passes.','model':'Local original_nonconservative v1 EQTransformer: published original weights, not the conservative variant. No weight/threshold scan. Strict local state_dict and deterministic CPU inference.','source_paper':'https://www.nature.com/articles/s41467-020-17591-w','implementation_documentation':'https://seisbench.readthedocs.io/en/latest/pages/documentation/models/waveform_models.html#eqtransformer','inference':'Real simultaneous three components, StationXML rotation, original100Hz. Metadata-specified1–45Hz bandpass and model normalization/taper. Each conditional query is independently inferred in two90s contexts centered5s before/after original predicted arrival. Original annotate overlap/blinding retained. Candidate is highest phase peak>=0.3 within P±1/S±1.2s, with detection score>=0.3 at peak; require context agreement<=0.1P/0.2S; retain first-context time. No gap fill, reference onset input or forced fallback.','selection':'At most20 high-confidence original observations per instrument/phase, deterministic hash on old147-event cohort; disjoint from all current targets/supports and reserve3. Predictions use original locations, which did use these original labels; compatibility, not independent ground truth. Existing picks are supplied only to post-inference scoring.','qualification_gates':{'per_phase_min_examples':200,'per_phase_min_instruments':20,'per_phase_accepted_fraction_min':.5,'P_median_abs_s_max':.1,'P_p90_abs_s_max':.25,'P_abs_median_signed_s_max':.05,'S_median_abs_s_max':.15,'S_p90_abs_s_max':.3,'S_abs_median_signed_s_max':.1},'target_policy_if_qualified':'Unchanged stage45 event cohort and old observations. Query only missing event/instrument/phase cells at original three-component TRAINING receivers. Same fixed inference recipe. Associate against all original6520 v1 competitors with nearest-event margin>=0.2s; reject different-event old/new onsets within0.100001s and S<=P. New P/S pick errors0.2/0.3s plus original model0.3s. Same stage39 pair graph and waveform CC rules, original model and16 matched solves, all unchanged coverage/boundary/reference/held/anchor gates, fixed old575/1408 measurements. Reserve3 remains unused.','limitations':'Automated reference picks are not manual truth. Training overlap of published weights with these data has not been established. Prediction-centered inference can miss arrivals biased by the current model; successful qualification only licenses a target experiment.','source_sha256':{str(f):M.sha(f) for f in files},'n_examples':len(ph),'n_events':ph.event_id.nunique()}
 freeze(OUT/'design.json',design);ph.to_csv(OUT/'qualification_inputs.csv',index=False)
 return jobs

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);args=ap.parse_args();jobs=prepare();allrows=[];pending=[]
 for work in jobs:
  path=OUT/'qualification_chunks'/(work[0]+'.json')
  if path.exists():allrows.extend(json.loads(path.read_text()))
  else:pending.append(work)
 print('Qualification jobs',len(jobs),'pending',len(pending),flush=True)
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn'),initializer=initialize) as pool:
  futures={pool.submit(job,j):j[0] for j in pending}
  for future in as_completed(futures):
   rows=future.result();M.save(OUT/'qualification_chunks'/(futures[future]+'.json'),rows);allrows.extend(rows)
 table=pd.DataFrame(allrows).sort_values(['instrument_id','phase','query_id']);table.to_csv(OUT/'qualification_results.csv',index=False);metrics={};gates={}
 for phase,g in table.groupby('phase'):
  a=g[g.accepted];d=a.difference_from_existing_pick_s;metrics[phase]={'n':len(g),'instruments':g.instrument_id.nunique(),'accepted':len(a),'accepted_fraction':len(a)/len(g),'median_abs_difference_s':float(d.abs().median()) if len(a) else None,'p90_abs_difference_s':float(d.abs().quantile(.9)) if len(a) else None,'median_signed_difference_s':float(d.median()) if len(a) else None,'rejections':g[~g.accepted].reason.value_counts().to_dict()}
  gates[phase+'_size']=len(g)>=200 and g.instrument_id.nunique()>=20;gates[phase+'_coverage']=len(a)>=.5*len(g);gates[phase+'_timing']=bool(len(a) and d.abs().median()<={'P':.1,'S':.15}[phase] and d.abs().quantile(.9)<={'P':.25,'S':.3}[phase] and abs(d.median())<={'P':.05,'S':.1}[phase])
 result={'round':25,'qualification_metrics':metrics,'qualification_gates':gates,'decision':'qualified_for_target_extraction' if all(gates.values()) else 'do_not_add_eqt_observations','new_target_picks_added':0,'full_catalog_adopted':False};M.save(OUT/'qualification.json',result)
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
