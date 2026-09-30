#!/usr/bin/env python3
"""Optimization round 2: native EDT likelihood with unchanged observations and model."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import importlib.util
import sys
import json
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2]
OUT=HERE/'export/22_edt_likelihood'
spec=importlib.util.spec_from_file_location('edt_helpers',HERE/'03_experiments/04_velocity_model/20_test_hk_model.py')
H=importlib.util.module_from_spec(spec);sys.modules[spec.name]=H;spec.loader.exec_module(H)
BASE=H.BASE


def prepare():
    OUT.mkdir(exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    cohort=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    picks=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False)
    picks=picks[picks.event_id.isin(cohort.event_id)].copy();picks['residual_s']=picks.residual_s_gamma
    stations=pd.read_csv(BASE/'stations.csv').set_index('id')
    held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    errors=None
    sources=[Path(__file__),Path(H.__file__),Path(H.NLL.__file__),Path(H.DIAG.__file__),Path(H.HELP.__file__),HERE/'00_config/nonlinloc.yaml',BASE/'stations.csv',HERE/'export/16_diagnose_systematics/pick_diagnostics.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/10_validate_catalog/reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv',HERE/'export/12_relative_location_pilot/run.json',HERE/'export/20_velocity_model_qualification/tables/events.csv',HERE/'export/20_velocity_model_qualification/tables/fit_phases.csv']
    sources+=list((BASE/'grids').glob('time.*.time.*'))+[Path(cfg['binary_directory'])/'NLLoc',Path(cfg['binary_directory'])/'NLLocLib.c']
    for eid in cohort.event_id:sources += [BASE/'events_raw'/eid/'input.obs',BASE/'events_raw'/eid/'control.in']
    design=dict(round=2,max_rounds=30,intervention='GAU_ANALYTIC to native EDT only; fixed input errors, picks, stations, grids and search settings.',implementation='Local NLLocLib.c CalcSolutionQuality_EDT: sum Gaussian pairwise differential-time probabilities; output origin is calculated using calc_maximum_likelihood_ot. No EDT_OT_WT spatial penalty requested. Native phase weights reflect pairwise consistency, not inverse variance.',gates='Same rules as round01: heldout RMS <=.95 baseline and P/S <=1.05; each reference median <=1.10; p90 sigma_z <=1.10; no loss of LOCATED; boundary increase <=3. Passing qualifies for fresh validation only.',limitations='Transfer cohort previously examined. Reference discrepancy is not truth error. Likelihood changes make posterior uncertainty model-dependent.',held_out=held,source_sha256={str(p):H.sha(p) for p in sources})
    path=OUT/'design.json'
    if path.exists():assert json.loads(path.read_text())==design,'Frozen inputs changed'
    else:H.write_json(path,design)
    return cfg,cohort,picks,stations,held,errors


def solve(e,obs,branch,data):
    cfg,cohort,picks,stations,held,errors=data
    aliases=stations.nll_station.to_dict();reverse={v:k for k,v in aliases.items()}
    folder=OUT/'native'/branch/e['event_id'];folder.mkdir(parents=True,exist_ok=True)
    source=BASE/'events_raw'/e['event_id'];text=(source/'input.obs').read_text()
    if branch.startswith('withheld'):
        excluded={aliases[k] for k in held}
        text='\n'.join(l for l in text.splitlines() if not l.split() or l.split()[0] not in excluded)+'\n'
        obs=[p for p in obs if p['instrument_id'] not in held]
    control='\n'.join(l for l in (source/'control.in').read_text().splitlines() if not l.startswith('LOCFILES '))+'\n'
    assert 'LOCDELAY ' not in control and 'LOCMETH GAU_ANALYTIC ' in control
    control=control.replace('LOCMETH GAU_ANALYTIC ','LOCMETH EDT ')
    control+=f'LOCFILES input.obs NLLOC_OBS {BASE}/grids/time solution\n'
    digest=H.hashlib.sha256((text+control).encode()).hexdigest();marker=folder/'complete.json'
    if marker.exists():
        d=json.loads(marker.read_text());assert d['input_sha256']==digest and H.sha(folder/d['hyp'])==d['hyp_sha256']
    else:
        (folder/'input.obs').write_text(text);(folder/'control.in').write_text(control)
        H.NLL.execute(Path(cfg['binary_directory'])/'NLLoc',folder/'control.in',folder,folder/'run.log',cfg['per_event_timeout_s'])
    paths=[p for p in folder.glob('solution.*.grid0.loc.hyp') if '.sum.' not in p.name];assert len(paths)==1
    row,links=H.NLL.parse_hyp(paths[0],e,obs,reverse,H.PROJ)
    for k in ['gamma_depth_km','gamma_rms_residual_s','gamma_rms_unweighted_s']:row.pop(k)
    row['branch']=branch
    for p in links:p['branch']=branch
    # Independently reproduce native mean-one phase weights from pairwise consistency.
    residual=np.array([p['residual_s'] for p in links])
    variance=np.array([cfg['model_error_s']**2+cfg['pick_error_s'][p['phase']]**2 for p in links])
    pairvar=variance[:,None]+variance[None,:]
    score=np.exp(-.5*(residual[:,None]-residual[None,:])**2/pairvar)/np.sqrt(pairvar)
    np.fill_diagonal(score,0.)
    expected=score.sum(axis=1);expected/=expected.mean()
    weight_error=float(np.max(np.abs(expected-np.array([p['weight'] for p in links]))))
    assert weight_error<.0005,(e['event_id'],weight_error)
    row['native_weight_check_max']=weight_error
    H.write_json(marker,dict(input_sha256=digest,hyp=paths[0].name,hyp_sha256=H.sha(paths[0])))
    return row,links


def run(data,workers):
    cfg,cohort,picks,stations,held,errors=data
    baseline=HERE/'export/20_velocity_model_qualification/tables'
    events=pd.read_csv(baseline/'events.csv');phases=pd.read_csv(baseline/'fit_phases.csv')
    rows=events[events.branch.isin(['control','withheld_control'])].to_dict('records')
    links=phases[phases.branch.isin(['control','withheld_control'])].to_dict('records')
    failures=[];groups={k:g.to_dict('records') for k,g in picks.groupby('event_id')}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(solve,e,groups[e['event_id']],b,data):(b,e['event_id']) for b in ['edt','withheld_edt'] for e in cohort.to_dict('records')}
        for i,f in enumerate(as_completed(futures),1):
            try:r,p=f.result();rows.append(r);links.extend(p)
            except Exception as exc:failures.append(dict(branch=futures[f][0],event_id=futures[f][1],error=repr(exc)));print(failures[-1],flush=True)
            if i%40==0 or i==len(futures):print(f'[{i}/294] failures={len(failures)}',flush=True)
    pd.DataFrame(failures,columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv',index=False)
    pd.DataFrame(rows).to_csv(OUT/'tables/events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'tables/fit_phases.csv',index=False)
    assert not failures


def report(data):
    cfg,cohort,picks,stations,held,errors=data
    events=pd.read_csv(OUT/'tables/events.csv');fits=pd.read_csv(OUT/'tables/fit_phases.csv');assert len(events)==588
    heldrows=[];metrics=[];maxerror=0.
    for branch,e in events.groupby('branch'):
        fp=fits[fits.branch.eq(branch)]
        p=fp.merge(picks[['pick_id','time_utc']],on='pick_id',validate='one_to_one').merge(e[['event_id','origin_time']+H.XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
        tt,_=H.DIAG.predict(BASE/'grids',p,stations)
        elapsed=(pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()
        maxerror=max(maxerror,float(np.abs(tt-p.predicted_travel_time_s).max()),float(np.abs(elapsed-tt-p.residual_s).max()));assert maxerror<.00035
        metrics.append(dict(branch=branch,n=len(e),located=int(e.status.eq('LOCATED').sum()),boundary=int(((e.depth_km<.5)|(e.depth_km>24.5)).sum()),median_depth_km=e.depth_km.median(),fit_rms_s=H.rms(fp.residual_s),p90_sigma_depth_km=e.posterior_sigma_depth_km.quantile(.9)))
        if branch.startswith('withheld'):
            assert not set(fp.instrument_id)&set(held)
            p=picks[picks.instrument_id.isin(held)].merge(e[['event_id','origin_time']+H.XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
            tt,_=H.DIAG.predict(BASE/'grids',p,stations)
            p['predicted_travel_time_s']=tt;p['branch']=branch
            p['residual_s']=(pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-tt
            heldrows.append(p)
    withheld=pd.concat(heldrows,ignore_index=True)
    hm=pd.DataFrame([dict(branch=b,phase=phase,n=len(q),rms_s=H.rms(q.residual_s)) for b,g in withheld.groupby('branch') for phase,q in [('all',g),('P',g[g.phase.eq('P')]),('S',g[g.phase.eq('S')])]])
    assert hm[hm.phase.eq('all')].n.eq(923).all()
    matches=pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv');refs=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    common=set.intersection(*(set(events[(events.branch==b)&events.status.eq('LOCATED')].event_id) for b in ['control','edt']))
    m=matches[matches.event_id.isin(common)&matches.matched&~matches.ambiguous].merge(refs[['catalog','reference_id','latitude','longitude']],on=['catalog','reference_id'],validate='many_to_one')
    vectors=[];rs=[]
    for branch in ['control','edt']:
        e=events[events.branch.eq(branch)].set_index('event_id').loc[m.event_id];rx,ry=H.PROJ(m.longitude.to_numpy(),m.latitude.to_numpy())
        v=m[['event_id','catalog','reference_id','reference_depth_km']].copy();v['branch']=branch;v['reference_x_km']=rx;v['reference_y_km']=ry
        v['horizontal_km']=np.hypot(e.x_km.to_numpy()-rx,e.y_km.to_numpy()-ry);v['depth_difference_km']=np.where(m.catalog.eq('Shelly'),e.depth_km.to_numpy()-m.reference_depth_km,np.nan);vectors.append(v)
        for cat,q in v.groupby('catalog'):rs.append(dict(branch=branch,catalog=cat,n=len(q),median_horizontal_km=q.horizontal_km.median(),median_abs_depth_km=q.depth_difference_km.abs().median()))
    rs=pd.DataFrame(rs);metrics=pd.DataFrame(metrics);vectors=pd.concat(vectors,ignore_index=True)
    mt=metrics.set_index('branch');hr=hm.pivot(index='phase',columns='branch',values='rms_s');rr=rs.pivot(index='catalog',columns='branch',values='median_horizontal_km');dr=rs[rs.catalog.eq('Shelly')].set_index('branch').median_abs_depth_km
    ratios=(rr.edt/rr.control).to_dict();ratios['Shelly_depth']=float(dr.edt/dr.control)
    gates=dict(execution=True,retention=bool(all(mt.loc[y,'located']>=mt.loc[x,'located'] for x,y in [('control','edt'),('withheld_control','withheld_edt')])),boundaries=bool(mt.loc['edt','boundary']<=mt.loc['control','boundary']+3),uncertainty=bool(mt.loc['edt','p90_sigma_depth_km']<=1.10*mt.loc['control','p90_sigma_depth_km']),heldout=bool(hr.loc['all','withheld_edt']<=.95*hr.loc['all','withheld_control'] and all(hr.loc[p,'withheld_edt']<=1.05*hr.loc[p,'withheld_control'] for p in ['P','S'])),reference=bool(all(v<=1.10 for v in ratios.values())))
    a=events[events.branch.eq('control')].set_index('event_id');b=events[events.branch.eq('edt')].set_index('event_id').loc[a.index]
    paired=pd.DataFrame(dict(event_id=a.index,control_depth_km=a.depth_km,edt_depth_km=b.depth_km,depth_shift_km=b.depth_km-a.depth_km,horizontal_shift_km=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km),control_rms_s=a.rms_unweighted_s,edt_rms_s=b.rms_unweighted_s))
    result=dict(round=2,decision='eligible_for_fresh_validation' if all(gates.values()) else 'do_not_promote',gates=gates,reference_ratios=ratios,heldout_rms_ratio=float(hr.loc['all','withheld_edt']/hr.loc['all','withheld_control']),median_depth_shift_km=float(paired.depth_shift_km.median()),timing_check_max_s=maxerror,parsed_new_fits=294,reused_verified_control_fits=294)
    for name,df in dict(metrics=metrics,heldout_predictions=withheld,heldout_metrics=hm,reference_pairs=vectors,reference_summary=rs,paired_events=paired).items():df.to_csv(OUT/f'tables/{name}.csv',index=False)
    H.write_json(OUT/'run.json',result)
    folder=OUT/'figures';folder.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(1,3,figsize=(10,3),layout='constrained')
    axes[0].scatter(a.depth_km,b.depth_km,s=9,alpha=.6);axes[0].plot([0,15],[0,15],'k-',lw=.7);axes[0].set(xlabel='Baseline depth (km)',ylabel='EDT depth (km)')
    for branch,label,color in [('control','Baseline','#2878B5'),('edt','EDT','#D65F24')]:
        values=np.sort(withheld[withheld.branch.eq('withheld_'+branch)].residual_s.abs());axes[1].plot(values,np.arange(1,len(values)+1)/len(values),label=label,color=color)
        values=np.sort(vectors[vectors.branch.eq(branch)&vectors.catalog.eq('Shelly')].depth_difference_km.abs());axes[2].plot(values,np.arange(1,len(values)+1)/len(values),label=label,color=color)
    axes[1].set(xlabel='Withheld absolute residual (s)',ylabel='Cumulative fraction',xlim=(0,2));axes[1].legend(frameon=False)
    axes[2].set(xlabel='Absolute depth difference to Shelly (km)',ylabel='Cumulative fraction')
    for label,ax in zip('abc',axes):ax.set_title(label,loc='left',fontweight='bold')
    for ext in ['png','pdf']:fig.savefig(folder/f'comparison.{ext}',dpi=240)
    plt.close(fig)
    table=lambda df:df.to_string(index=False,float_format=lambda v:f'{v:.4f}')
    (OUT/'README.md').write_text(f'''# Optimization round 2: native EDT likelihood

Decision: **{result['decision']}**. Completed 294 new EDT fits plus 294 verified baseline controls, on the same 147 events. No full-catalog replacement.

## Intervention and implementation

Only LOCMETH changes from GAU_ANALYTIC to EDT. Preserve original arrival timestamps, errors, model grids, receiver elevations, search settings and seed. The two auxiliary fits withhold the same six instruments. No empirical errors from round 1 are applied.

The installed NLLocLib.c, CalcSolutionQuality_EDT, computes pairwise differential-time Gaussian consistency and sums these contributions. Pairwise differences remove the common origin from the spatial term. Native output origin is obtained by calc_maximum_likelihood_ot; it is not a reference-derived or held-out recentering. Do not substitute EDT_OT_WT/EDT_OT_WT_ML, which introduce additional origin-time consistency weighting. Source and binary identities are frozen in design.json.

Independently reconstruct every output phase weight from pairwise residual differences and fixed total variances, then normalize to mean one (tolerance 0.0005 due to rounded native output). Independently verify travel-time prediction and the residual equation for every fitted phase; maximum discrepancy {maxerror:.7f} s. Native QUALITY RMS for EDT is a method-specific misfit; use recomputed unweighted residual RMS in the comparisons below. Conditional posterior sigmas do not represent total structural errors.

## Locations

```text
{table(metrics)}
```

Median paired depth change: {result['median_depth_shift_km']:.3f} km.

## Withheld observations

Predict 923 arrivals at the corresponding auxiliary locations and native fitted origins, without recentering or modifying the omitted picks. This is an examined transfer cohort, not a blind benchmark.

```text
{table(hm)}
```

## Fixed reference pairs

```text
{table(rs)}
```

Reference identities and ambiguity exclusions remain fixed. Shelly depths retain the previous nominal datum convention; no reference-based alignment or fitting. Reference discrepancies are not true location errors.

## Frozen gates

```text
{table(pd.DataFrame([dict(gate=k,passed=v) for k,v in gates.items()]))}
```

Passing every gate permits reserved-data validation only, not full adoption. A failure closes this fixed likelihood trial; do not tune it on these outcomes. Preserve the original v1.

## Reproduction

`python -u 03_experiments/05_catalog_optimization/22_test_edt.py --workers 8` in seismoagent. `--report-only` regenerates the report. Tables contain all locations/phases, held-out predictions and fixed reference pairs; figures show paired depth and discrepancy distributions; native/ retains exact observations, controls and logs. run.json contains the outcome; design.json freezes the sources. The original baseline fit branches are reused from stage 20 by source identity.
''')
    print(json.dumps(result,indent=2),flush=True);print(table(hm),flush=True);print(table(rs),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--workers',type=int,default=8);ap.add_argument('--report-only',action='store_true');args=ap.parse_args()
    if args.workers<1:ap.error('workers must be positive')
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=prepare()
        if not args.report_only:run(data,args.workers)
        report(data)

if __name__=='__main__':main()
