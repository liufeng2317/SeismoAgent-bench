#!/usr/bin/env python3
"""Qualify conditional vertical-only DPP P picking before adding observations."""
from pathlib import Path
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:os.environ[name]='1'
import argparse,hashlib,importlib.util,json,sys,multiprocessing
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import pandas as pd
from obspy import read,Stream,UTCDateTime
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/42_vertical_p_observations'
LIB=HERE.parents[2].parent/'TRACE-1.1/seismoagent/library'
WAVE=HERE.parents[2]/'benchmark_source/2019_ridgecrest_california/data/waveforms'
WEIGHT=LIB/'ai_module/phase_picking/pretrained/v3/dpppickerp/scedc.pt'
META=WEIGHT.with_suffix('.json');MODEL=None
spec=importlib.util.spec_from_file_location('original42',HERE/'03_experiments/07_joint_location/33_joint_location.py');M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)

def initialize():
 global MODEL
 os.environ['SEISBENCH_CACHE_ROOT']=str(OUT/'cache');sys.path.insert(0,str(LIB/'ai_module'))
 import torch
 from phase_picking.model.dpppickerp import DPPPicker
 torch.set_num_threads(1);torch.set_num_interop_threads(1);torch.manual_seed(0);torch.use_deterministic_algorithms(True)
 MODEL=DPPPicker(mode='P');weights=torch.load(WEIGHT,map_location='cpu',weights_only=True);weights=weights.get('state_dict',weights);assert weights['lstm1.weight_ih_l0'].shape[1]==1;MODEL.load_state_dict(weights,strict=True);MODEL.eval()

def crossing(probability):
 indices=np.flatnonzero(probability>.5)
 return int(indices[0]) if len(indices) else None

def pick_job(job):
 import torch
 instrument,requests,files=job;stream=Stream();seeds={r['seed_id'] for r in files};assert len(seeds)==1;seed=next(iter(seeds))
 for row in files:
  path=WAVE/row['path'];assert path.stat().st_size==int(row['bytes']);assert float(row['sample_rate_hz'])==100;assert abs(abs(float(row['dip_deg']))-90)<.01
  stream+=read(str(path)).select(id=seed)
 stream.merge(method=-1);polarity=-np.sin(np.deg2rad(float(files[0]['dip_deg'])));windows=[];valid=[];results=[];arrays={}
 for request in requests:
  key=request['pick_id'];record=dict(request,accepted=False,reason='missing_contiguous_window',instrument_id=instrument,source_seed_id=seed)
  center=float(pd.Timestamp(request['predicted_utc']).timestamp());pieces=[]
  for trace in stream:
   j=round((center-6-float(trace.stats.starttime))*100)
   if j>=0 and j+1200<=len(trace):pieces.append((trace,j))
  if len(pieces)!=1:results.append(record);continue
  tr,j=pieces[0];a=tr.data[j:j+1200]
  if tr.stats.sampling_rate!=100 or np.ma.isMaskedArray(a) or not np.isfinite(a).all():record['reason']='invalid_samples';results.append(record);continue
  raw=np.asarray(a,dtype=np.float32)*polarity;start=float(tr.stats.starttime)+j/100;pair=np.stack([raw[:1000],raw[200:1200]]);pair-=pair.mean(axis=1,keepdims=True);scale=np.max(abs(pair),axis=1,keepdims=True)
  if (scale<=0).any():record['reason']='zero_signal';results.append(record);continue
  pair/=scale;windows.extend(pair[:,None,:]);valid.append((record,raw,start,center));arrays[key+'|waveform']=raw
 if windows:
  predictions=[]
  with torch.inference_mode():
   for begin in range(0,len(windows),32):predictions.extend(MODEL(torch.from_numpy(np.stack(windows[begin:begin+32]))).cpu().numpy())
  assert len(predictions)==2*len(valid)
  for n,(record,raw,start,center) in enumerate(valid):
   p0,p1=np.asarray(predictions[2*n]),np.asarray(predictions[2*n+1]);assert p0.shape==p1.shape==(1000,) and np.isfinite(p0).all() and np.isfinite(p1).all();key=record['pick_id'];arrays[key+'|probabilities']=np.stack([p0,p1]);i0,i1=crossing(p0),crossing(p1)
   record['waveform_start_utc']=str(UTCDateTime(start));record['reason']='no_threshold_crossing'
   if i0 is None or i1 is None:results.append(record);continue
   if not(100<=i0<900 and 100<=i1<900):record['reason']='window_edge_or_already_positive';results.append(record);continue
   t0=start+i0/100;t1=start+2+i1/100;record.update(candidate_utc=str(UTCDateTime(t0)),window_difference_s=t1-t0,model_residual_s=t0-center)
   pre=max(float(np.median(p0[i0-50:i0-10])),float(np.median(p1[i1-50:i1-10])));post=min(float(np.median(p0[i0+10:i0+50])),float(np.median(p1[i1+10:i1+50])));snr=float(np.std(raw[i0:i0+50])/max(float(np.std(raw[i0-200:i0-50])),1e-20)) if i0>=200 else 0.;record.update(pre_step_score=pre,post_step_score=post,snr=snr)
   reasons=[]
   if abs(t1-t0)>.100001:reasons.append('window_instability')
   if abs(t0-center)>1.:reasons.append('outside_association_gate')
   if pre>.2 or post<.8:reasons.append('weak_step_contrast')
   if snr<2:reasons.append('low_snr')
   record['accepted']=not reasons;record['reason']=';'.join(reasons) or 'accepted'
   if 'reference_pick_utc' in record:record['difference_from_existing_P_s']=t0-float(pd.Timestamp(record['reference_pick_utc']).timestamp())
   results.append(record)
 return results,arrays

