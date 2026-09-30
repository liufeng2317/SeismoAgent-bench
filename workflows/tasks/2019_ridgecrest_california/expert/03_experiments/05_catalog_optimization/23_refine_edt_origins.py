#!/usr/bin/env python3
"""Round 03: fit-only analytic origins at frozen EDT xyz and paired station-omission stability."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import importlib.util,json,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('origin_helpers',HERE/'03_experiments/04_velocity_model/20_test_hk_model.py')
H=importlib.util.module_from_spec(spec);sys.modules[spec.name]=H;spec.loader.exec_module(H)
OUT=HERE/'export/23_edt_origins';SOURCE=HERE/'export/22_edt_likelihood'


def main():
    OUT.mkdir(exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
    files=[Path(__file__),Path(H.__file__),Path(H.DIAG.__file__),SOURCE/'tables/events.csv',SOURCE/'tables/fit_phases.csv',SOURCE/'tables/heldout_predictions.csv',SOURCE/'tables/reference_summary.csv',SOURCE/'run.json',HERE/'export/10_validate_catalog/phases.csv',H.BASE/'stations.csv',HERE/'docs/optimization_reserved_events.csv']
    files+=list((H.BASE/'grids').glob('time.*.time.*'))
    design=dict(round=3,max_rounds=30,intervention='Replace native EDT origin by inverse-total-variance least-squares origin at identical xyz, using fit observations only. No search, offset tuning, or coordinate fitting.',variance='P=.1^2+.3^2; S=.2^2+.3^2, matching baseline.',stability='Paired displacement under the same fixed six-instrument omission for both methods, all 147 events. One perturbation, not a calibrated sampling uncertainty or new bootstrap.',gates='Frozen reference improvement from round02; heldout RMS <=.95 baseline and P/S <=1.05; median and p90 horizontal and absolute-depth omission displacement each <=1.10 baseline. Native posterior widths remain reported in round02 and are not declared improved by changing origin.',source_sha256={str(p):H.sha(p) for p in files})
    path=OUT/'design.json'
    if path.exists():assert json.loads(path.read_text())==design
    else:H.write_json(path,design)
    events=pd.read_csv(SOURCE/'tables/events.csv');fits=pd.read_csv(SOURCE/'tables/fit_phases.csv')
    picks=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False)
    picks=picks[picks.event_id.isin(events.event_id)]
    stations=pd.read_csv(H.BASE/'stations.csv').set_index('id')
    reserved=set(pd.read_csv(HERE/'docs/optimization_reserved_events.csv').event_id);assert not reserved&set(events.event_id)
    held=pd.read_csv(SOURCE/'tables/heldout_predictions.csv')
    p=fits.merge(picks[['pick_id','time_utc']],on='pick_id',validate='many_to_one').merge(events[['branch','event_id','origin_time']+H.XYZ],on=['branch','event_id'],validate='many_to_one').reset_index(drop=True)
    tt,_=H.DIAG.predict(H.BASE/'grids',p,stations)
    p['residual_exact_s']=(pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-tt
    p['inverse_variance']=1/(.3**2+np.where(p.phase.eq('P'),.1,.2)**2)
    updates=[]
    for (branch,eid),q in p.groupby(['branch','event_id']):
        shift=float(np.average(q.residual_exact_s,weights=q.inverse_variance))
        centered=q.residual_exact_s-shift
        assert abs(float(np.average(centered,weights=q.inverse_variance)))<1e-12
        assert np.average(centered**2,weights=q.inverse_variance)<=np.average(q.residual_exact_s**2,weights=q.inverse_variance)+1e-12
        updates.append(dict(branch=branch,event_id=eid,origin_shift_s=shift,n_fit=len(q)))
    updates=pd.DataFrame(updates)
    baseline_error=float(updates[updates.branch.isin(['control','withheld_control'])].origin_shift_s.abs().max());assert baseline_error<.0002
    events=events.merge(updates,on=['branch','event_id'],validate='one_to_one')
    # Preserve native diagnostics explicitly when exporting changed origins.
    events=events.rename(columns={'rms_residual_s':'native_quality_misfit','rms_unweighted_s':'native_rms_unweighted_s','origin_time_shift_s':'native_origin_time_shift_s'})
    residuals=p.merge(updates[['branch','event_id','origin_shift_s']],on=['branch','event_id'],validate='many_to_one')
    residuals['refined_residual_s']=residuals.residual_exact_s-residuals.origin_shift_s
    newrms=residuals.groupby(['branch','event_id']).refined_residual_s.apply(H.rms).rename('rms_unweighted_s').reset_index()
    events=events.merge(newrms,on=['branch','event_id'],validate='one_to_one')
    events['native_origin_time']=events.origin_time
    events['origin_time']=(pd.to_datetime(events.origin_time,utc=True,format='ISO8601')+pd.to_timedelta(events.origin_shift_s,unit='s')).astype(str)
    assert len(events)==588
    # Apply fit-only shifts to held-out predictions; never estimate their mean for fitting.
    after=held.merge(updates,on=['branch','event_id'],validate='many_to_one')
    after['native_residual_s']=after.residual_s
    after['residual_s']=after.residual_s-after.origin_shift_s
    after['origin_time']=after.origin_time.astype(str)
    metrics=[]
    for branch,g in after.groupby('branch'):
        for phase,q in [('all',g),('P',g[g.phase.eq('P')]),('S',g[g.phase.eq('S')])]:
            for variant,col in [('native','native_residual_s'),('analytic_origin','residual_s')]:
                metrics.append(dict(branch=branch,variant=variant,phase=phase,n=len(q),rms_s=H.rms(q[col]),median_abs_s=q[col].abs().median()))
    metrics=pd.DataFrame(metrics)
    stability=[]
    for method in ['control','edt']:
        a=events[events.branch.eq(method)].set_index('event_id');b=events[events.branch.eq('withheld_'+method)].set_index('event_id').loc[a.index]
        for eid in a.index:
            dx=b.loc[eid,'x_km']-a.loc[eid,'x_km'];dy=b.loc[eid,'y_km']-a.loc[eid,'y_km'];dz=b.loc[eid,'depth_km']-a.loc[eid,'depth_km']
            stability.append(dict(method=method,event_id=eid,horizontal_km=float(np.hypot(dx,dy)),absolute_depth_km=abs(dz),shift_3d_km=float(np.sqrt(dx*dx+dy*dy+dz*dz))))
    stability=pd.DataFrame(stability);summary=[]
    for method,g in stability.groupby('method'):
        row=dict(method=method,n=len(g))
        for name in ['horizontal_km','absolute_depth_km','shift_3d_km']:
            row['median_'+name]=g[name].median();row['p90_'+name]=g[name].quantile(.9)
        summary.append(row)
    summary=pd.DataFrame(summary);mt=metrics.set_index(['branch','variant','phase']);st=summary.set_index('method')
    ratios={p:float(mt.loc[('withheld_edt','analytic_origin',p),'rms_s']/mt.loc[('withheld_control','native',p),'rms_s']) for p in ['all','P','S']}
    sr={name:float(st.loc['edt',name]/st.loc['control',name]) for name in ['median_horizontal_km','p90_horizontal_km','median_absolute_depth_km','p90_absolute_depth_km']}
    gates=dict(origin_identity=baseline_error<.0002,reference=bool(json.loads((SOURCE/'run.json').read_text())['gates']['reference']),heldout=bool(ratios['all']<=.95 and ratios['P']<=1.05 and ratios['S']<=1.05),omission_stability=bool(all(v<=1.10 for v in sr.values())))
    result=dict(round=3,decision='candidate_for_further_independent_validation' if all(gates.values()) else 'do_not_promote',gates=gates,heldout_ratios=ratios,stability_ratios=sr,baseline_origin_reproduction_max_s=baseline_error,median_edt_origin_shift_s=float(updates[updates.branch.eq('edt')].origin_shift_s.median()),n_fixed_locations=len(events),no_new_spatial_solutions=True)
    # Keep new timing metadata self-consistent in every exported table.
    after['native_origin_time']=after.origin_time
    after['origin_time']=(pd.to_datetime(after.origin_time,utc=True,format='ISO8601')+pd.to_timedelta(after.origin_shift_s,unit='s')).astype(str)
    for name,df in dict(events=events,origin_updates=updates,heldout_predictions=after,heldout_metrics=metrics,omission_displacements=stability,omission_summary=summary).items():df.to_csv(OUT/f'tables/{name}.csv',index=False)
    H.write_json(OUT/'run.json',result)
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(1,3,figsize=(10,3),layout='constrained')
    for method,label,col in [('control','Baseline','#2878B5'),('edt','EDT','#D65F24')]:
        g=stability[stability.method.eq(method)]
        for ax,key in zip(axes[:2],['horizontal_km','absolute_depth_km']):
            values=np.sort(g[key]);ax.plot(values,np.arange(1,len(values)+1)/len(values),label=label,color=col)
    axes[0].set(xlabel='Station-omission horizontal shift (km)',ylabel='Cumulative fraction');axes[0].legend(frameon=False)
    axes[1].set(xlabel='Station-omission depth shift (km)',ylabel='Cumulative fraction')
    q=after[after.branch.eq('withheld_edt')]
    for label,key in [('Native origin','native_residual_s'),('Analytic origin','residual_s')]:
        values=np.sort(q[key].abs());axes[2].plot(values,np.arange(1,len(values)+1)/len(values),label=label)
    axes[2].set(xlabel='EDT withheld absolute residual (s)',ylabel='Cumulative fraction',xlim=(0,2));axes[2].legend(frameon=False)
    for label,ax in zip('abc',axes):ax.set_title(label,loc='left',fontweight='bold')
    for ext in ['png','pdf']:fig.savefig(OUT/f'comparison.{ext}',dpi=220)
    plt.close(fig)
    table=lambda df:df.to_string(index=False,float_format=lambda v:f'{v:.5f}')
    (OUT/'README.md').write_text(f'''# Round 03: EDT origins and matched omission stability

Decision: **{result['decision']}**. Spatial positions remain exactly those of round 02. New origins are an experimental timing product, not a new full catalog. No reserved events or reference coordinates enter fitting.

## Intervention

At each fixed location, compute origin shift = sum(w * (arrival - native_origin - predicted_time)) / sum(w), with w=1/(model_error² + pick_error²). P error 0.1 s, S 0.2 s, model error 0.3 s. Use only the arrivals in that branch's location fit. Apply the resulting shift to held-out predictions without recentering them. This is a conditional analytic origin estimate, not another spatial inversion. The original Gaussian analytic origins reproduce to {baseline_error:.8f} s. Weighted training squared residual cannot increase; every group is checked. Spatial coordinates and their conditional posterior sigmas are unchanged.

## Withheld arrival prediction

```text
{table(metrics)}
```

## Common station-omission comparison

Use the already completed all-station versus six-instrument-withheld solutions for both methods, all 147 identical events. Compare spatial displacement under exactly the same removed observations, independent of native posterior normalization. This is one fixed perturbation, not a bootstrap distribution, a proof of absolute accuracy, or a calibration of posterior coverage. The reserved sample remains unused.

```text
{table(summary)}
```

## Gates

```text
{table(pd.DataFrame([dict(gate=k,passed=v) for k,v in gates.items()]))}
```

Round-02 posterior-width and held-out gates remain failed as originally recorded. This round explicitly evaluates a new origin estimator and a directly comparable perturbation metric; it does not retroactively change that decision. Passing would only support independent validation, not full adoption. Reference differences remain inherited, because xyz is unchanged.

## Reproduction and outputs

Run `python -u 03_experiments/05_catalog_optimization/23_refine_edt_origins.py` in seismoagent. Tables preserve native/new origins, fit-only shifts, all held-out predictions, and event-by-event omission displacements. Comparison figure is available as PNG/PDF. design.json freezes intervention/gates/source identities; run.json summarizes checks and decision. No native solutions, waveforms, picks or earlier outputs were modified.
''')
    print(json.dumps(result,indent=2),flush=True);print(table(metrics),flush=True);print(table(summary),flush=True)

if __name__=='__main__':main()
