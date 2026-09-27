#!/usr/bin/env python3
"""Bounded catalog-differential relocation using the unchanged stage04 time grids.

This is a custom grid-based experiment, not a hypoDD reproduction. No waveform
correlation, phase reassignment, or reference-informed fitting is performed.
"""
from pathlib import Path
import hashlib
import json
import importlib.util
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix, vstack, eye
from scipy.sparse.csgraph import connected_components
from scipy.optimize import least_squares
from pyproj import CRS, Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from threadpoolctl import threadpool_limits

threadpool_limits(1)
HERE = Path(__file__).resolve().parents[2]  # Expert root; independent of working directory.
OUT = HERE / 'export/12_relative_location_pilot'
BASE = HERE / 'export/10_validate_catalog'
NLL = HERE / 'export/04_locate_nonlinloc'
XYZ = ['x_km', 'y_km', 'depth_km']
SETTINGS = dict(max_events=150, per_period=75, nearest_neighbors=12,
                max_pair_distance_km=3., min_shared_phases=6, min_shared_stations=4,
                min_probability=.5, max_abs_pick_residual_s=.5, seed=20260926,
                spatial_prior_km=2., origin_prior_s=.5,
                centroid_prior_km=.05, centroid_origin_prior_s=.01)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(BASE / 'events.csv')
    phases = pd.read_csv(BASE / 'phases.csv')
    stations = pd.read_csv(NLL / 'stations.csv').set_index('id')
    pool = events[events.in_v1_working_catalog & events.period.isin(['between_mainshocks', 'after_M7.1'])].copy()
    # Select a local cluster with the smallest radius containing 75 events in each period.
    groups = [pool[pool.period.eq(p)].reset_index(drop=True) for p in ['between_mainshocks', 'after_M7.1']]
    if any(len(g) < SETTINGS['per_period'] for g in groups):
        raise ValueError('Insufficient events for the fixed temporal sampling rule')
    radii = [cKDTree(g[XYZ]).query(pool[XYZ], k=SETTINGS['per_period'])[0][:, -1] for g in groups]
    center = pool.iloc[int(np.argmin(np.max(radii, axis=0)))][XYZ].to_numpy(float)
    selected = pd.concat([g.iloc[np.argsort(np.linalg.norm(g[XYZ].to_numpy()-center, axis=1), kind='stable')[:75]] for g in groups]).sort_values('event_id').reset_index(drop=True)
    p = phases[phases.event_id.isin(selected.event_id) & (phases.probability >= .5) & (phases.residual_s_nll.abs() <= .5)].copy()
    # Exclude ambiguous duplicate station-phase observations rather than choosing a pick.
    p = p[~p.duplicated(['event_id', 'instrument_id', 'phase'], keep=False)].reset_index(drop=True)
    p['key'] = p.instrument_id + ':' + p.phase
    mapping = {eid: dict(zip(g.key, g.index)) for eid, g in p.groupby('event_id')}
    tree = cKDTree(selected[XYZ]); pairs = set()
    for i, point in enumerate(selected[XYZ].to_numpy()):
        dist, ids = tree.query(point, k=min(13, len(selected)))
        pairs.update(tuple(sorted((i, int(j)))) for d,j in zip(dist, ids) if j != i and d <= 3.)
    links = []
    for i,j in sorted(pairs):
        a, b = mapping.get(selected.event_id[i], {}), mapping.get(selected.event_id[j], {})
        common = sorted(a.keys() & b.keys())
        if len(common) < 6 or len({k.split(':')[0] for k in common}) < 4: continue
        links.extend((i,j,a[k],b[k]) for k in common)
    if not links: raise ValueError('No adequately linked event pairs')
    links = np.asarray(links)
    inst = p.iloc[links[:,2]].instrument_id.to_numpy()
    unique = np.array(sorted(set(inst)))
    rng = np.random.default_rng(SETTINGS['seed'])
    held = sorted(rng.choice(unique, max(2, len(unique)//5), replace=False))
    train = ~np.isin(inst, held)
    # Define the connected cohort using training links only.
    graph = coo_matrix((np.ones(train.sum()), (links[train,0],links[train,1])), shape=(len(selected),len(selected)))
    nc, labels = connected_components(graph, directed=False)
    keep = labels == np.argmax(np.bincount(labels))
    selected['included_connected_cohort'] = keep
    selected.to_csv(OUT/'selection.csv', index=False)
    use = keep[links[:,0]] & keep[links[:,1]]
    links,inst,train = links[use],inst[use],train[use]
    selected = selected[keep].reset_index(drop=True)
    if len(selected) < 100: raise ValueError('Training component smaller than 100 events; inspect selection')
    event_index = dict(zip(selected.event_id, range(len(selected))))
    used_p = np.unique(links[:,2:]); remap = {v:i for i,v in enumerate(used_p)}
    p = p.loc[used_p].reset_index(drop=True)
    a = np.array([remap[v] for v in links[:,2]]); b = np.array([remap[v] for v in links[:,3]])
    ei = p.event_id.map(event_index).to_numpy(int)
    i,j = ei[a],ei[b]
    n = len(selected); m = len(links)
    anchor = pd.Timestamp('2019-07-04T00:00:00Z')
    arrival = (pd.to_datetime(p.time_utc, utc=True, format='ISO8601')-anchor).dt.total_seconds().to_numpy()
    origin = (pd.to_datetime(selected.origin_time,utc=True,format='ISO8601')-anchor).dt.total_seconds().to_numpy()
    initial = selected[XYZ].to_numpy(float)
    # Load identical native receiver-specific grids, including burial/elevation treatment.
    spec = importlib.util.spec_from_file_location('depth_diagnostic', HERE/'02_diagnostics/06_diagnose_depth.py')
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    mod.initialize(NLL/'grids', {}, [])
    keys = [r.phase+'.'+stations.loc[r.instrument_id,'nll_station'] for r in p.itertuples()]
    gridkeys = sorted(set(keys)); grid_index = np.array([gridkeys.index(k) for k in keys])
    grids = np.stack([mod.GRIDS[k] for k in gridkeys]); step,top = mod.STEP,mod.TOP
    receivers = stations.loc[p.instrument_id,['x(km)','y(km)']].to_numpy()

    def predict(delta):
        state = delta.reshape(n,4)
        xyz = initial[ei]+state[ei,:3]
        diff = xyz[:,:2]-receivers; r = np.linalg.norm(diff,axis=1)
        ur,uz = r/step,(xyz[:,2]-top)/step
        ir,iz = np.floor(ur).astype(int),np.floor(uz).astype(int)
        f,g = ur-ir,uz-iz
        q00=grids[grid_index,ir,iz];q10=grids[grid_index,ir+1,iz]
        q01=grids[grid_index,ir,iz+1];q11=grids[grid_index,ir+1,iz+1]
        tt=(1-f)*((1-g)*q00+g*q01)+f*((1-g)*q10+g*q11)
        dr=((1-g)*(q10-q00)+g*(q11-q01))/step
        dz=((1-f)*(q01-q00)+f*(q11-q10))/step
        deriv=np.column_stack([dr[:,None]*diff/np.maximum(r[:,None],1e-12),dz,np.ones(len(p))])
        return origin[ei]+state[ei,3]+tt,deriv,tt

    observed = arrival[a]-arrival[b]
    # Conservative differential error includes pick and model terms; shared picks
    # mean rows are dependent. Objective values are not formal chi-square confidence.
    sigma = np.where(p.phase.to_numpy()[a]=='P', .2, .3)
    def differences(delta):
        pred,deriv,_ = predict(delta)
        residual = pred[a]-pred[b]-observed
        rr=np.repeat(np.arange(m),8)
        cc=np.column_stack([4*i[:,None]+np.arange(4),4*j[:,None]+np.arange(4)]).ravel()
        values=np.column_stack([deriv[a],-deriv[b]]).ravel()
        return residual,coo_matrix((values,(rr,cc)),shape=(m,4*n)).tocsr()

    def solve(mask, prior=2.):
        scale=np.tile([1/prior]*3+[2.],n)
        centroid=coo_matrix((np.tile([20./n]*3+[100./n],n), (np.tile(np.arange(4),n),np.arange(4*n))),shape=(4,4*n)).tocsr()
        penalty=vstack([eye(4*n).multiply(scale),centroid]).tocsr()
        def fun(x):
            residual,_=differences(x)
            return np.r_[residual[mask]/sigma[mask],penalty@x]
        def jac(x):
            _,jacobian=differences(x)
            return vstack([jacobian[mask].multiply((1/sigma[mask])[:,None]),penalty]).tocsr()
        lower=np.tile([-3.,-3.,-3.,-1.],(n,1)); upper=-lower
        lower[:,2]=np.maximum(lower[:,2],.05-initial[:,2]);upper[:,2]=np.minimum(upper[:,2],24.95-initial[:,2])
        result=least_squares(fun,np.zeros(4*n),jac=jac,bounds=(lower.ravel(),upper.ravel()),max_nfev=100,ftol=1e-6,xtol=1e-6,gtol=1e-5)
        print(f'Fit: success={result.success}; nfev={result.nfev}; cost={result.cost:.2f}',flush=True)
        return result.x,dict(success=bool(result.success),message=result.message,nfev=int(result.nfev),cost=float(result.cost),optimality=float(result.optimality))

    zero=np.zeros(n*4)
    pred,deriv,tt=predict(zero)
    native_error=float(np.max(np.abs(tt-p.predicted_travel_time_s)))
    if native_error>.002: raise ValueError(f'Time-grid mismatch {native_error}')
    # Directional finite-difference check of the sparse differential Jacobian.
    direction=np.random.default_rng(7).normal(size=n*4)
    residual,jac=differences(zero);epsilon=1e-5
    jac_error=float(np.max(np.abs((differences(epsilon*direction)[0]-differences(-epsilon*direction)[0])/(2*epsilon)-jac@direction)))
    if jac_error>.002: raise ValueError(f'Jacobian check failed: {jac_error}')
    counts=pd.Series(inst[train]).value_counts(); deleted=counts.index[0]
    print(f'{n} events; {m} differential observations; {train.sum()} training; held-out stations: {held}',flush=True)
    fits={'baseline':zero}; fit_info={}
    for name,mask,prior in [('catalog_dd',train,2.),('weaker_prior',train,4.),('remove_one_station',train & (inst!=deleted),2.)]:
        fits[name],fit_info[name]=solve(mask,prior)
    output=selected.copy(); metrics=[]
    inv=Transformer.from_crs(CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km'),4326,always_xy=True)
    for name,x in fits.items():
        state=x.reshape(n,4); loc=initial+state[:,:3]
        for k,col in enumerate(XYZ): output[name+'_'+col]=loc[:,k]
        output[name+'_longitude'],output[name+'_latitude']=inv.transform(loc[:,0],loc[:,1])
        output[name+'_origin_shift_s']=state[:,3]
        output[name+'_at_bound']=(np.any(np.abs(state[:,:3])>2.99,axis=1) | (loc[:,2]<.051) | (loc[:,2]>24.949) | (np.abs(state[:,3])>.99))
        rr,_=differences(x)
        pp,_,_=predict(x)
        for label,mask in [('training',train),('held_out_stations',~train)]:
            metrics.append(dict(variant=name,split=label,n=int(mask.sum()),rms_s=float(np.sqrt(np.mean(rr[mask]**2))),median_abs_s=float(np.median(np.abs(rr[mask])))))
        p[name+'_residual_s']=arrival-pp
    output.to_csv(OUT/'events.csv',index=False)
    p.to_csv(OUT/'picks.csv',index=False)
    pd.DataFrame(metrics).to_csv(OUT/'metrics.csv',index=False)
    edge=pd.DataFrame(dict(event_id_a=p.event_id.to_numpy()[a],event_id_b=p.event_id.to_numpy()[b],pick_id_a=p.pick_id.to_numpy()[a],pick_id_b=p.pick_id.to_numpy()[b],instrument_id=inst,phase=p.phase.to_numpy()[a],observed_dt_s=observed,training=train))
    for name,x in fits.items():edge[name+'_residual_s']=differences(x)[0]
    edge.to_csv(OUT/'differential_times.csv',index=False)
    stat=p.groupby(['instrument_id','phase']).agg(n=('pick_id','size'),baseline_median_s=('baseline_residual_s','median'),baseline_std_s=('baseline_residual_s','std'),relocated_median_s=('catalog_dd_residual_s','median')).reset_index()
    stat['held_out']=stat.instrument_id.isin(held);stat.to_csv(OUT/'station_residuals.csv',index=False)
    # No reference rematching or fitting: report distances for the frozen pairs.
    matches=pd.read_csv(BASE/'reference_matches.csv'); refs=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    matched=matches[matches.event_id.isin(selected.event_id)&matches.matched&~matches.ambiguous].merge(refs[['catalog','reference_id','longitude','latitude']],on=['catalog','reference_id']).merge(output,on='event_id',suffixes=('_ref','_expert'))
    forward=Transformer.from_crs(4326,inv.source_crs,always_xy=True)
    rx,ry=forward.transform(matched.longitude_ref.to_numpy(),matched.latitude_ref.to_numpy())
    for name in fits:
        matched[name+'_horizontal_km']=np.hypot(matched[name+'_x_km']-rx,matched[name+'_y_km']-ry)
        matched[name+'_depth_difference_km']=np.where(matched.catalog.eq('Shelly'),matched[name+'_depth_km']-matched.reference_depth_km,np.nan)
    matched.to_csv(OUT/'reference_comparison.csv',index=False)
    shift=fits['catalog_dd'].reshape(n,4)
    sensitivity={name:float(np.median(np.linalg.norm((x-fits['catalog_dd']).reshape(n,4)[:,:3],axis=1))) for name,x in fits.items() if name not in ['baseline','catalog_dd']}
    report=dict(settings=SETTINGS,selected_events=150,connected_events=n,training_components=int(nc),differential_rows=m,held_out_stations=held,deleted_station=deleted,native_travel_time_max_error_s=native_error,jacobian_max_error=jac_error,fit_info=fit_info,centroid_shift_xyz_km=shift[:,:3].mean(axis=0).tolist(),median_horizontal_shift_km=float(np.median(np.linalg.norm(shift[:,:2],axis=1))),sensitivity_median_3d_km=sensitivity,bound_hit_events=int(np.sum(np.any(np.abs(shift[:,:2])>2.99,axis=1)|(np.abs(shift[:,2])>2.99)|(initial[:,2]+shift[:,2]<.051)|(initial[:,2]+shift[:,2]>24.949)|(np.abs(shift[:,3])>.99))))
    files=[Path(__file__),HERE/'02_diagnostics/06_diagnose_depth.py',BASE/'events.csv',BASE/'phases.csv',NLL/'stations.csv',NLL/'inputs.json',BASE/'reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv']+sorted((NLL/'grids').glob('time.*.time.*'))
    report['source_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    (OUT/'run.json').write_text(json.dumps(report,indent=2)+'\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(2,3,figsize=(11,6.5),layout='constrained')
    limits=[(initial[:,k].min()-3.2,initial[:,k].max()+3.2) for k in range(3)]
    for col,name in enumerate(['baseline','catalog_dd','remove_one_station']):
        loc=initial+fits[name].reshape(n,4)[:,:3]
        for period,color in [('between_mainshocks','tab:blue'),('after_M7.1','tab:orange')]:
            mask=selected.period.eq(period)
            ax[0,col].scatter(loc[mask,0],loc[mask,1],s=8,c=color,label=period.replace('_',' '))
            ax[1,col].scatter(loc[mask,0],loc[mask,2],s=8,c=color)
        ax[0,col].set(title={'baseline':'Baseline: NonLinLoc','catalog_dd':'Catalog differential times','remove_one_station':'One training station removed'}[name],xlabel='East (km)',ylabel='North (km)',xlim=limits[0],ylim=limits[1],aspect='equal')
        ax[1,col].set(xlabel='East (km)',ylabel='Depth (km)',xlim=limits[0],ylim=limits[2][::-1],aspect='equal')
    ax[0,0].legend(frameon=False,fontsize=8)
    fig.savefig(OUT/'01_relative_locations.png',dpi=220);fig.savefig(OUT/'01_relative_locations.pdf');plt.close(fig)
    table=pd.DataFrame(metrics).to_string(index=False,float_format=lambda v:f'{v:.4f}')
    depthsummary=matched.loc[matched.catalog.eq('Shelly'),[name+'_depth_difference_km' for name in fits]].abs().median().to_string(float_format=lambda v:f'{v:.3f}')
    per_station=edge[~edge.training].groupby('instrument_id')[[name+'_residual_s' for name in fits]].agg(lambda v:float(np.sqrt(np.mean(v**2))))
    per_station.to_csv(OUT/'held_out_station_metrics.csv')
    reference_counts=matched.groupby('catalog').size().to_dict()
    refsummary=matched.groupby('catalog')[[name+'_horizontal_km' for name in fits]].median().to_string(float_format=lambda v:f'{v:.3f}')
    (OUT/'README.md').write_text(f'''# Catalog differential-time pilot

This experimental output does not replace expert v1. It is a custom grid-based
relative-location experiment, **not hypoDD**, and not yet waveform-correlation relocation.

## Fixed inputs and selection

Select the smallest-radius local cohort containing 75 working events between the
mainshocks and 75 after M7.1, using only baseline coordinates and periods.
This balances periods, not event rates; it is not representative of the full catalog.
Keep probability >= 0.5 and absolute baseline residual <= 0.5 s; exclude duplicate
instrument-phase observations. Pair up to 12 nearest neighbors within 3 km in 3D,
requiring >= 6 shared phases and >= 4 instruments. Use the largest training-connected
component: {n}/150 events. Original picks, associations and v1 remain unchanged.

Reuse the exact receiver-specific stage04 grids, continuous velocity interpolation,
nominal depth datum and elevation treatment. Native travel-time maximum disagreement:
{native_error:.6f} s. Sparse Jacobian directional check: {jac_error:.6g}.

## Fit and validation

Differential observation is arrival_i - arrival_j at the same instrument and phase.
Jointly fit xyz and origin-time corrections; P/S differential scales are 0.2/0.3 s.
Quadratic 2 km spatial / 0.5 s origin priors and 0.05 km / 0.01 s mean-shift priors
stabilize the relative solution. Corrections are bounded at +/-3 km and +/-1 s;
depth remains 0.05--24.95 km. These are explicit regularization choices, not inferred errors.
The 4 km prior experiment and deletion of training station {deleted} test sensitivity.
Mean-shift regularization constrains drift and cannot establish absolute accuracy.

Held-out instruments: {', '.join(held)}. All their differential observations are
excluded from optimization. These are validation of incremental changes only:
the original baseline locations/quality selection already used these stations.
Shared picks make pair rows dependent; no formal uncertainty or independent-row
significance is claimed. Station residual medians are diagnostics, not corrections.

```text
{table}
```

Fixed unambiguous reference pair counts: {reference_counts}. Median horizontal distances in km (no rematching):

```text
{refsummary}
```

Shelly-only median absolute depth differences (km; inherited compatible datum):

```text
{depthsummary}
```

Median 3D difference from the primary fit: {sensitivity}.
Bound-hit events: {report['bound_hit_events']}. Read these alongside fit convergence
in run.json and held-out errors before interpreting visually narrower structures.
Neither smoothness nor a reduced training residual proves more accurate locations.

## Interpretation

Held-out differential RMS improves modestly (0.1633 to 0.1513 s), and the frozen
reference horizontal distances decrease. This is encouraging for this selected
cluster, not a full-catalog accuracy result. The largest component excludes six
proposed events. The deleted-station sensitivity (median 0.47 km in 3D), twelve
boundary hits and wider depth distribution prevent adopting the output as final.
Convergence is by objective-change tolerance; gradient optimality is recorded,
not asserted to meet the tighter gradient threshold. Inspect the per-station
held-out metrics; the aggregate does not imply every station improves.
The horizontal projection uses an origin at 35.75 N, 117.55 W; depths are below
the nominal surface 0.7 km above sea level. Profile figures project every selected
event onto the east-depth plane, not a narrow geological cross-section.

## Files and next decision

- events.csv: fixed cohort, baseline and all experimental coordinates.
- picks.csv / differential_times.csv: exact observations and split memberships.
- selection.csv: all 150 proposed events, including disconnected exclusions.
- station_residuals.csv: station/phase residual patterns.
- metrics.csv / reference_comparison.csv: held-out and fixed-reference comparisons.
- 01_relative_locations.png/pdf: identical axes and event sets for map/profile views.
- run.json: configuration, convergence, numerical checks and input fingerprints.

The next controlled addition is waveform cross-correlation on these fixed event
pairs, with lag/peak/SNR checks and the same withheld stations. Do not expand to the
full catalog until held-out behavior and sensitivity support doing so.
''')
    print(table,flush=True);print(refsummary,flush=True);print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2),flush=True)


if __name__ == '__main__':
    main()