def prepare():
 OUT.mkdir(exist_ok=True);base=HERE/'export/01_prepare_inputs/full';p=M.Problem();pred,_=p.prediction(p.start.ravel());ph=p.p.copy();ph['predicted_utc']=pd.to_datetime(p.t0[p.ei]+pred,unit='s',utc=True).astype(str)
 ph=ph[ph.phase.eq('P')&ph.probability.ge(.7)].copy();ph['selection_hash']=ph.pick_id.map(lambda s:hashlib.sha256(('vertical42:'+s).encode()).hexdigest());ph=ph.sort_values('selection_hash').groupby('instrument_id',sort=True).head(20).sort_values(['instrument_id','pick_id']);assert len(ph)>=200 and ph.instrument_id.nunique()>=20
 evaluation=pd.read_csv(HERE/'export/39_support_aware_pairs/inputs/events.csv');assert not set(ph.event_id)&set(evaluation.event_id)
 inventory=pd.read_csv(base/'waveform_inputs.csv',keep_default_na=False);inventory=inventory[inventory.component.eq('Z')].copy();jobs=[]
 for instrument,q in ph.groupby('instrument_id'):
  seeds={s for channels in q.source_channels for s in channels.split(';') if s.endswith('Z')};assert len(seeds)==1
  records=[dict(pick_id=r.pick_id,event_id=r.event_id,predicted_utc=r.predicted_utc,reference_pick_utc=r.time_utc,existing_probability=float(r.probability)) for r in q.itertuples()];files=inventory[inventory.seed_id.isin(seeds)];assert len(files)>0;jobs.append((instrument,records,files.to_dict('records')))
 files=[Path(__file__),Path(M.__file__),WEIGHT,META,LIB/'ai_module/phase_picking/model/dpppickerp.py',base/'waveform_inputs.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/39_support_aware_pairs/inputs/events.csv']+p.gridfiles
 design={'round':21,'stage':'Qualification before target picking/location; no new catalog observations admitted yet.','candidate':'Use genuine vertical-only DPPPicker P with local SCEDC benchmark weights; no missing-horizontal imputation, no S picks. Conditional picking around existing event travel-time predictions, not continuous detection or a new event catalog.','implementation_source':'https://github.com/seisbench/pick-benchmark/blob/main/benchmark/models.py#L876-L981','paper':'https://doi.org/10.1029/2021JB023499','inference':'1000 samples at 100 Hz, per-window demean and peak normalize, inference mode. Step-label output: FIRST >0.5 sample, never peak argmax. No crossing => abstain (never benchmark midpoint fallback). Windows centered at prediction minus/plus 1 s; require first crossings at least 1 s from edges and agree <=0.10 s. Keep earlier-window onset. Require pre-step median<=0.2, post-step median>=0.8, raw within-window signal/noise standard-deviation ratio>=2, prediction difference<=1 s. Raw finite contiguous Z only, vertical polarity from dip; no waveform-gap fill or response/filter changes.','selection':'Up to 20 existing P picks per instrument with probability>=0.7, sorted by fixed hash, from old 147-event cohort excluded from every current target/support. Window centers use original NLL travel times, not observed pick timestamps. Existing picks enter comparison only.','qualification_gates':'At least 200 examples and 20 instruments; accepted fraction>=0.50, median absolute existing-pick difference<=0.10 s, P90<=0.25 s, absolute median signed difference<=0.05 s. No threshold/weight scan if failed. Passing is compatibility only and allows conditional candidate extraction, not adoption.','limitations':'Original automated P picks are not ground truth; their original locations used arrivals including these picks. SCEDC weight training-event overlap with this case is not established. A step picker is not an independent detector. New-station association must check competing events and gap/epoch metadata before inclusion.','n_examples':len(ph),'n_instruments':ph.instrument_id.nunique(),'n_events':ph.event_id.nunique(),'source_sha256':{str(f):M.sha(f) for f in files}}
 f=OUT/'design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:M.save(f,design)
 ph.to_csv(OUT/'qualification_inputs.csv',index=False);assert crossing(np.zeros(1000)) is None and crossing(np.r_[np.zeros(400),np.ones(600)])==400
 return jobs

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);args=parser.parse_args();jobs=prepare();results=[];arrays={}
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn'),initializer=initialize) as pool:
  for i,f in enumerate(as_completed([pool.submit(pick_job,j) for j in jobs]),1):
   rows,cache=f.result();results.extend(rows);arrays.update(cache);print('Qualified input station',i,'/',len(jobs),'accepted',sum(r['accepted'] for r in rows),'/',len(rows),flush=True)
 q=pd.DataFrame(results).sort_values(['instrument_id','pick_id']);q.to_csv(OUT/'qualification_results.csv',index=False);np.savez_compressed(OUT/'qualification_windows.npz',**arrays);accepted=q[q.accepted];delta=accepted.difference_from_existing_P_s
 metrics={'n_examples':len(q),'n_instruments':q.instrument_id.nunique(),'n_accepted':len(accepted),'accepted_fraction':len(accepted)/len(q),'median_abs_difference_s':float(delta.abs().median()) if len(delta) else None,'p90_abs_difference_s':float(delta.abs().quantile(.9)) if len(delta) else None,'median_signed_difference_s':float(delta.median()) if len(delta) else None,'rejection_counts':q[~q.accepted].reason.value_counts().to_dict()}
 gates={'size':len(q)>=200 and q.instrument_id.nunique()>=20,'coverage':len(accepted)>=.5*len(q),'timing':bool(len(delta) and delta.abs().median()<=.10 and delta.abs().quantile(.9)<=.25 and abs(delta.median())<=.05)}
 result={'round':21,'qualification_gates':gates,'qualification_metrics':metrics,'decision':'qualified_for_target_extraction' if all(gates.values()) else 'do_not_add_vertical_p_observations','full_catalog_adopted':False,'new_target_picks_added':0};M.save(OUT/'qualification.json',result)
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
