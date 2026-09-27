#!/usr/bin/env python3
"""Audit and plot completed frozen confirmation without changing selection or fits."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'export/51_confirmation'
COLORS={'Original NLL':'#777777','Absolute only':'#E69F00','Joint':'#0072B2'}

def audit_confirmation():
 root=HERE;out=OUT
 files=['design.json','observations/design.json','observations/model_identity.json','graph_design.json','cc_processing/design.json','location_design.json','native_controls/design.json'];expected={}
 for name in files:
  for p,h in json.loads((out/name).read_text())['source_sha256'].items():
   assert p not in expected or expected[p]==h,p
   expected[p]=h
 for p,h in json.loads((root/'export/50_uncertain_depth_pairs/frozen_candidate.json').read_text())['source_sha256'].items():
  assert p not in expected or expected[p]==h,p
  expected[p]=h
 for p,h in expected.items():
  a=hashlib.sha256()
  with Path(p).open('rb') as f:
   for block in iter(lambda:f.read(1024*1024),b''):a.update(block)
  assert a.hexdigest()==h,p
 run=json.loads((out/'run.json').read_text());status=pd.read_csv(out/'solver_status.csv');assert len(status)==16 and status.success.all()
 e=pd.read_csv(out/'inputs/events.csv');targets=set(e[e.role.eq('reserve')].event_id);assert targets==set(pd.read_csv(root/'docs/optimization_reserved_events_v3.csv').event_id) and len(targets)==300
 positions=pd.read_csv(out/'events.csv');joint=positions[positions.branch.eq('joint_all')&positions.role.eq('reserve')];assert set(joint.event_id)==targets;near=(joint.depth_km<.5)|(joint.depth_km>24.5);assert int(near.sum())==6
 original=e[e.event_id.isin(targets)];assert int(((original.depth_km<.5)|(original.depth_km>24.5)).sum())==0
 metrics=pd.read_csv(out/'metrics.csv').set_index(['branch','kind']);ref=pd.read_csv(out/'reference_summary.csv').set_index(['branch','catalog']);anchor=pd.read_csv(out/'anchor_metrics.csv').query("branch=='joint_withheld'");coverage=run['coverage']
 cc=pd.read_csv(out/'cc_measurements.csv');auxids=set(e[e.auxiliary_eligible].event_id);cc=cc[cc.accepted&cc.event_id_a.isin(auxids)&cc.event_id_b.isin(auxids)];training=cc[cc.training];held=cc[~cc.training];independent_coverage={'primary_reserve':len(targets),'auxiliary_reserve':len(targets&auxids),'training_cc_reserve':len((set(training.event_id_a)|set(training.event_id_b))&targets),'held_cc_reserve':len((set(held.event_id_a)|set(held.event_id_b))&targets),'held_cc_edges':len(held)};assert independent_coverage==coverage
 for row in status.itertuples():
  expected_ids=set(e[e.auxiliary_eligible].event_id) if row.branch.endswith('_withheld') else set(e.event_id)
  with np.load(out/(row.branch+'_'+row.start+'.npz')) as fit:
   assert set(fit['event_id'])==expected_ids and len(fit['event_id'])==len(expected_ids)
   assert fit['x'].shape==(len(expected_ids),4) and np.isfinite(fit['x']).all()
   assert np.all((fit['x'][:,2]>=0)&(fit['x'][:,2]<=25))
 
 refok=True
 for ctrl in ['absolute_all','original_nll']:
  for cat in ['Liu','Official','Shelly']:refok &= ref.loc[('joint_all',cat),'median_horizontal_km']<=1.1*ref.loc[(ctrl,cat),'median_horizontal_km']
  refok &= ref.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*ref.loc[(ctrl,'Shelly'),'median_abs_depth_km']
 recomputed={'coverage':coverage['primary_reserve']==300 and coverage['auxiliary_reserve']>=240 and coverage['training_cc_reserve']>=210 and coverage['held_cc_reserve']>=50 and coverage['held_cc_edges']>=100,'termination':bool(status.success.all()),'held_cc':bool(metrics.loc[('joint_withheld','cc'),'rms_s']<=.95*metrics.loc[('absolute_withheld','cc'),'rms_s']),'held_absolute':bool(metrics.loc[('joint_withheld','absolute'),'rms_s']<=1.05*metrics.loc[('absolute_withheld','absolute'),'rms_s'] and metrics.loc[('joint_withheld','absolute'),'rms_s']<=1.05*run['original_nll_held_absolute_rms_s']),'references':bool(refok),'anchor':bool(anchor.mean_shift_km.le(.1).all() and anchor.p90_shift_km.le(.2).all()),'boundary':bool(near.sum()<=3)}
 assert recomputed==run['gates'] and not run['all_gates_passed'] and not run['full_catalog_adopted']
 for name in ['51_graph','51_measure','51_run','51_evaluate','51_continue']:assert (root/'03_experiments/15_confirmation/logs'/f'{name}.exitcode').read_text().strip()=='0'
 result={'rounds_completed':30,'objective_achieved':False,'confirmation_all_gates_passed':False,'failed_gate':'boundary','source_identities_verified':len(expected),'successful_fits':len(status),'retained_confirmation_targets':len(targets),'boundary_targets':int(near.sum()),'boundary_limit':3,'gates_recomputed_from_outputs':recomputed,'full_catalog_adopted':False,'next_optimization_authorized':False,'current_full_product':'export/10_validate_catalog (v1, unchanged source identity)','audit_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'audit_scope':'Frozen source identities, all16 fits, every confirmation gate, target retention and pipeline exit status. This audit does not convert a failed confirmation into full-product success.'}
 (out/'completion_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

def main():
 audit_confirmation()
 result=json.loads((OUT/'run.json').read_text())
 assert result['round']==30 and result['reserve_v3_used'] and not result['full_catalog_adopted']
 statuses=pd.read_csv(OUT/'solver_status.csv');assert len(statuses)==16
 metrics=pd.read_csv(OUT/'metrics.csv').set_index(['branch','kind'])
 references=pd.read_csv(OUT/'reference_summary.csv').set_index(['branch','catalog'])
 original=pd.read_csv(OUT/'inputs/events.csv');original=original[original.role.eq('reserve')].set_index('event_id')
 located=pd.read_csv(OUT/'events.csv');located=located[located.role.eq('reserve')&located.branch.eq('joint_all')].set_index('event_id')
 assert len(original)==len(located)==300 and set(original.index)==set(located.index)
 located=located.loc[original.index]
 absolute=pd.read_csv(OUT/'events.csv');absolute=absolute[absolute.role.eq('reserve')&absolute.branch.eq('absolute_all')].set_index('event_id').loc[original.index]
 boundary=(located.depth_km<.5)|(located.depth_km>24.5)
 audit=original.loc[boundary,['origin_time','depth_km','posterior_mean_depth_km','posterior_sigma_depth_km','n_phases','n_stations','auxiliary_eligible']].copy().rename(columns={'depth_km':'original_depth_km','posterior_mean_depth_km':'original_posterior_mean_depth_km','posterior_sigma_depth_km':'original_posterior_sigma_depth_km'})
 audit['absolute_depth_km']=absolute.loc[audit.index,'depth_km'];audit['joint_depth_km']=located.loc[audit.index,'depth_km'];audit['absolute_near_boundary']=(audit.absolute_depth_km<.5)|(audit.absolute_depth_km>24.5);audit['joint_depth_change_km']=audit.joint_depth_km-audit.original_depth_km
 cc=pd.read_csv(OUT/'cc_measurements.csv');cc=cc[cc.accepted];ph=pd.read_csv(OUT/'inputs/all_phases.csv',low_memory=False);auxids=set(pd.read_csv(OUT/'inputs/events.csv').query('auxiliary_eligible').event_id)
 for eid in audit.index:
  incident=cc[cc.event_id_a.eq(eid)|cc.event_id_b.eq(eid)];training=incident[incident.training];eligible=training[training.event_id_a.isin(auxids)&training.event_id_b.isin(auxids)]
  audit.loc[eid,'primary_all_cc_edges']=len(incident);audit.loc[eid,'primary_all_cc_instruments']=incident.instrument_id.nunique();audit.loc[eid,'primary_held_cc_edges']=int((~incident.training).sum());audit.loc[eid,'primary_training_cc_edges']=len(training);audit.loc[eid,'primary_training_cc_instruments']=training.instrument_id.nunique();audit.loc[eid,'primary_training_cc_neighbors']=len((set(training.event_id_a)|set(training.event_id_b))-{eid});audit.loc[eid,'auxiliary_training_cc_edges']=len(eligible)
  picks=ph[ph.event_id.eq(eid)];audit.loc[eid,'all_P_picks']=int(picks.phase.eq('P').sum());audit.loc[eid,'all_S_picks']=int(picks.phase.eq('S').sum());audit.loc[eid,'relative_only_EQ_S']=int(picks.pick_id.str.startswith('eqs47_').sum())
 assert len(audit)==result['near_boundary_counts']['joint_all']
 audit.to_csv(OUT/'boundary_review.csv',index_label='event_id')
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
 fig,axes=plt.subplots(2,2,figsize=(9.2,6.8),layout='constrained')
 names=['Original NLL','Absolute only','Joint']
 values=[result['original_nll_held_absolute_rms_s'],metrics.loc[('absolute_withheld','absolute'),'rms_s'],metrics.loc[('joint_withheld','absolute'),'rms_s']]
 axes[0,0].bar(names,values,color=[COLORS[n] for n in names],width=.65)
 axes[0,0].set_ylabel('Held-out arrival RMS (s)');axes[0,0].set_ylim(bottom=0)
 names=['Absolute only','Joint'];values=[metrics.loc[(b,'cc'),'rms_s'] for b in ['absolute_withheld','joint_withheld']]
 axes[0,1].bar(names,values,color=[COLORS[n] for n in names],width=.55)
 axes[0,1].set_ylabel('Held-out differential RMS (s)');axes[0,1].set_ylim(bottom=0)
 catalogs=['Liu','Official','Shelly'];x=np.arange(3);width=.24
 for i,(branch,label) in enumerate([('original_nll','Original NLL'),('absolute_all','Absolute only'),('joint_all','Joint')]):
  values=[references.loc[(branch,c),'median_horizontal_km'] for c in catalogs]
  axes[1,0].bar(x+(i-1)*width,values,width,color=COLORS[label],label=label)
 axes[1,0].set_xticks(x,catalogs);axes[1,0].set_ylabel('Median horizontal discrepancy (km)');axes[1,0].set_ylim(0,1.25*references.median_horizontal_km.max());axes[1,0].legend(frameon=False,fontsize=8,loc='upper center',ncol=3)
 before=original.depth_km.to_numpy();after=located.depth_km.to_numpy();boundary=(after<.5)|(after>24.5)
 axes[1,1].scatter(before[~boundary],after[~boundary],s=10,c=COLORS['Joint'],alpha=.65,linewidths=0,label='Joint')
 axes[1,1].scatter(before[boundary],after[boundary],s=23,facecolors='none',edgecolors='#D55E00',linewidths=.8,label='Boundary flagged')
 axes[1,1].plot([0,25],[0,25],color='black',lw=.7)
 axes[1,1].set(xlabel='Original NLL depth (km)',ylabel='Joint depth (km)',xlim=(-.3,25.3),ylim=(-.3,25.3));axes[1,1].legend(frameon=False,fontsize=8)
 for letter,ax in zip('abcd',axes.ravel()):
  ax.set_title(letter,loc='left',fontweight='bold');ax.tick_params(direction='out',length=3,width=.7)
 dest=OUT/'figures';dest.mkdir(exist_ok=True)
 for extension in ['png','pdf']:fig.savefig(dest/f'confirmation_overview.{extension}',dpi=240)
 plt.close(fig)
 (dest/'README.md').write_text('''# Confirmation comparison figure

`confirmation_overview.png` and `.pdf` show completed round30 results with unchanged event identities and scoring rules.

- **a:** held-station absolute-arrival RMS on the same eligible confirmation targets. Original NLL is the native six-instrument omission control; the other bars are matched withheld fits.
- **b:** held waveform differential-time RMS on the identical measured edge set, comparing absolute-only and joint withheld fits.
- **c:** primary-fit median horizontal discrepancies on the original unambiguous reference pairs for each catalogue. Each catalogue retains its own pair count; no rematching is performed.
- **d:** all300 confirmation targets, comparing original and joint primary depths on the benchmark's shared +0.7km datum plane. Orange rings mark depths below0.5km or above24.5km; no target is removed or clipped for display.

These panels are descriptive. The complete gate decision, nominal Shelly depth comparison, coverage and multi-start checks remain in `../RESULTS.md` and `../run.json`. Reference catalogues are not ground truth; shared supports and upstream catalogue exposure limit independence. The plotted experiment is not an adopted full catalogue.
''')
 print('Saved',dest/'confirmation_overview.png',flush=True)
if __name__=='__main__':main()
