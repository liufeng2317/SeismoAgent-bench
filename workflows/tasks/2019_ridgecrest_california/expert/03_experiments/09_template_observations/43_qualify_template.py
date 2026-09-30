#!/usr/bin/env python3
"""Qualify waveform-only recovery of hidden P times before missing-pick use."""
from pathlib import Path
import os
for key in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[key]='1'
import importlib.util,json,hashlib
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
from obspy import read,UTCDateTime
DIR=Path(__file__).resolve().parent;HERE=DIR.parents[1];OUT=HERE/'export/43_template_p_observations'
WAVE=HERE.parents[2]/'data/2019_ridgecrest_california/data/waveforms'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
M=load('original43',DIR.parent/'07_joint_location/33_joint_location.py')
BANDS=[(2.,8.),(2.,12.)];FS=100;LIMIT=75;TIMES=np.arange(-500,301)/100

def correlation(template,search):
 windows=np.lib.stride_tricks.sliding_window_view(search,len(template)).astype(float);windows-=windows.mean(axis=1,keepdims=True);a=template.astype(float)-template.mean();den=np.sqrt(np.sum(windows**2,axis=1)*np.sum(a*a));return np.divide(windows@a,den,out=np.zeros(len(windows)),where=den>1e-20)

def measure(template,query):
 """Neither event predictions nor hidden pick times are available here."""
 peaks=[];margins=[];lags=[];snrs=[]
 for a,b in zip(template,query):
  signal=a[480:601];curve=correlation(signal,b[405:676]);assert len(curve)==151
  best=int(np.argmax(abs(curve)));lag=best-LIMIT;peaks.append(float(curve[best]));lags.append(lag)
  competing=curve[abs(np.arange(len(curve))-best)>8];margins.append(float(curve[best]-np.max(abs(competing))))
  noise_a=np.sqrt(np.mean(a[:400]**2));noise_b=np.sqrt(np.mean(b[:400]**2));snrs.append(float(min(np.sqrt(np.mean(signal**2))/max(noise_a,1e-20),np.sqrt(np.mean(b[480+lag:601+lag]**2))/max(noise_b,1e-20))))
 reasons=[]
 if min(peaks)<.75:reasons.append('low_or_negative_cc')
 if min(margins)<.08:reasons.append('ambiguous_peak')
 if max(abs(v) for v in lags)>=74:reasons.append('lag_boundary')
 if abs(lags[0]-lags[1])>2:reasons.append('band_instability')
 if min(snrs)<2:reasons.append('low_snr')
 return dict(accepted=not reasons,reason=';'.join(reasons) or 'accepted',lag_s=lags[0]/100,check_lag_s=lags[1]/100,cc=peaks[0],cc_check=peaks[1],peak_margin=min(margins),snr=min(snrs))

def extract(job):
 path,rows=job;stream=read(str(WAVE/path));arrays={};audit=[]
 for row in rows:
  key=row['key'];seed=row['seed_id'];t=UTCDateTime(pd.Timestamp(row['center_utc']).isoformat());traces=stream.select(id=seed).slice(t-10,t+10).copy();traces.merge(method=-1)
  valid=[tr for tr in traces if tr.stats.starttime<=t-9.9 and tr.stats.endtime>=t+9.9 and not np.ma.isMaskedArray(tr.data)]
  record=dict(row,path=path,status='gap_or_missing')
  if len(valid)!=1:audit.append(record);continue
  tr=valid[0];fs=float(tr.stats.sampling_rate)
  if fs<50 or not np.isfinite(tr.data).all():record['status']='invalid_samples';audit.append(record);continue
  values=[]
  for lo,hi in BANDS:
   f=tr.copy().detrend('linear').taper(.05).filter('bandpass',freqmin=lo,freqmax=hi,corners=3,zerophase=True);x=np.arange(len(f.data))/fs+float(f.stats.starttime-t);values.append(np.interp(TIMES,x,f.data).astype(np.float32))
  arrays[key]=np.stack(values);record['status']='ok';audit.append(record)
 return arrays,audit

