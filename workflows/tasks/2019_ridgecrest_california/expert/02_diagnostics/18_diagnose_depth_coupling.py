#!/usr/bin/env python3
"""Attribute fixed station corrections to depth sensitivity; no inversions or tuning."""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threadpool_limits(1)
HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'export/18_depth_coupling'
PRE=HERE/'export/17_station_corrections'
BASE=HERE/'export/04_locate_nonlinloc'
XYZ=['x_km','y_km','depth_km']
spec=importlib.util.spec_from_file_location('coupling_grids',HERE/'02_diagnostics/16_diagnose_systematics.py')
D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    events=pd.read_csv(PRE/'tables/events.csv')
    a=events[events.branch.eq('control')].set_index('event_id')
    b=events[events.branch.eq('corrected')].set_index('event_id').loc[a.index]
    p=pd.read_csv(HERE/'export/16_diagnose_systematics/pick_diagnostics.csv')
    p=p[p.event_id.isin(a.index)].drop(columns=XYZ+['origin_time']).merge(a[XYZ+['origin_time']],on='event_id',validate='many_to_one').reset_index(drop=True)
    corrections=pd.read_csv(PRE/'tables/corrections.csv').set_index(['instrument_id','phase']).proposed_tt_correction_s
    p['correction_s']=[corrections.get((r.instrument_id,r.phase),0.) for r in p.itertuples()]
    p['supported']=[(r.instrument_id,r.phase) in corrections.index for r in p.itertuples()]
    stations=pd.read_csv(BASE/'stations.csv').set_index('id')
    tt,grad=D.predict(BASE/'grids',p,stations)
    layer_tt,layer_grad=D.predict(HERE/'export/06_diagnose_depth/layered_grids',p,stations)
    # Validate exact implemented derivatives, not a separate velocity approximation.
    checks={}
    for j,key in enumerate(XYZ):
        plus=p.copy();minus=p.copy();plus[key]+=1e-5;minus[key]-=1e-5
        numerical=(D.predict(BASE/'grids',plus,stations)[0]-D.predict(BASE/'grids',minus,stations)[0])/2e-5
        checks[key+'_gradient_max_error']=float(np.max(np.abs(numerical-grad[:,j])))
        assert checks[key+'_gradient_max_error']<1e-4
    native=pd.read_csv(PRE/'tables/fit_phases.csv').query("branch == 'control'").set_index('pick_id')
    checks['native_tt_max_error_s']=float(np.max(np.abs(tt-native.loc[p.pick_id,'predicted_travel_time_s'].to_numpy())))
    assert checks['native_tt_max_error_s']<.0002
    endpoint=p.drop(columns=XYZ+['origin_time']).merge(b[XYZ+['origin_time']],on='event_id',validate='many_to_one')
    assert (endpoint.pick_id.to_numpy()==p.pick_id.to_numpy()).all()
    final_tt,_=D.predict(BASE/'grids',endpoint,stations)
    # Same per-pick variances as the fixed NLL Gaussian observation/model terms.
    weights=1/(.3**2+np.where(p.phase.eq('P'),.1,.2)**2)
    p['weight']=weights
    contributions=[];rows=[]
    alt=pd.read_csv(HERE/'export/16_diagnose_systematics/station_phase_transfer.csv')
    alt=alt[alt.model.eq('layered_elevated')].set_index(['instrument_id','phase']).development_median_s
    for eid,g in p.groupby('event_id'):
        idx=g.index.to_numpy();w=weights[idx];sw=np.sqrt(w);c=g.correction_s.to_numpy()
        J=np.column_stack([grad[idx],np.ones(len(idx))])
        # Eliminate horizontal position and origin time before evaluating depth.
        nuisance=J[:,[0,1,3]]
        rz=J[:,2]-nuisance@np.linalg.lstsq(nuisance*sw[:,None],J[:,2]*sw,rcond=None)[0]
        kernel=w*rz/np.sum(w*rz**2)
        delta=-np.linalg.lstsq(J*sw[:,None],c*sw,rcond=None)[0]
        assert abs(delta[2]+kernel@c)<1e-8
        assert abs(kernel.sum())<1e-8
        # A uniform time delay has zero depth projection; it changes origin only.
        homogeneous=-np.linalg.lstsq(J*sw[:,None],np.full(len(idx),.2)*sw,rcond=None)[0]
        assert np.max(np.abs(homogeneous[:3]))<1e-8 and abs(homogeneous[3]+.2)<1e-8
        actual=(b.loc[eid,XYZ]-a.loc[eid,XYZ]).to_numpy(float)
        dt=(pd.Timestamp(b.loc[eid,'origin_time'])-pd.Timestamp(a.loc[eid,'origin_time'])).total_seconds()
        exact=final_tt[idx]-tt[idx]+dt
        first=J@np.r_[actual,dt]
        layerJ=np.column_stack([layer_grad[idx],np.ones(len(idx))])
        layer_delta=-np.linalg.lstsq(layerJ*sw[:,None],c*sw,rcond=None)[0]
        altc=np.array([alt.get((r.instrument_id,r.phase),0.) for r in g.itertuples()])
        layer_alt=-np.linalg.lstsq(layerJ*sw[:,None],altc*sw,rcond=None)[0]
        modeled=layer_tt[idx]-tt[idx]
        rows.append(dict(event_id=eid,linear_predicted_depth_shift_km=delta[2],actual_depth_shift_km=actual[2],linear_predicted_dx_km=delta[0],linear_predicted_dy_km=delta[1],actual_dx_km=actual[0],actual_dy_km=actual[1],linear_predicted_origin_shift_s=delta[3],actual_origin_shift_s=dt,
            layered_same_correction_depth_shift_km=layer_delta[2],layered_own_correction_depth_shift_km=layer_alt[2],layer_change_only_local_depth_shift_km=-kernel@modeled,
            conditional_depth_scale_km=1/np.sqrt(np.sum(w*rz**2)),kernel_sum=kernel.sum(),nonlinear_path_rms_s=np.sqrt(np.average((exact-first)**2,weights=w)),
            p_contribution_km=float(np.sum((-kernel*c)[g.phase.eq('P')])),s_contribution_km=float(np.sum((-kernel*c)[g.phase.eq('S')])) ))
        for i,(k,cr) in enumerate(zip(kernel,c)):
            row=g.iloc[i]
            contributions.append(dict(event_id=eid,instrument_id=row.instrument_id,phase=row.phase,distance_km=row.distance_km,correction_s=cr,supported=row.supported,depth_kernel_km_per_s=k,projected_depth_contribution_km=-k*cr,raw_depth_gradient_s_per_km=grad[idx[i],2],depth_gradient_after_nuisance_s_per_km=rz[i]))
    e=pd.DataFrame(rows);q=pd.DataFrame(contributions)
    e.to_csv(OUT/'event_coupling.csv',index=False);q.to_csv(OUT/'pick_contributions.csv',index=False)
    # Zero contributions for unobserved cells when forming cohort mean contributions.
    station=q.groupby(['instrument_id','phase']).agg(n=('event_id','size'),correction_s=('correction_s','first'),sum_depth_contribution_km=('projected_depth_contribution_km','sum'),median_distance_km=('distance_km','median')).reset_index()
    station['mean_cohort_depth_contribution_km']=station.sum_depth_contribution_km/len(e)
    station=station.sort_values('mean_cohort_depth_contribution_km');station.to_csv(OUT/'station_phase_contributions.csv',index=False)
    q['distance_group']=pd.cut(q.distance_km,[0,10,20,40,80,1000],right=False).astype(str)
    bins=q.groupby(['distance_group','phase']).projected_depth_contribution_km.sum().div(len(e)).reset_index(name='mean_cohort_depth_contribution_km')
    bins.to_csv(OUT/'distance_phase_contributions.csv',index=False)
    # One counterfactual, not a depth search: shift DEVELOPMENT hypocenters by +1 km.
    # Recompute centered residual medians on exactly the original observations;
    # use the resulting change only for local attribution at transfer controls.
    dev=pd.read_csv(HERE/'export/16_diagnose_systematics/pick_diagnostics.csv')
    dev=dev[dev.cohort.eq('development')].copy().reset_index(drop=True)
    shifted=dev.copy();shifted.depth_km+=1.
    newtt,_=D.predict(BASE/'grids',shifted,stations)
    dev['shifted_residual_s']=dev.linear_elevated_residual_s-(newtt-dev.linear_elevated_tt_s)
    dev['shifted_centered_s']=dev.shifted_residual_s-dev.groupby('event_id').shifted_residual_s.transform('median')
    basec=dev.groupby(['instrument_id','phase']).linear_elevated_centered_s.median()
    newc=dev.groupby(['instrument_id','phase']).shifted_centered_s.median()
    assert max(abs(basec.loc[k]-v) for k,v in corrections.items())<1e-10
    source=[]
    for event,g in q.groupby('event_id'):
        change=np.array([newc.loc[(r.instrument_id,r.phase)]-corrections.loc[(r.instrument_id,r.phase)] if r.supported else 0. for r in g.itertuples()])
        dz=-g.depth_kernel_km_per_s.to_numpy()@change
        source.append(dict(event_id=event,development_imposed_depth_change_km=1.,transfer_local_depth_change_due_to_new_station_terms_km=dz))
    source=pd.DataFrame(source);source.to_csv(OUT/'source_depth_counterfactual.csv',index=False)
    dc=pd.DataFrame({'original_c_s':corrections,'development_deeper_1km_c_s':newc.reindex(corrections.index)})
    dc.to_csv(OUT/'source_depth_station_terms.csv')
    summary=dict(n_events=len(e),n_picks=len(p),predicted_shallow=int((e.linear_predicted_depth_shift_km<0).sum()),actual_shallow=int((e.actual_depth_shift_km<0).sum()),
        median_predicted_depth_shift_km=float(e.linear_predicted_depth_shift_km.median()),median_actual_depth_shift_km=float(e.actual_depth_shift_km.median()),
        depth_shift_correlation=float(e.linear_predicted_depth_shift_km.corr(e.actual_depth_shift_km)),median_absolute_prediction_error_km=float((e.linear_predicted_depth_shift_km-e.actual_depth_shift_km).abs().median()),
        mean_predicted_depth_shift_km=float(e.linear_predicted_depth_shift_km.mean()),mean_p_contribution_km=float(e.p_contribution_km.mean()),mean_s_contribution_km=float(e.s_contribution_km.mean()),
        layered_same_correction_median_depth_shift_km=float(e.layered_same_correction_depth_shift_km.median()),layered_same_correction_shallow=int((e.layered_same_correction_depth_shift_km<0).sum()),
        layered_own_correction_median_depth_shift_km=float(e.layered_own_correction_depth_shift_km.median()),layered_own_correction_shallow=int((e.layered_own_correction_depth_shift_km<0).sum()),
        layer_change_only_median_depth_shift_km=float(e.layer_change_only_local_depth_shift_km.median()),median_nonlinear_path_rms_s=float(e.nonlinear_path_rms_s.median()),checks=checks)
    summary['development_plus_1km_transfer_median_response_km']=float(source.transfer_local_depth_change_due_to_new_station_terms_km.median())
    summary['development_plus_1km_transfer_deeper_count']=int((source.transfer_local_depth_change_due_to_new_station_terms_km>0).sum())
    files=[Path(__file__),HERE/'02_diagnostics/16_diagnose_systematics.py',PRE/'tables/events.csv',PRE/'tables/corrections.csv',PRE/'tables/fit_phases.csv',HERE/'export/16_diagnose_systematics/pick_diagnostics.csv',HERE/'export/16_diagnose_systematics/station_phase_transfer.csv',BASE/'stations.csv']
    summary['source_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    (OUT/'run.json').write_text(json.dumps(summary,indent=2)+'\n')
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(1,3,figsize=(10,3.2),layout='constrained')
    ax=axes[0];ax.scatter(e.linear_predicted_depth_shift_km,e.actual_depth_shift_km,s=10,alpha=.6)
    lo=min(e.linear_predicted_depth_shift_km.min(),e.actual_depth_shift_km.min())-.2;hi=max(e.linear_predicted_depth_shift_km.max(),e.actual_depth_shift_km.max())+.2
    ax.plot([lo,hi],[lo,hi],'k-',lw=.7);ax.set(xlabel='Linear predicted depth change (km)',ylabel='Observed depth change (km)',xlim=(lo,hi),ylim=(lo,hi))
    ax=axes[1];top=station.reindex(station.mean_cohort_depth_contribution_km.abs().sort_values(ascending=False).index).head(10).sort_values('mean_cohort_depth_contribution_km')
    ax.barh(top.instrument_id+' '+top.phase,top.mean_cohort_depth_contribution_km,color=np.where(top.mean_cohort_depth_contribution_km<0,'#2878B5','#D65F24'))
    ax.axvline(0,color='k',lw=.6);ax.set_xlabel('Mean depth contribution (km)')
    ax=axes[2]
    for label,col in [('Linear, fixed c','linear_predicted_depth_shift_km'),('Layered, fixed c','layered_same_correction_depth_shift_km'),('Layered, own c','layered_own_correction_depth_shift_km')]:
        v=np.sort(e[col]);ax.plot(v,np.arange(1,len(v)+1)/len(v),label=label)
    ax.set(xlabel='Local predicted depth change (km)',ylabel='Cumulative fraction');ax.legend(frameon=False,fontsize=7)
    for label,ax in zip('abc',axes):ax.set_title(label,loc='left',fontweight='bold')
    for ext in ['png','pdf']:fig.savefig(OUT/f'depth_coupling.{ext}',dpi=240)
    plt.close(fig)
    text=f'''# Why fixed station corrections move the transfer cluster shallower

No new inversion, grid generation, correction fitting or parameter search is performed.
Use the exact stage-17 control positions, picks, corrections and existing travel-time grids.

## Mechanism

At a fixed location, let J contain travel-time derivatives in x, y, depth and
origin time. Adding a predicted-time correction c requires approximately
`J delta_theta = -c`. Weighted least squares uses the existing variances
`0.3^2 + sigma_phase^2`, with sigma_P=0.1 s and sigma_S=0.2 s.
Remove the x/y/origin contribution from the depth derivative to obtain g_z_perp.
Then `delta_z = -sum(w*g_z_perp*c)/sum(w*g_z_perp^2)`.
This isolates the part of the station correction that can be exchanged for depth,
not simply the average P or S correction. The output depth kernel sums to zero:
a uniform delay changes origin time, not depth. Station contributions depend on
the fixed origin-time gauge of c; their total is invariant to a common delay.

## Results

- Linear prediction: {summary['predicted_shallow']}/{len(e)} events move shallower;
  actual stage-17 solutions: {summary['actual_shallow']}/{len(e)}.
- Median predicted / actual depth changes: {summary['median_predicted_depth_shift_km']:.3f} /
  {summary['median_actual_depth_shift_km']:.3f} km.
- Eventwise predicted-versus-actual depth-change correlation:
  {summary['depth_shift_correlation']:.3f}; median absolute prediction difference
  {summary['median_absolute_prediction_error_km']:.3f} km.
- Mean P / S contributions: {summary['mean_p_contribution_km']:.3f} /
  {summary['mean_s_contribution_km']:.3f} km. These additive means, not medians,
  sum to the mean predicted depth change.
- Median nonlinear travel-time remainder along the actual displacement:
  {summary['median_nonlinear_path_rms_s']:.4f} s. Linearization is an attribution
  approximation, not a replacement for the native nonlinear location result.

Largest station-phase terms (mean over all 147 events, zero for absent observations):

```text
{top[['instrument_id','phase','correction_s','n','mean_cohort_depth_contribution_km']].to_string(index=False,float_format=lambda x:f'{x:.4f}')}
```

## Velocity-representation coupling

At the SAME control coordinates, recompute the Jacobian with the existing original
constant-layer/elevated grids. Applying the SAME c predicts median depth change
{summary['layered_same_correction_median_depth_shift_km']:.3f} km, with
{summary['layered_same_correction_shallow']}/{len(e)} shallow shifts.
Using instead the already archived constant-layer-model development correction
estimates gives {summary['layered_own_correction_median_depth_shift_km']:.3f} km and
{summary['layered_own_correction_shallow']}/{len(e)} shallow shifts.
The isolated linear-to-layered travel-time change projects to median local depth
change {summary['layer_change_only_median_depth_shift_km']:.3f} km in the baseline
Jacobian. None of these values is a new relocated catalog or an accuracy test of
the alternate velocity model. The original locations were optimized in the linear
model, and switching to another model changes that reference optimum.

## Source-depth contamination test

Impose a single +1-km depth change on ALL 144 development hypocenters, keeping their
horizontal coordinates, origin times and observed picks fixed. Recompute exactly
the same centered-residual median estimator on the same supported cells. This is
an intentionally non-optimal counterfactual, not a proposed relocation or a true
depth correction. Its changed station terms alone project to median additional
transfer depth change {summary['development_plus_1km_transfer_median_response_km']:.3f} km,
with {summary['development_plus_1km_transfer_deeper_count']}/{len(e)} predicted deeper
responses. No reference coordinates enter the test.

Thus the station-term estimator can transmit assumed source depth from one cluster
to the other. Its output is not separately identifiable as a pure receiver term
under the present estimation procedure. This demonstrates a mechanism for depth
bias transfer; it does not measure the actual depth error of either cluster.

## Interpretation and limits

A correction estimated at an imperfect development hypocenter can include receiver,
picker, velocity/path AND source-location errors. Event-median residual removal
eliminates a common time offset, but cannot eliminate depth-dependent patterns
across stations. Transferable residual structure therefore need not be a pure
station term. This experiment tests the immediate numerical cause of the depth
shift; it does not identify the true crustal velocity or prove a station clock error.
Reference coordinates are not used in this projection or correction estimation.

All reported station contributions are signed components of one fixed sensitivity
calculation; they are not station quality labels and do not justify station removal.
Retain the stage-17 decision not to promote. Do not tune c, force reference depths,
or claim smaller residuals establish depth accuracy. Any later physical model
experiment must separately constrain depth and velocity/path structure.

## Reproduction and files

Run from expert root: `python -u 02_diagnostics/18_diagnose_depth_coupling.py`.
Derivative finite-difference checks, native travel-time agreement and the uniform
shift identity are enforced. run.json records checks and source hashes.
Event/pick/station/distance tables preserve the full signed attribution; the figure
compares linear predictions, station contributions and model sensitivity.
'''
    (OUT/'README.md').write_text(text)
    print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},indent=2),flush=True)
    print(top.to_string(index=False),flush=True)


if __name__=='__main__':main()
