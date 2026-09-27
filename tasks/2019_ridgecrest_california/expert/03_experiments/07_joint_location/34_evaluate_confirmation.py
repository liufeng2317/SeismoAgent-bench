#!/usr/bin/env python3
"""Score the frozen reserve only; support events are never substituted as targets."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
spec=importlib.util.spec_from_file_location('confirm34',Path(__file__).with_name('34_run_confirmation.py'));C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C);M=C.M;OUT=C.OUT
from pyproj import CRS,Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def main():
 template=M.Problem();primary=C.problem(template,False);aux=C.problem(template,True)
 status=pd.read_csv(OUT/'solver_status.csv');assert len(status)==16
 rows=[];positions=[];scoreframes=[]
 for p,withheld in [(primary,False),(aux,True)]:
  reserve=set(p.e.loc[p.e.role.eq('reserve'),'event_id']);pm=p.p.event_id.isin(reserve).to_numpy();cm=(p.c.event_id_a.isin(reserve)|p.c.event_id_b.isin(reserve)).to_numpy()
  for joint in [False,True]:
   branch=('joint' if joint else 'absolute')+('_withheld' if withheld else '_all');f=np.load(OUT/(branch+'_control.npz'));assert np.array_equal(f['event_id'],p.e.event_id.to_numpy());x=f['x'];tt,_=p.prediction(x.ravel());ar=tt-p.obs;cr=tt[p.a]-tt[p.b]-p.dt
   for kind,residual,mask in [('absolute',ar,pm&~p.train),('cc',cr,cm&~p.c.training.to_numpy())]:rows.append({'branch':branch,'kind':kind,'heldout':withheld,'n':int(mask.sum()),'rms_s':float(np.sqrt(np.mean(residual[mask]**2)))})
   q=p.e[['event_id','role','auxiliary_eligible']].copy();q[M.XYZ]=x[:,:3];q['origin_time']=pd.to_datetime(p.t0+x[:,3],unit='s',utc=True).astype(str);q['branch']=branch;positions.append(q)
   if withheld:
    q=p.p.loc[pm&~p.train,['pick_id','event_id','phase','instrument_id']].copy();q['residual_s']=ar[pm&~p.train];q['branch']=branch;scoreframes.append(q)
 metrics=pd.DataFrame(rows);metrics.to_csv(OUT/'metrics.csv',index=False);e=pd.concat(positions,ignore_index=True);e.to_csv(OUT/'events.csv',index=False);pd.concat(scoreframes).to_csv(OUT/'held_absolute_predictions.csv',index=False)
 reserve=set(primary.e.loc[primary.e.role.eq('reserve'),'event_id']);auxreserve=set(aux.e.loc[aux.e.role.eq('reserve'),'event_id'])
 native=pd.read_csv(OUT/'native_controls/events.csv').set_index('event_id');assert set(native.index)==auxreserve and native.status.eq('LOCATED').all()
 # Predict only reserve observations using the same native grids, never support substitutions.
 obs=aux.p[aux.p.event_id.isin(auxreserve)].copy().reset_index(drop=True);origins=pd.to_datetime(native.loc[obs.event_id,'origin_time'],utc=True,format='ISO8601').astype('int64').to_numpy()/1e9;obs[M.XYZ]=native.loc[obs.event_id,M.XYZ].to_numpy()
 spec=importlib.util.spec_from_file_location('diag34',M.HERE/'02_diagnostics/16_diagnose_systematics.py');d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d);tt,_=d.predict(M.BASE/'grids',obs,aux.st);elapsed=pd.to_datetime(obs.time_utc,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9-origins;obs['residual_s_independent']=elapsed-tt
 held=json.loads((M.HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'];mask=obs.instrument_id.isin(held);original_rms=float(np.sqrt(np.mean(obs.loc[mask,'residual_s_independent']**2)))
 nativefit=pd.read_csv(OUT/'native_controls/fit_phases.csv');check=nativefit[['pick_id','residual_s']].merge(obs[['pick_id','residual_s_independent']],on='pick_id',validate='one_to_one');assert len(check)==len(nativefit);native_error=float(np.max(abs(check.residual_s-check.residual_s_independent)));assert native_error<.00035
 # Frozen pairs used only now, after fitting; primary comparison on all reserve IDs.
 match=pd.read_csv(M.HERE/'export/10_validate_catalog/reference_matches.csv');match=match[match.event_id.isin(reserve)&match.matched&~match.ambiguous]
 refs=pd.read_csv(M.HERE/'export/05_review_catalog/reference_events.csv');match=match.merge(refs[['catalog','reference_id','longitude','latitude']],on=['catalog','reference_id'],validate='many_to_one')
 proj=Transformer.from_crs(4326,CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km'),always_xy=True);match['rx'],match['ry']=proj.transform(match.longitude.to_numpy(),match.latitude.to_numpy())
 base=primary.e[primary.e.event_id.isin(reserve)][['event_id']+M.XYZ].copy();base['branch']='original_nll';allpos=pd.concat([e[e.event_id.isin(reserve)&e.branch.isin(['absolute_all','joint_all'])],base],ignore_index=True);rrows=[];details=[]
 for branch,g in allpos.groupby('branch'):
  assert len(g)==300
  q=match.merge(g[['event_id']+M.XYZ],on='event_id',validate='many_to_one');q['horizontal_km']=np.hypot(q.x_km-q.rx,q.y_km-q.ry);q['absolute_depth_km']=np.where(q.catalog.eq('Shelly'),abs(q.depth_km-q.reference_depth_km),np.nan);q['branch']=branch;details.append(q)
  for cat,h in q.groupby('catalog'):rrows.append({'branch':branch,'catalog':cat,'n':len(h),'median_horizontal_km':h.horizontal_km.median(),'median_abs_depth_km':h.absolute_depth_km.median()})
 r=pd.DataFrame(rrows);r.to_csv(OUT/'reference_summary.csv',index=False);pd.concat(details).to_csv(OUT/'reference_comparison.csv',index=False)
 am=[];rm=aux.e.role.eq('reserve').to_numpy()
 for branch in ['absolute_withheld','joint_withheld']:
  b=np.load(OUT/(branch+'_control.npz'))['x'][rm,:3]
  for label in list(M.SHIFTS)[1:]:
   z=np.load(OUT/(branch+'_'+label+'.npz'))['x'][rm,:3]-b;am.append({'branch':branch,'start':label,'mean_shift_km':float(np.linalg.norm(z.mean(axis=0))),'p90_shift_km':float(np.quantile(np.linalg.norm(z,axis=1),.9))})
 anchor=pd.DataFrame(am);anchor.to_csv(OUT/'anchor_metrics.csv',index=False)
 train=aux.c[aux.c.training];hc=aux.c[~aux.c.training];trainids=(set(train.event_id_a)|set(train.event_id_b))&reserve;heldids=(set(hc.event_id_a)|set(hc.event_id_b))&reserve
 coverage={'primary_reserve':300,'auxiliary_reserve':len(auxreserve),'training_cc_reserve':len(trainids),'held_cc_reserve':len(heldids),'held_cc_edges':len(hc)}
 cohort=primary.e[primary.e.role.eq('reserve')][['event_id','auxiliary_eligible']].copy();cohort['training_cc_supported']=cohort.event_id.isin(trainids);cohort['held_cc_supported']=cohort.event_id.isin(heldids);cohort.to_csv(OUT/'reserve_status.csv',index=False)
 idx=metrics.set_index(['branch','kind']);ccratio=float(idx.loc[('joint_withheld','cc'),'rms_s']/idx.loc[('absolute_withheld','cc'),'rms_s']);aratio=float(idx.loc[('joint_withheld','absolute'),'rms_s']/idx.loc[('absolute_withheld','absolute'),'rms_s']);refok=True;rs=r.set_index(['branch','catalog'])
 for ctrl in ['absolute_all','original_nll']:
  for cat in ['Liu','Official','Shelly']:refok &= bool(rs.loc[('joint_all',cat),'median_horizontal_km']<=1.1*rs.loc[(ctrl,cat),'median_horizontal_km'])
  refok &= bool(rs.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*rs.loc[(ctrl,'Shelly'),'median_abs_depth_km'])
 near={b:int(((g.depth_km<.5)|(g.depth_km>24.5)).sum()) for b,g in allpos.groupby('branch')};a=anchor[anchor.branch.eq('joint_withheld')]
 gates={'coverage':len(auxreserve)>=240 and len(trainids)>=210 and len(heldids)>=50 and len(hc)>=100,'termination':bool(status.success.all()),'held_cc':ccratio<=.95,'held_absolute':bool(aratio<=1.05 and idx.loc[('joint_withheld','absolute'),'rms_s']<=1.05*original_rms),'references':bool(refok),'anchor':bool(a.mean_shift_km.le(.1).all() and a.p90_shift_km.le(.2).all()),'boundary':near['joint_all']<=near['original_nll']+3}
 result={'round':13,'decision':'confirmation_passed_prepare_full_production' if all(gates.values()) else 'do_not_promote','gates':gates,'coverage':coverage,'held_cc_ratio':ccratio,'held_absolute_ratio':aratio,'original_nll_held_absolute_rms_s':original_rms,'native_residual_check_max_s':native_error,'near_boundary_counts':near,'reserve_v2_used':True,'full_catalog_adopted':False};M.save(OUT/'run.json',result)
 fig,axes=plt.subplots(1,2,figsize=(8,3.4),layout='constrained')
 for ax,kind in zip(axes,['absolute','cc']):ax.bar(['Absolute only','Joint'],[idx.loc[(b,kind),'rms_s'] for b in ['absolute_withheld','joint_withheld']],color=['#666666','#0072B2']);ax.set_ylabel('Held-out RMS (s)');ax.set_title('Absolute arrivals' if kind=='absolute' else 'CC differential times')
 fig.savefig(OUT/'confirmation.png',dpi=220);fig.savefig(OUT/'confirmation.pdf');plt.close(fig)
 (OUT/'RESULTS.md').write_text('# Frozen reserve confirmation\n\nDecision: **'+result['decision']+'**. Only fixed reserve events are scoring targets; support locations are not substitutes.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n```text\n'+metrics.to_string(index=False)+'\n```\n\n```text\n'+r.to_string(index=False)+'\n```\n\nEvery primary reserve event remains represented; auxiliary eligibility and CC support are in reserve_status.csv. `all` branch station-subset metrics are fitted diagnostics, not holdout scores. Shared support events/CC edges and upstream pick selection limit independence. Cost-change termination and local multi-start stability are not proof of a global optimum. No formal posterior or full-catalog accuracy claim is made.\n')
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
