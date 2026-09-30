#!/usr/bin/env python3
"""Noise-normalized two-horizontal-component S correlation; P rows unchanged."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('robust38source',DIR/'37_robust_cc.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);M=R.M;HERE=M.HERE
SRC=HERE/'export/35_cc_observation_selection';OUT=HERE/'export/38_vector_s';CACHE=SRC/'cc_processing'

def curve(a,b,limit=40):
 a=np.asarray(a,float).copy();b=np.asarray(b,float).copy();assert a.shape==b.shape and a.ndim==2
 a-=a.mean(axis=1,keepdims=True);b-=b.mean(axis=1,keepdims=True);na=np.linalg.norm(a);nb=np.linalg.norm(b)
 if min(na,nb)<1e-20:raise ValueError('Zero vector signal')
 a/=na;b/=nb;n=a.shape[1];lags=np.arange(-limit,limit+1);values=[]
 for lag in lags:
  aa,bb=(a[:,-lag:],b[:,:n+lag]) if lag<0 else ((a[:,:n-lag],b[:,lag:]) if lag>0 else (a,b))
  values.append(float(np.sum(aa*bb)))
 return lags,np.array(values)

def whiten(signal,snr):
 rms=np.sqrt(np.mean(signal**2,axis=1));snr=np.asarray(snr,float)
 if not np.all(np.isfinite(snr)) or np.any(snr<=0) or np.any(rms<=0):raise ValueError('Invalid noise estimate')
 return signal/(rms/snr)[:,None]

def checks():
 t=np.arange(181)/100;a=np.exp(-((t-.6)/.06)**2)*np.cos(2*np.pi*6*(t-.6));b=np.exp(-((t-.67)/.06)**2)*np.cos(2*np.pi*6*(t-.67));aa=np.vstack([a,.1*a]);bb=np.vstack([b,.1*b]);ls,c=curve(aa,bb);lag=ls[np.argmax(c)]/100;assert abs(lag-.07)<1e-12;assert abs((2-lag)-1.93)<1e-12
 one=curve(a[None,:],b[None,:]);zero=curve(np.vstack([a,np.zeros_like(a)]),np.vstack([b,np.zeros_like(b)]));assert np.allclose(one[1],zero[1],atol=1e-14)
 w1=whiten(aa,[10,1]);w2=whiten(aa*np.array([3.,.2])[:,None],[10,1]);assert np.allclose(w1,w2,atol=1e-13)
 swap=curve(bb,aa);assert ls[np.argmax(swap[1])]==-7
 return {'known_lag_s':float(lag),'arrival_difference_sign_verified':True,'zero_component_reduction':True,'channel_gain_invariance_after_noise_normalization':True,'pair_reversal_lag_verified':True}

def main():
 OUT.mkdir(exist_ok=True)
 files=[Path(__file__),CACHE/'cc_windows.npz',CACHE/'waveform_windows.csv',SRC/'inputs/picks.csv',SRC/'cc_measurements.csv',HERE/'export/37_robust_cc/design.json']
 design={'round':17,'cohort_role':'Exposed development, same 300 targets and 1970 supports.','intervention':'Replace S measurement/eligibility by a common lag maximizing full-window normalized dot product of the two matched horizontal traces. Normalize each component by its own pre-event noise RMS recovered from cached window RMS and band SNR. Demean per component; retain full-window normalization at all lags, as in the original scalar routine. P observations are copied unchanged.','quality':'Both horizontal channels and both band windows must exist. Combined noise-normalized SNR sqrt(mean(component_SNR^2)) >=2 for each event and band. Both vector band peaks >=0.75, positive polarity, peak margin>=0.08 outside 0.08 s exclusion, abs lag<=0.38 s (same two-sample boundary rule at +/-0.4), band lag difference<=0.020001 s. No separate component veto or post-hoc choice of the better method.','location':'Keep stage37 CC-only Huber delta=1.345, CC error 0.05 s, original quadratic absolute objective and mean 1D model. Only S observations change.','gates':'All stage34 gates retained. Additionally score ALL original 575 held CC measurements (including newly rejected S edges) and require RMS <=1.05 times stage37 on those identical observations. Score new held set separately. No threshold scans or cohort replacements. Exposed data cannot count as fresh confirmation.','limitations':'Joint SNR/CC statistics differ from individual-component statistics, despite unchanged numerical cutoffs. Noise estimates are recovered from archived SNR values and float32 signal windows. No polarity rotation or instrument-response reinterpretation; noise normalization cancels constant positive channel gains. Independence/calibration is not presumed.','source_sha256':{str(f):M.sha(f) for f in files}}
 p=OUT/'design.json'
 if p.exists():assert json.loads(p.read_text())==design
 else:M.save(p,design)
 M.save(OUT/'numerical_checks.json',checks())
 source=pd.read_csv(SRC/'cc_measurements.csv');result=source.copy();picks=pd.read_csv(SRC/'inputs/picks.csv').set_index('pick_id');meta=pd.read_csv(CACHE/'waveform_windows.csv').set_index(['pick_id','seed_id']);archive=np.load(CACHE/'cc_windows.npz');windows={key:archive[key] for key in archive.files};archive.close();audits=[]
 for count,(idx,row) in enumerate(source[source.phase.eq('S')].iterrows(),1):
  a,b=picks.loc[row.pick_id_a],picks.loc[row.pick_id_b];seeds=sorted((set(a.source_channels.split(';'))&set(b.source_channels.split(';')))-{v for v in a.source_channels.split(';') if v.endswith('Z')});record={'edge_index':idx,'accepted':False,'reason':'missing_horizontal_windows'}
  valid=len(seeds)==2 and all((pid,seed) in meta.index and meta.loc[(pid,seed),'status']=='ok' and pid+'|'+seed in windows for pid in [row.pick_id_a,row.pick_id_b] for seed in seeds)
  if valid:
   try:
    lag=[];peak=[];margin=[];snrs=[];boundary=False
    for band,snrname in [(0,'snr_primary'),(1,'snr_check')]:
     av=np.stack([windows[row.pick_id_a+'|'+seed][band] for seed in seeds]).astype(float);bv=np.stack([windows[row.pick_id_b+'|'+seed][band] for seed in seeds]).astype(float);sa=np.array([meta.loc[(row.pick_id_a,seed),snrname] for seed in seeds]);sb=np.array([meta.loc[(row.pick_id_b,seed),snrname] for seed in seeds]);snrs.extend([float(np.sqrt(np.mean(sa**2))),float(np.sqrt(np.mean(sb**2)))])
     ls,c=curve(whiten(av,sa),whiten(bv,sb));best=int(np.argmax(abs(c)));lag.append(float(ls[best]/100));peak.append(float(c[best]));margin.append(float(c[best]-np.max(abs(c[abs(ls-ls[best])>8]))));boundary |= abs(ls[best])>=39
    reasons=[]
    if min(snrs)<2:reasons.append('low_vector_snr')
    if min(peak)<.75:reasons.append('low_or_negative_vector_cc')
    if min(margin)<.08:reasons.append('ambiguous_peak')
    if boundary:reasons.append('lag_boundary')
    if abs(lag[0]-lag[1])>.020001:reasons.append('band_instability')
    record.update(accepted=not reasons,reason=';'.join(reasons) or 'accepted',lag_s=lag[0],cc=peak[0],cc_check=peak[1],lag_check_s=lag[1],min_vector_snr=min(snrs),peak_margin=min(margin))
   except ValueError as exc:record['reason']='invalid_noise_estimate'
  for col,value in [('accepted',record['accepted']),('reason',record['reason']),('lag_s',record.get('lag_s',np.nan) if record['accepted'] else np.nan),('cc',record.get('cc',np.nan) if record['accepted'] else np.nan)]:result.loc[idx,col]=value
  result.loc[idx,'cc_arrival_difference_s']=row.observed_dt_s-record['lag_s'] if record['accepted'] else np.nan;audits.append(record)
  if count%3000==0:print('Vector S',count,'of',int(source.phase.eq('S').sum()),flush=True)
 assert result[source.phase.eq('P')].equals(source[source.phase.eq('P')]);result.to_csv(OUT/'cc_measurements.csv',index=False);pd.DataFrame(audits).to_csv(OUT/'vector_s_audit.csv',index=False)
 M.save(OUT/'measurement_summary.json',{'old_P':int((source.accepted&source.phase.eq('P')).sum()),'new_P':int((result.accepted&result.phase.eq('P')).sum()),'old_S':int((source.accepted&source.phase.eq('S')).sum()),'new_S':int((result.accepted&result.phase.eq('S')).sum()),'all_old_P_rows_identical':True})
 for f,h in design['source_sha256'].items():assert M.sha(Path(f))==h
 print((OUT/'measurement_summary.json').read_text(),flush=True)
if __name__=='__main__':main()
