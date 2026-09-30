#!/usr/bin/env python3
"""Evaluate frozen joint-location candidates; never fit reference coordinates."""
from pathlib import Path
import importlib.util,json
import numpy as np
import pandas as pd
from pyproj import CRS,Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
spec=importlib.util.spec_from_file_location('joint33',Path(__file__).with_name('33_joint_location.py'));M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
p=M.Problem();out=M.OUT;e=pd.read_csv(out/'events.csv');metrics=pd.read_csv(out/'metrics.csv');anchor=pd.read_csv(out/'anchor_metrics.csv');status=pd.read_csv(out/'solver_status.csv')
base=p.e.copy();base['branch']='original_nll';e=pd.concat([e,base[['event_id','branch']+M.XYZ]],ignore_index=True)
match=pd.read_csv(M.HERE/'export/10_validate_catalog/reference_matches.csv');match=match[match.event_id.isin(base.event_id)&match.matched&~match.ambiguous]
refs=pd.read_csv(M.HERE/'export/05_review_catalog/reference_events.csv');match=match.merge(refs[['catalog','reference_id','longitude','latitude']],on=['catalog','reference_id'],validate='many_to_one')
proj=Transformer.from_crs(4326,CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km'),always_xy=True);rx,ry=proj.transform(match.longitude.to_numpy(),match.latitude.to_numpy());match['rx']=rx;match['ry']=ry
rows=[];details=[]
for branch,g in e.groupby('branch'):
 if branch.endswith('withheld'):continue
 q=match.merge(g[['event_id']+M.XYZ],on='event_id',validate='many_to_one');q['horizontal_km']=np.hypot(q.x_km-q.rx,q.y_km-q.ry);q['absolute_depth_km']=np.where(q.catalog.eq('Shelly'),abs(q.depth_km-q.reference_depth_km),np.nan);q['branch']=branch;details.append(q)
 for catalog,h in q.groupby('catalog'):rows.append({'branch':branch,'catalog':catalog,'n':len(h),'median_horizontal_km':h.horizontal_km.median(),'median_abs_depth_km':h.absolute_depth_km.median()})
r=pd.DataFrame(rows);r.to_csv(out/'reference_summary.csv',index=False);pd.concat(details).to_csv(out/'reference_comparison.csv',index=False)
# Independently score archived NLL six-station-withheld control on identical 923 picks.
b=pd.read_csv(M.HERE/'export/20_velocity_model_qualification/tables/events.csv');b=b[b.branch.eq('withheld_control')].set_index('event_id').loc[p.e.event_id];assert len(b)==147
x=np.column_stack([b[M.XYZ].to_numpy(),pd.to_datetime(b.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9-p.t0]);t,_=p.prediction(x.ravel());original_rms=float(np.sqrt(np.mean((t[~p.train]-p.obs[~p.train])**2)))
idx=metrics.set_index(['branch','kind']);ratio_cc=float(idx.loc[('joint_withheld','cc'),'rms_s']/idx.loc[('absolute_withheld','cc'),'rms_s']);ratio_abs=float(idx.loc[('joint_withheld','absolute'),'rms_s']/idx.loc[('absolute_withheld','absolute'),'rms_s'])
refs_pass=True;rs=r.set_index(['branch','catalog'])
for control in ['absolute_all','original_nll']:
 for cat in ['Liu','Official','Shelly']:
  refs_pass &= bool(rs.loc[('joint_all',cat),'median_horizontal_km']<=1.1*rs.loc[(control,cat),'median_horizontal_km'])
 refs_pass &= bool(rs.loc[('joint_all','Shelly'),'median_abs_depth_km']<=1.1*rs.loc[(control,'Shelly'),'median_abs_depth_km'])
near={branch:int(((g.depth_km<.5)|(g.depth_km>24.5)).sum()) for branch,g in e.groupby('branch')}
a=anchor[anchor.branch.eq('joint_withheld')]
gates={'all_solvers_terminate':bool(len(status)==16 and status.success.all()),'held_cc':ratio_cc<=.95,'held_absolute':bool(ratio_abs<=1.05 and idx.loc[('joint_withheld','absolute'),'rms_s']<=1.05*original_rms),'references':bool(refs_pass),'anchor':bool(a.mean_shift_km.le(.1).all() and a.p90_shift_km.le(.2).all()),'boundary':near['joint_all']<=near['original_nll']+3}
result={'round':12,'decision':'qualifies_for_broader_validation' if all(gates.values()) else 'do_not_promote','gates':gates,'held_cc_ratio':ratio_cc,'held_absolute_ratio':ratio_abs,'archived_nll_held_absolute_rms_s':original_rms,'near_boundary_counts':near,'confirmation_used':False,'full_catalog_adopted':False,'numerical_caveat':'Termination is ftol, not proof of vanishing gradient/global minimum. Piecewise grid derivatives; recorded optimality and multi-start behavior retained. No formal posterior uncertainty is produced.'};M.save(out/'run.json',result)
fig,axes=plt.subplots(1,2,figsize=(8,3.4),layout='constrained')
for ax,kind in zip(axes,['absolute','cc']):
 vals=[idx.loc[(b,kind),'rms_s'] for b in ['absolute_withheld','joint_withheld']];ax.bar(['Absolute only','Joint'],vals,color=['#666666','#0072B2']);ax.set_ylabel('Held-out RMS (s)');ax.set_title('Absolute arrivals' if kind=='absolute' else 'CC differential times')
fig.savefig(out/'heldout_comparison.png',dpi=220);fig.savefig(out/'heldout_comparison.pdf');plt.close(fig)
(out/'README.md').write_text('''# Round 12: joint absolute and CC differential location

Decision: **'''+result['decision']+'''**. This is a 147-event fixed-cohort pilot, not a full catalog or independent confirmation. All 16 solves terminate by the cost-change criterion; nonzero gradient optimality remains recorded. No reference locations enter the objective.

The model, receiver elevations and interpolated travel times are identical for absolute and differential terms. All 5,413 associated absolute picks are retained in primary fits; 1,162 accepted CC edges enter the joint primary fit. Both terms exclude the same six stations for prediction tests (923 withheld absolute observations and 160 CC edges). No catalog differential rows are added. Absolute errors retain the original 0.3 s model term plus P/S pick errors; the fixed CC working error is 0.05 s. Edge/shared-waveform correlations are not whitened and this error is not a calibrated posterior uncertainty.

## Prediction and fixed reference comparisons

Only branches ending in `withheld` represent withheld prediction. The same station subset in `all` branches was fitted and is NOT an independent test.

```text
'''+metrics.to_string(index=False)+'''\n```

```text
'''+r.to_string(index=False)+'''\n```

```text
'''+json.dumps(result,indent=2)+'''\n```

Common ±1 km initial translations produce at most '''+f'{a.mean_shift_km.max():.5f}'+''' km mean displacement and '''+f'{a.p90_shift_km.max():.5f}'+''' km P90 displacement in withheld joint solutions. These checks establish local initialization stability, not true accuracy. Historical pick/CC eligibility used upstream all-station solutions, so observation holdouts are not fully blind end-to-end tests.

[Prediction figure](heldout_comparison.png). `design.json` freezes weights, inputs and gates; `numerical_checks.json` verifies native-grid prediction and the sparse analytic Jacobian; `solver_status.csv` retains every optimization termination. No formal uncertainty, magnitude update, reserve validation or full production has been performed. Preserve v1.
''')
print(json.dumps(result,indent=2));print(r.to_string(index=False))
