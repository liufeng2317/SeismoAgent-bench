#!/usr/bin/env python3
"""Disjoint-event, origin-free constant Vp/Vs calibration before location use."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parents[2]
OUT=HERE/'export/49_velocity_ratio'
OLD=1.73
LAMBDA=(.2**2+.3**2)/(.1**2+.3**2)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def moments(frame):
 rows=[]
 for eid,g in frame.groupby('event_id'):
  if len(g)<4 or g.P.max()-g.P.min()<1.:continue
  x=g.P.to_numpy()-g.P.mean();y=g.S.to_numpy()-g.S.mean();w=1/(len(g)-1)
  rows.append({'event_id':eid,'xx':float(x@x*w),'xy':float(x@y*w),'yy':float(y@y*w),'n':len(g)})
 return pd.DataFrame(rows)
def fit(m):
 xx,xy,yy=m[['xx','xy','yy']].sum().to_numpy()
 assert xy>0
 return float((yy-LAMBDA*xx+np.sqrt((yy-LAMBDA*xx)**2+4*LAMBDA*xy**2))/(2*xy))
def fold(e):return int(hashlib.sha256(e.encode()).hexdigest()[:8],16)%5
def main():
 OUT.mkdir(exist_ok=True)
 files=[Path(__file__),HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/12_relative_location_pilot/run.json',HERE/'export/48_differential_augmentation/refreshed/inputs/events.csv',HERE/'docs/optimization_reserved_events_v3.csv']
 design={'round':28,'intervention':'Estimate one constant path-average Vp/Vs using event-centered, equal-event-weight Deming regression on original high-confidence paired P/S arrivals. No reference coordinates, source depths, new EQ S or station corrections enter calibration.','input':'Original147 transfer events, disjoint from current targets/supports and unused reserve3. Unique event/instrument P/S with both PN probabilities>=0.7 and S>P. Event training pairs>=4, P-time span>=1s. No post-fit residual trimming.','fit':'Five deterministic event folds, slope from other four folds at training stations only; held-event intercept estimated from its training stations, never its held stations. Deming error variance ratio=(0.2^2+0.3^2)/(0.1^2+0.3^2), matching archived working absolute errors. Equal event weight1/(n-1); no station-pair pseudo-replication.','uncertainty':'2000 event bootstrap draws, seed49; leave-one-training-station-out slope range. These do not encompass systematic picker/path error or historical calibration exposure.','gates':{'eligible_events_min':50,'held_pairs_min':100,'held_events_min':30,'held_rms_ratio_max':.98,'held_p90_ratio_max':1.05,'five_fold_slope_range_max':.05,'leave_station_out_range_max':.05,'slope_strict_interval':[1.45,2.1],'bootstrap95_excludes_original':True},'next':'Only if all calibration gates pass: use fitted ratio with unchanged Vp and 1D geometry in actual matched relocation. Keep every stage48 catalog gate, all data and coverage failure. No ratio scan, bounds change or depth-reference fitting.','source':'Dahm & Fischer2014, GJI196,957-970, equations3-4 and origin-free orthogonal multi-event regression; https://doi.org/10.1093/gji/ggt410 . This implementation uses Deming moments, not their least-median estimator.','source_sha256':{str(p):sha(p) for p in files}}
 f=OUT/'design.json'
 if f.exists():assert json.loads(f.read_text())==design
 else:save(f,design)
 ids=set(pd.read_csv(files[1]).event_id);current=set(pd.read_csv(files[4]).event_id);reserve=set(pd.read_csv(files[5]).event_id);assert len(ids)==147 and not ids&current and not ids&reserve
 held=set(json.loads(files[3].read_text())['held_out_stations'])
 p=pd.read_csv(files[2],low_memory=False);p=p[p.event_id.isin(ids)&p.phase.isin(['P','S'])&p.probability.ge(.7)].copy();p=p[~p.duplicated(['event_id','instrument_id','phase'],keep=False)]
 # Subtract a fixed date for precision, not estimated event origin or location.
 p['seconds']=(pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.Timestamp('2019-07-04T00:00:00Z')).dt.total_seconds()
 pair=p.pivot(index=['event_id','instrument_id'],columns='phase',values='seconds').dropna().reset_index();pair=pair[pair.S>pair.P].copy();pair['held_station']=pair.instrument_id.isin(held);pair['fold']=pair.event_id.map(fold)
 train=pair[~pair.held_station];m=moments(train);train=train[train.event_id.isin(m.event_id)];pair=pair[pair.event_id.isin(m.event_id)].copy();pair.to_csv(OUT/'paired_arrivals.csv',index=False);m.to_csv(OUT/'event_moments.csv',index=False)
 assert len(m)>=10
 m['fold']=m.event_id.map(fold);ratio=fit(m);folds=[];pred=[]
 for k in range(5):
  r=fit(m[m.fold.ne(k)]);folds.append({'fold':k,'vp_vs':r,'fit_events':int(m.fold.ne(k).sum())})
  for eid,g in pair[pair.fold.eq(k)].groupby('event_id'):
   tr=g[~g.held_station];ho=g[g.held_station].copy()
   for label,slope in [('original',OLD),('calibrated',r)]:
    # Separate event intercept for each ratio; no held-station or reference input.
    intercept=float((tr.S-slope*tr.P).mean());q=ho[['event_id','instrument_id','P','S']].copy();q['model']=label;q['fold']=k;q['vp_vs']=slope;q['residual_s']=ho.S-slope*ho.P-intercept;pred.append(q)
 predictions=pd.concat(pred,ignore_index=True);predictions.to_csv(OUT/'held_predictions.csv',index=False);pd.DataFrame(folds).to_csv(OUT/'fold_fits.csv',index=False)
 rng=np.random.default_rng(49);boot=[fit(m.iloc[rng.integers(0,len(m),len(m))]) for _ in range(2000)];ci=np.quantile(boot,[.025,.975]);jack=[]
 for station in sorted(train.instrument_id.unique()):
  mm=moments(train[train.instrument_id.ne(station)]);jack.append({'excluded_station':station,'vp_vs':fit(mm),'events':len(mm)})
 pd.DataFrame(jack).to_csv(OUT/'station_jackknife.csv',index=False)
 stats={}
 for label,g in predictions.groupby('model'):
  stats[label]={'n':len(g),'events':g.event_id.nunique(),'rms_s':float(np.sqrt(np.mean(g.residual_s**2))),'p90_abs_s':float(np.quantile(abs(g.residual_s),.9))}
 rms=stats['calibrated']['rms_s']/stats['original']['rms_s'];p90=stats['calibrated']['p90_abs_s']/stats['original']['p90_abs_s'];fr=float(np.ptp([r['vp_vs'] for r in folds]));jr=float(np.ptp([r['vp_vs'] for r in jack]));gates={'coverage':len(m)>=50 and stats['calibrated']['n']>=100 and stats['calibrated']['events']>=30,'held_rms':rms<=.98,'held_p90':p90<=1.05,'event_split_stability':fr<=.05,'station_stability':jr<=.05,'physical_interval':1.45<ratio<2.1,'bootstrap_distinguishes_original':not ci[0]<=OLD<=ci[1]}
 result={'round':28,'decision':'qualified_for_matched_location' if all(gates.values()) else 'do_not_change_velocity_ratio','gates':gates,'vp_vs':ratio,'original_vp_vs':OLD,'event_bootstrap95':ci.tolist(),'eligible_events':len(m),'training_pairs':len(train),'held_scores':stats,'rms_ratio':rms,'p90_ratio':p90,'fold_slope_range':fr,'station_jackknife_range':jr,'reserve3_used':False,'full_catalog_adopted':False}
 save(OUT/'calibration.json',result)
 # Candidate numerical model, explicitly not an adopted model.
 z=np.array([0,1,2,3,4,5,6,7,8,30]);vp=np.array([4.74,5.01,5.35,5.71,6.07,6.17,6.27,6.34,6.39,7.8]);pd.DataFrame({'depth_km_below_0p7km_ASL':z,'vp_km_s':vp,'vs_candidate_km_s':vp/ratio,'vs_original_km_s':vp/OLD}).to_csv(OUT/'candidate_velocity_model.csv',index=False)
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42});fig,axes=plt.subplots(1,3,figsize=(10,3.2),layout='constrained');center=train[['P','S']]-train.groupby('event_id')[['P','S']].transform('mean');axes[0].scatter(center.P,center.S,s=5,alpha=.35,color='#0072B2');xx=np.array([center.P.min(),center.P.max()]);axes[0].plot(xx,xx*OLD,color='#666666',label='Original');axes[0].plot(xx,xx*ratio,color='#D55E00',label='Calibrated');axes[0].set(xlabel='Centered P arrival (s)',ylabel='Centered S arrival (s)');axes[0].legend(frameon=False)
 axes[1].errorbar([0],[ratio],yerr=[[ratio-ci[0]],[ci[1]-ratio]],fmt='o',color='#0072B2');axes[1].scatter(np.ones(5),[x['vp_vs'] for x in folds],s=20,color='#D55E00');axes[1].axhline(OLD,color='#666666');axes[1].set(xticks=[0,1],xticklabels=['Fit / bootstrap','Event folds'],ylabel='Vp/Vs')
 for label,color in [('original','#666666'),('calibrated','#0072B2')]:
  v=np.sort(abs(predictions.loc[predictions.model.eq(label),'residual_s']));axes[2].plot(v,np.arange(1,len(v)+1)/len(v),label=label.capitalize(),color=color)
 axes[2].set(xlabel='Held S moveout error (s)',ylabel='Cumulative fraction');axes[2].legend(frameon=False)
 for ax,letter in zip(axes,'abc'):ax.text(0,1.04,letter,transform=ax.transAxes,fontweight='bold')
 for suffix in ['png','pdf']:fig.savefig(OUT/('calibration.'+suffix),dpi=220)
 plt.close(fig)
 for p,h in design['source_sha256'].items():assert sha(Path(p))==h
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