def collect(requests):
 metadata=pd.read_csv(HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',keep_default_na=False);index={}
 for r in metadata.itertuples():index[(r.seed_id,Path(r.path).name.split('__')[1][:8])]=r
 jobs={};missing=[]
 for row in requests:
  key=(row['seed_id'],pd.Timestamp(row['center_utc']).strftime('%Y%m%d'));source=index.get(key)
  if source is None:missing.append(dict(row,path='',status='unindexed_file'));continue
  assert (WAVE/source.path).stat().st_size==int(source.bytes);jobs.setdefault(source.path,[]).append(row)
 arrays={};audit=missing
 with ThreadPoolExecutor(max_workers=4) as pool:
  for n,f in enumerate(as_completed([pool.submit(extract,j) for j in jobs.items()]),1):
   a,b=f.result();arrays.update(a);audit.extend(b)
   if n%20==0 or n==len(jobs):print('Extracted files',n,'/',len(jobs),flush=True)
 return arrays,pd.DataFrame(audit)

def prepare():
 OUT.mkdir(exist_ok=True);p=M.Problem();ph=p.p[p.p.phase.eq('P')].copy();held=set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']);ph=ph[~ph.instrument_id.isin(held)].sort_values('probability',ascending=False).drop_duplicates(['event_id','instrument_id']);lookup=ph.set_index(['event_id','instrument_id']);stations={k:set(g.instrument_id) for k,g in ph.groupby('event_id')}
 events=p.e.set_index('event_id');pred,_=p.prediction(p.start.ravel());predictions=dict(zip(p.p.pick_id,p.t0[p.ei]+pred));edges=pd.read_csv(HERE/'export/15_validate_transfer/inputs/differential_times.csv');pairs=edges[['event_id_a','event_id_b']].drop_duplicates();rows=[]
 for ea,eb in pairs.itertuples(index=False,name=None):
  if np.linalg.norm(events.loc[ea,M.XYZ].to_numpy(float)-events.loc[eb,M.XYZ].to_numpy(float))>3:continue
  for instrument in stations.get(ea,set())&stations.get(eb,set()):
   a=lookup.loc[(ea,instrument)];b=lookup.loc[(eb,instrument)]
   if min(a.probability,b.probability)<.3 or max(a.probability,b.probability)<.7:continue
   if b.probability>a.probability:a,b=b,a
   seed=[v for v in a.source_channels.split(';') if v.endswith('Z')];assert len(seed)==1
   if seed[0] not in b.source_channels.split(';'):continue
   identity=a.pick_id+'__'+b.pick_id;digest=hashlib.sha256(('template43:'+identity).encode()).hexdigest();jitter=.3 if int(digest[:2],16)%2 else -.3
   center=float(pd.Timestamp(a.time_utc).timestamp())+predictions[b.pick_id]-predictions[a.pick_id]+jitter
   rows.append(dict(id=identity,instrument_id=instrument,seed_id=seed[0],template_pick_id=a.pick_id,template_event=a.name[0],query_event=b.name[0],template_utc=a.time_utc,query_center_utc=pd.Timestamp(center,unit='s',tz='UTC').isoformat(),hidden_reference_utc=b.time_utc,jitter_s=jitter,selection_hash=digest))
 q=pd.DataFrame(rows).sort_values('selection_hash').groupby('instrument_id',sort=True).head(20).sort_values(['instrument_id','id']).reset_index(drop=True);assert len(q)>=200 and q.instrument_id.nunique()>=15
 current=pd.read_csv(HERE/'export/42_vertical_p_observations/inputs/events.csv');reserve=pd.read_csv(HERE/'docs/optimization_reserved_events_v3.csv');used=set(q.template_event)|set(q.query_event);assert not used&set(current.event_id) and not used&set(reserve.event_id)
 files=[Path(__file__),Path(M.__file__),M.BASE/'stations.csv',HERE/'export/12_relative_location_pilot/run.json',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/15_validate_transfer/inputs/differential_times.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',HERE/'export/42_vertical_p_observations/inputs/events.csv',HERE/'docs/optimization_reserved_events_v3.csv']+p.gridfiles
 design={'round':22,'stage':'Qualification before target extraction; no new observations admitted.','source':'https://www.usgs.gov/data/correlation-derived-seismic-phase-arrival-times-matched-filter-studies-yellowstone-wyoming','method':'Same-channel vertical P template, 1.21 s (-0.2,+1.0 s), two bands 2-8 and 2-12 Hz, fixed +/-0.75 s search on the query. Pearson normalized sliding correlation with a constant full template (no variable-overlap lag correlation). Keep positive dominant peak >=0.75, margin >=0.08 outside +/-0.08 s, both-band lag agreement <=0.02 s, no peak within 0.01 s of search edge, both-window/band SNR>=2. Candidate onset is query center plus first-band peak lag, never the model center fallback. No interpolation or model fitting.','inputs':'Up to20 hashed pairs per training instrument from disjoint147-event calibration, original distance<=3km. Template probability>=0.7, hidden query>=0.3; choose higher-probability endpoint as template. Centers use template observed time plus original predicted differential arrival, with fixed hash +/-0.3 s jitter for qualification. Hidden timestamps enter scoring only; original locations did use those picks, so this is compatibility, not blind timing truth.','offtime':'For every query also test center+30 s with waveform gates only. This can contain real earthquakes, so report off-time waveform acceptance, not noise-only false-positive rate. No prediction-time/association veto is applied to these controls.','gates':'>=200 pairs/15 instruments; >=100 accepted, >=25% of all pairs, accepted >=15 instruments and20 query events; median absolute hidden-pick difference<=0.10 s, P90<=0.20 s and median error<=0.75 times accepted-center median error; off-time acceptance<=1% of all requested controls; at least90% of query and off-time requests must have actual waveform measurements. Fixed thresholds, no scan on failure.','future_use':'Only after qualification passes, test missing P constraints on the fixed stage39/42 graph. Do not double-count a template-derived arrival as independent absolute data plus the same differential measurement. New third reserve stays unopened. Full location/coverage/reference/anchor gates remain; qualification alone cannot promote a catalog.','source_sha256':{str(f):M.sha(f) for f in files},'n_pairs':len(q),'n_instruments':q.instrument_id.nunique()}
 dest=OUT/'design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 q.to_csv(OUT/'qualification_inputs.csv',index=False);requests={}
 for r in q.itertuples():
  requests[r.template_pick_id]=dict(key=r.template_pick_id,seed_id=r.seed_id,center_utc=r.template_utc)
  for suffix,offset in [('query',0),('offtime',30)]:
   key=r.id+'|'+suffix;requests[key]=dict(key=key,seed_id=r.seed_id,center_utc=(pd.Timestamp(r.query_center_utc)+pd.Timedelta(seconds=offset)).isoformat())
 pd.DataFrame(requests.values()).to_csv(OUT/'waveform_requests.csv',index=False)
 t=TIMES;a=np.exp(-((t-.3)/.06)**2)*np.cos(2*np.pi*6*(t-.3));b=np.exp(-((t-.51)/.06)**2)*np.cos(2*np.pi*6*(t-.51));curve=correlation(a[480:601],b[405:676]);lag=(np.argmax(curve)-75)/100;assert abs(lag-.21)<1e-10
 reverse=measure(np.stack([a,a]),np.stack([-b,-b]));assert not reverse['accepted'] and 'negative_cc' in reverse['reason']
 M.save(OUT/'numerical_checks.json',{'synthetic_positive_lag_s':lag,'arrival_rule':'query_center + lag; absolute timestamp A - B = center_A - center_B - lag','reversed_polarity_rejected':True})
 return q,list(requests.values())

def main():
 q,requests=prepare();print('Qualification pairs',len(q),'instruments',q.instrument_id.nunique(),flush=True);arrays,audit=collect(requests);audit.to_csv(OUT/'waveform_windows.csv',index=False);np.savez_compressed(OUT/'qualification_windows.npz',**arrays);rows=[]
 for r in q.itertuples():
  for kind in ['query','offtime']:
   key=r.id+'|'+kind;record=dict(id=r.id,instrument_id=r.instrument_id,query_event=r.query_event,kind=kind,accepted=False,reason='missing_contiguous_window')
   if r.template_pick_id in arrays and key in arrays:
    record.update(measure(arrays[r.template_pick_id],arrays[key]));center=pd.Timestamp(r.query_center_utc)+pd.Timedelta(seconds=30 if kind=='offtime' else 0);candidate=center+pd.Timedelta(seconds=record['lag_s']);record.update(candidate_utc=candidate.isoformat(),difference_from_hidden_P_s=(candidate-pd.Timestamp(r.hidden_reference_utc)).total_seconds(),center_difference_s=(center-pd.Timestamp(r.hidden_reference_utc)).total_seconds())
   rows.append(record)
 table=pd.DataFrame(rows);table.to_csv(OUT/'qualification_results.csv',index=False);accepted=table[table.kind.eq('query')&table.accepted];control=table[table.kind.eq('offtime')];err=accepted.difference_from_hidden_P_s.abs();center=accepted.center_difference_s.abs()
 metrics={'requested':len(q),'accepted':len(accepted),'accepted_instruments':accepted.instrument_id.nunique(),'accepted_query_events':accepted.query_event.nunique(),'acceptance_fraction':len(accepted)/len(q),'median_abs_difference_s':float(err.median()) if len(err) else None,'p90_abs_difference_s':float(err.quantile(.9)) if len(err) else None,'median_abs_center_difference_s':float(center.median()) if len(center) else None,'offtime_accepted':int(control.accepted.sum()),'offtime_requested':len(control),'offtime_acceptance_fraction':float(control.accepted.mean()),'measured_query_fraction':float(table[table.kind.eq('query')].reason.ne('missing_contiguous_window').mean()),'measured_offtime_fraction':float(control.reason.ne('missing_contiguous_window').mean())}
 gates={'size':len(q)>=200 and q.instrument_id.nunique()>=15,'coverage':len(accepted)>=100 and len(accepted)>=.25*len(q) and accepted.instrument_id.nunique()>=15 and accepted.query_event.nunique()>=20,'timing':bool(len(err) and err.median()<=.1 and err.quantile(.9)<=.2 and err.median()<=.75*center.median()),'offtime':bool(control.accepted.mean()<=.01),'waveform_availability':bool(metrics['measured_query_fraction']>=.9 and metrics['measured_offtime_fraction']>=.9)}
 M.save(OUT/'qualification.json',{'round':22,'qualification_gates':gates,'metrics':metrics,'decision':'qualified_for_missing_P_trial' if all(gates.values()) else 'do_not_add_template_P','full_catalog_adopted':False})
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'qualification.json').read_text(),flush=True)
if __name__=='__main__':main()
