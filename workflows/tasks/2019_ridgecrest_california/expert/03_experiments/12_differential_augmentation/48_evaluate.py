#!/usr/bin/env python3
"""Score fixed observations and unchanged catalog gates for both frozen branches."""
from pathlib import Path
import argparse,importlib.util,json
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('run48',DIR/'48_run.py');M=C.M;V=load('validation48',DIR.parent/'07_joint_location/_joint_validation.py')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--branch',choices=['fixed','refreshed'],default='refreshed');args=ap.parse_args();C.configure(args.branch);out=C.OUT
 result=V.evaluate(C,out,round_id=27,cohort_role='exposed_development')
 for suffix in ['png','pdf']:(out/('confirmation.'+suffix)).replace(out/('development_comparison.'+suffix))
 template=M.Problem();rows=[];details=[]
 for name,source,expected in [('old575',C.OBS,575),('fixed1408',C.SRC,1408)]:
  B=load('old48_'+name,DIR.parent/'07_joint_location/34_run_confirmation.py');B.OUT=source;B.INPUT=source/'inputs';B.M.BASE=M.BASE;p=B.problem(template,True);held=~p.c.training.to_numpy();assert held.sum()==expected
  for label,file in [('stage45',C.BASELINE/'joint_withheld_control.npz'),('stage47',C.SRC/'joint_withheld_control.npz'),('candidate',out/'joint_withheld_control.npz'),('matched_absolute',out/'absolute_withheld_control.npz')]:
   with np.load(file) as data:
    ix=pd.Index(data['event_id']).get_indexer(p.e.event_id);assert (ix>=0).all();x=data['x'][ix]
   tt,_=p.prediction(x.ravel());residual=tt[p.a]-tt[p.b]-p.dt
   for phase in ['all','P','S']:
    mask=held if phase=='all' else held&p.c.phase.eq(phase).to_numpy();rows.append({'observations':name,'solution':label,'phase':phase,'n':int(mask.sum()),'rms_s':float(np.sqrt(np.mean(residual[mask]**2)))})
   q=p.c.loc[held,['event_id_a','event_id_b','pick_id_a','pick_id_b','instrument_id','phase']].copy();q['observations']=name;q['solution']=label;q['residual_s']=residual[held];details.append(q)
 table=pd.DataFrame(rows);table.to_csv(out/'fixed_observation_scores.csv',index=False);pd.concat(details).to_csv(out/'held_cc_predictions.csv',index=False);idx=table.set_index(['observations','solution','phase']).rms_s
 for name in ['old575','fixed1408']:
  for previous in ['stage45','stage47']:
   ratio=float(idx.loc[(name,'candidate','all')]/idx.loc[(name,previous,'all')]);result[name+'_'+previous+'_ratio']=ratio;result['gates'][name+'_'+previous+'_non_degradation']=ratio<=1.05
 current=pd.read_csv(out/'reference_summary.csv').set_index(['branch','catalog'])
 for previous,source in [('stage45',C.BASELINE),('stage47',C.SRC),('stage39',M.HERE/'export/39_support_aware_pairs')]:
  old=pd.read_csv(source/'reference_summary.csv').set_index(['branch','catalog']);ok=all(current.loc[('joint_all',cat),'median_horizontal_km']<=1.1*old.loc[('joint_all',cat),'median_horizontal_km'] for cat in ['Liu','Official','Shelly']) and current.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*old.loc[('joint_all','Shelly'),'median_abs_depth_km'];result['gates'][previous+'_reference_non_degradation']=bool(ok)
 p=C.problem(template,True);old=pd.read_csv(C.SRC/'cc_measurements.csv');old=old[old.accepted&~old.training&old.event_id_a.isin(p.e.event_id)&old.event_id_b.isin(p.e.event_id)];oldkeys=set(zip(old.pick_id_a,old.pick_id_b));newkeys=set(zip(p.c.loc[~p.c.training,'pick_id_a'],p.c.loc[~p.c.training,'pick_id_b']));assert len(oldkeys)==1408 and oldkeys<=newkeys
 event=pd.read_csv(out/'events.csv');target=event[event.branch.eq('joint_all')&event.role.eq('reserve')].copy();base=pd.read_csv(C.BASELINE/'events.csv').query("branch=='joint_all'").set_index('event_id');target['stage45_depth_km']=target.event_id.map(base.depth_km);target['depth_change_km']=target.depth_km-target.stage45_depth_km;target.to_csv(out/'target_changes.csv',index=False)
 result['experiment_branch']=args.branch;result['candidate_branch']='refreshed';result['median_depth_change_from_stage45_km']=float(target.depth_change_km.median());result['reserve3_used']=False;result['all_gates_passed']=all(result['gates'].values());result['decision']=('development_passed_requires_fresh_confirmation' if result['all_gates_passed'] else 'do_not_promote') if args.branch=='refreshed' else 'attribution_control_only';M.save(out/'run.json',result)
 (out/'RESULTS.md').write_text('# Differential-only S: '+args.branch+'\n\nDecision: **'+result['decision']+'**. The refreshed branch is the sole promotion candidate. The fixed graph is an attribution control; neither is a new full catalog.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\n## Identical old held observations\n\n```text\n'+table.to_string(index=False)+'\n```\n\nAll old observations, targets and auxiliary flags remain. Every eqs47_ observation is retained as a prediction/CC row but omitted uniformly from the absolute objective; observation_usage.csv records that distinction. References are not truth or fitting targets. No source-depth alignment or gate changes are allowed.\n')
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 fig,axes=plt.subplots(1,3,figsize=(10,3.2),layout='constrained');xx=np.arange(3);metric=pd.read_csv(out/'metrics.csv').set_index(['branch','kind']);oldmetric=pd.read_csv(C.BASELINE/'metrics.csv').set_index(['branch','kind'])
 aa=[oldmetric.loc[('joint_withheld','absolute'),'rms_s']]+[idx.loc[(name,'stage45','all')] for name in ['old575','fixed1408']];bb=[metric.loc[('joint_withheld','absolute'),'rms_s']]+[idx.loc[(name,'candidate','all')] for name in ['old575','fixed1408']]
 axes[0].bar(xx-.18,aa,.36,color='#666666',label='Stage 45');axes[0].bar(xx+.18,bb,.36,color='#0072B2',label=args.branch.capitalize());axes[0].set(xticks=xx,xticklabels=['Arrivals','CC 575','CC 1408'],ylabel='Held-out RMS (s)',yscale='log');axes[0].legend(frameon=False,fontsize=8)
 oldref=pd.read_csv(C.BASELINE/'reference_summary.csv').set_index(['branch','catalog']);cats=['Liu','Official','Shelly'];axes[1].bar(xx-.18,[oldref.loc[('joint_all',c),'median_horizontal_km'] for c in cats],.36,color='#666666');axes[1].bar(xx+.18,[current.loc[('joint_all',c),'median_horizontal_km'] for c in cats],.36,color='#0072B2');axes[1].set(xticks=xx,xticklabels=cats,ylabel='Median horizontal difference (km)')
 axes[2].scatter(target.stage45_depth_km,target.depth_km,s=12,alpha=.6,color='#0072B2');axes[2].plot([0,25],[0,25],color='black',lw=.8);axes[2].set(xlim=(0,25),ylim=(0,25),xlabel='Stage 45 depth (km)',ylabel='Differential-only depth (km)')
 for ax,letter in zip(axes,'abc'):ax.text(0,1.04,letter,transform=ax.transAxes,fontweight='bold')
 for suffix in ['png','pdf']:fig.savefig(out/('comparison.'+suffix),dpi=220)
 plt.close(fig)
 for f,h in json.loads((out/'location_design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
