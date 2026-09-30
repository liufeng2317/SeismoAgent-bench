#!/usr/bin/env python3
"""Round 08: one fixed 80-km station selection, no station corrections."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
from pathlib import Path
import importlib.util,sys,json
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('near_helpers',HERE/'03_experiments/05_catalog_optimization/27_validate_reserved_p.py')
H=importlib.util.module_from_spec(spec);sys.modules[spec.name]=H;spec.loader.exec_module(H)
S=H.S;OUT=HERE/'export/28_near_stations';S.OUT=OUT;S.write_json=H.write_json


def prepare():
    OUT.mkdir(exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    e=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False);p=p[p.event_id.isin(e.event_id)].copy();p['residual_s']=p.residual_s_gamma
    st=pd.read_csv(S.BASE/'stations.csv').set_index('id');held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    reserved=set(pd.read_csv(HERE/'docs/optimization_reserved_events.csv').event_id);assert not reserved&set(e.event_id)
    selected=[];excluded={};elig=[]
    for row in e.to_dict('records'):
        distance=np.hypot(st['x(km)']-row['x_km'],st['y(km)']-row['y_km'])
        outside=set(st.index[distance>80]);excluded[row['event_id']]=outside
        q=p[p.event_id.eq(row['event_id'])]
        for x in q.itertuples():selected.append(dict(event_id=row['event_id'],pick_id=x.pick_id,instrument_id=x.instrument_id,phase=x.phase,distance_km=float(distance[x.instrument_id]),within_80km=x.instrument_id not in outside,is_heldout=x.instrument_id in held))
        for branch,remove in [('near',outside),('withheld_near',outside|set(held))]:
            z=q[~q.instrument_id.isin(remove)]
            elig.append(dict(event_id=row['event_id'],branch=branch,n_fit=len(z),n_s=int(z.phase.eq('S').sum()),eligible=len(z)>=10 and z.phase.eq('S').sum()>=3))
    selection=pd.DataFrame(selected);elig=pd.DataFrame(elig)
    selection.to_csv(OUT/'tables/selection.csv',index=False);elig.to_csv(OUT/'tables/eligibility.csv',index=False)
    files=[Path(__file__),Path(H.__file__),Path(S.__file__),Path(S.NLL.__file__),Path(S.DIAG.__file__),HERE/'00_config/nonlinloc.yaml',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/10_validate_catalog/reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv',HERE/'export/12_relative_location_pilot/run.json',HERE/'docs/optimization_reserved_events.csv',S.BASE/'stations.csv',HERE/'export/20_velocity_model_qualification/tables/events.csv',HERE/'export/20_velocity_model_qualification/tables/fit_phases.csv',Path(cfg['binary_directory'])/'NLLoc']
    files+=list((S.BASE/'grids').glob('time.*.time.*'))
    for eid in e.event_id:files += [S.BASE/'events_raw'/eid/'input.obs',S.BASE/'events_raw'/eid/'control.in']
    design=dict(round=8,max_rounds=30,distance_km=80,distance_definition='Horizontal model-coordinate distance from original NLL event xy; fixed before new results.',intervention='Select stations within 80 km, retain original P/S picks/errors/model/search; zero delays; no distance scan.',motivation='Previously provided Liu Text S2 uses an 80-km phase limit before hypoDD; this is a distinct NLL absolute-location test, not a reproduction.',n_events=147,n_new_fits=int(elig.eligible.sum()),gates='No loss of LOCATED primary/auxiliary compared with baseline; heldout all RMS <=.95 baseline and P/S <=1.05; each reference median <=1.10 and at least one <=.95; near-bound count <=baseline+3; posterior depth P90 <=1.10; median/P90 horizontal/depth omission shift <=1.10. No refit on consumed 300 confirmation events.',source_sha256={str(p):S.sha(p) for p in files})
    path=OUT/'design.json'
    if path.exists():assert json.loads(path.read_text())==design
    else:H.write_json(path,design)
    print('Frozen input selection:',elig.groupby('branch').eligible.sum().to_dict(),'; removed picks',int((~selection.within_80km).sum()),flush=True)
    return cfg,e,p,st,held,excluded,elig


def run(data):
    cfg,e,p,st,held,excluded,elig=data;aliases=st.nll_station.to_dict();groups={k:g.to_dict('records') for k,g in p.groupby('event_id')}
    base=HERE/'export/20_velocity_model_qualification/tables';be=pd.read_csv(base/'events.csv');bp=pd.read_csv(base/'fit_phases.csv')
    rows=be[be.branch.isin(['control','withheld_control'])].to_dict('records');links=bp[bp.branch.isin(['control','withheld_control'])].to_dict('records');failures=[]
    events=e.set_index('event_id')
    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs={}
        for x in elig[elig.eligible].itertuples():
            remove=excluded[x.event_id]|(set(held) if x.branch.startswith('withheld') else set())
            row=events.loc[x.event_id].to_dict();row['event_id']=x.event_id
            jobs[pool.submit(S.solve,row,groups[x.event_id],x.branch,{},aliases,cfg,remove)]=(x.branch,x.event_id)
        for i,f in enumerate(as_completed(jobs),1):
            try:r,pp=f.result();rows.append(r);links.extend(pp)
            except Exception as exc:failures.append(dict(branch=jobs[f][0],event_id=jobs[f][1],error=repr(exc)));print(failures[-1],flush=True)
            if i%40==0 or i==len(jobs):print(f'[{i}/{len(jobs)}] failures={len(failures)}',flush=True)
    pd.DataFrame(rows).to_csv(OUT/'tables/events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'tables/fit_phases.csv',index=False)
    pd.DataFrame(failures,columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv',index=False);assert not failures


def report(data):
    cfg,cohort,picks,st,held,excluded,elig=data;e=pd.read_csv(OUT/'tables/events.csv');fp=pd.read_csv(OUT/'tables/fit_phases.csv');hm=[];hp=[];metrics=[];maxerr=0.
    for branch,g in e.groupby('branch'):
        f=fp[fp.branch.eq(branch)];p=f.merge(picks[['pick_id','time_utc']],on='pick_id',validate='one_to_one').merge(g[['event_id','origin_time']+S.XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
        tt,_=S.DIAG.predict(S.BASE/'grids',p,st)
        residual=(pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-tt
        maxerr=max(maxerr,float(np.abs(residual-p.residual_s).max()));assert maxerr<.00035
        if 'near' in branch:
            assert all(row.instrument_id not in excluded[row.event_id] for row in f.itertuples())
        metrics.append(dict(branch=branch,n=len(g),located=int(g.status.eq('LOCATED').sum()),near_bound=int(((g.depth_km<.5)|(g.depth_km>24.5)).sum()),median_depth_km=g.depth_km.median(),fit_rms_s=S.rms(f.residual_s),p90_sigma_z_km=g.posterior_sigma_depth_km.quantile(.9)))
    # Use identical eligible events and all six-station held-out arrivals, including >80 km.
    valid=set(elig[(elig.branch=='withheld_near')&elig.eligible].event_id)
    for branch in ['withheld_control','withheld_near']:
        g=e[e.branch.eq(branch)&e.event_id.isin(valid)]
        p=picks[picks.instrument_id.isin(held)].merge(g[['event_id','origin_time']+S.XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
        assert not set(fp[fp.branch.eq(branch)].instrument_id)&set(held)
        tt,_=S.DIAG.predict(S.BASE/'grids',p,st);p['branch']=branch;p['predicted_travel_time_s']=tt
        p['residual_s']=(pd.to_datetime(p.time_utc,utc=True,format='ISO8601')-pd.to_datetime(p.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-tt;hp.append(p)
        for phase,q in [('all',p),('P',p[p.phase.eq('P')]),('S',p[p.phase.eq('S')])]:hm.append(dict(branch=branch,phase=phase,n=len(q),rms_s=S.rms(q.residual_s)))
    matches=pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv');refs=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    common=set.intersection(*(set(e[e.branch.eq(b)&e.status.eq('LOCATED')].event_id) for b in ['control','near']))
    m=matches[matches.event_id.isin(common)&matches.matched&~matches.ambiguous].merge(refs[['catalog','reference_id','latitude','longitude']],on=['catalog','reference_id'],validate='many_to_one');vectors=[];rs=[]
    for branch in ['control','near']:
        g=e[e.branch.eq(branch)].set_index('event_id').loc[m.event_id];rx,ry=S.PROJ(m.longitude.to_numpy(),m.latitude.to_numpy());v=m[['event_id','catalog','reference_id','reference_depth_km']].copy();v['branch']=branch
        v['horizontal_km']=np.hypot(g.x_km.to_numpy()-rx,g.y_km.to_numpy()-ry);v['depth_difference_km']=np.where(m.catalog.eq('Shelly'),g.depth_km.to_numpy()-m.reference_depth_km,np.nan);vectors.append(v)
        for cat,q in v.groupby('catalog'):rs.append(dict(branch=branch,catalog=cat,n=len(q),median_horizontal_km=q.horizontal_km.median(),median_abs_depth_km=q.depth_difference_km.abs().median()))
    om=[]
    for method in ['control','near']:
        b=e[e.branch.eq('withheld_'+method)&e.event_id.isin(valid)].set_index('event_id');a=e[e.branch.eq(method)].set_index('event_id').loc[b.index]
        h=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km);z=(b.depth_km-a.depth_km).abs();om.append(dict(method=method,median_horizontal_km=h.median(),p90_horizontal_km=h.quantile(.9),median_depth_km=z.median(),p90_depth_km=z.quantile(.9)))
    metrics=pd.DataFrame(metrics);hm=pd.DataFrame(hm);rs=pd.DataFrame(rs);om=pd.DataFrame(om);hp=pd.concat(hp,ignore_index=True);vectors=pd.concat(vectors,ignore_index=True)
    mt=metrics.set_index('branch');hr=hm.pivot(index='phase',columns='branch',values='rms_s');rr=rs.pivot(index='catalog',columns='branch',values='median_horizontal_km');dr=rs[rs.catalog.eq('Shelly')].set_index('branch').median_abs_depth_km
    ratios=(rr.near/rr.control).to_dict();ratios['Shelly_depth']=float(dr.near/dr.control);oo=om.set_index('method');oratio=(oo.loc['near']/oo.loc['control']).to_dict()
    gates=dict(execution=True,retention=bool(all(mt.loc[b,'located']>=mt.loc[a,'located'] for a,b in [('control','near'),('withheld_control','withheld_near')])),heldout=bool(hr.loc['all','withheld_near']<=.95*hr.loc['all','withheld_control'] and all(hr.loc[p,'withheld_near']<=1.05*hr.loc[p,'withheld_control'] for p in ['P','S'])),reference=bool(all(x<=1.10 for x in ratios.values())),reference_gain=bool(any(x<=.95 for x in ratios.values())),depth_bounds=bool(mt.loc['near','near_bound']<=mt.loc['control','near_bound']+3),posterior=bool(mt.loc['near','p90_sigma_z_km']<=1.10*mt.loc['control','p90_sigma_z_km']),omission_stability=bool(all(x<=1.10 for x in oratio.values())))
    result=dict(round=8,decision='eligible_for_separate_confirmation' if all(gates.values()) else 'do_not_promote',gates=gates,heldout_rms_ratio=float(hr.loc['all','withheld_near']/hr.loc['all','withheld_control']),reference_ratios=ratios,omission_ratios=oratio,timing_check_max_s=maxerr)
    for name,df in dict(metrics=metrics,heldout_metrics=hm,heldout_predictions=hp,reference_pairs=vectors,reference_summary=rs,omission_summary=om).items():df.to_csv(OUT/f'tables/{name}.csv',index=False)
    H.write_json(OUT/'run.json',result)
    fig,axes=plt.subplots(1,2,figsize=(7,3),layout='constrained')
    for branch,label in [('control','Baseline'),('near','Within 80 km')]:
        q=np.sort(hp[hp.branch.eq('withheld_'+branch)].residual_s.abs());axes[0].plot(q,np.arange(1,len(q)+1)/len(q),label=label)
        q=np.sort(vectors[vectors.branch.eq(branch)&vectors.catalog.eq('Shelly')].depth_difference_km.abs());axes[1].plot(q,np.arange(1,len(q)+1)/len(q),label=label)
    axes[0].set(xlabel='Withheld absolute residual (s)',ylabel='Cumulative fraction',xlim=(0,2));axes[1].set(xlabel='Absolute depth difference to Shelly (km)',ylabel='Cumulative fraction');axes[0].legend(frameon=False)
    for ext in ['png','pdf']:fig.savefig(OUT/f'comparison.{ext}',dpi=220)
    plt.close(fig)
    table=lambda df:df.to_string(index=False,float_format=lambda v:f'{v:.5f}')
    (OUT/'README.md').write_text(f'''# Round 08: fixed 80-km station selection

Decision: **{result['decision']}**. Existing 147-event development-validation cohort; the consumed 300-event confirmation set is not used to tune this intervention. No full catalog replacement.

## Inputs and eligibility

Fix an inclusive 80-km horizontal model-coordinate radius around each ORIGINAL NLL location. Do not recompute membership after relocation. Retain original P/S picks from selected instruments, original errors, velocity grids and search settings; set all station delays to zero. The radius is motivated by the previously supplied Liu supplement (phase selection before hypoDD), but this is a distinct absolute-location experiment, not its reproduction or a distance scan.

selection.csv records every original pick, distance and selection. eligibility.csv retains every event and branch with input counts. Require native minima of ten arrivals and three S picks before fitting. Any loss of location coverage remains a failed retention gate, not an excluded adverse outcome. Baseline fits are reused from verified stage-20 tables. New native controls contain no delays and omit only explicitly selected instruments.

## Locations

```text
{table(metrics)}
```

## Unchanged held-out scoring

Both auxiliary branches omit the same six instruments. Evaluate ALL their arrivals on identical eligible events, including instruments outside 80 km; do not shrink scoring to the near-station set. No origin recentering. Independent travel-time residual check maximum is {maxerr:.7f} s.

```text
{table(hm)}
```

## Fixed reference pairs

```text
{table(rs)}
```

Only Shelly depth uses the existing nominal datum. References are not truth; no identity rematching, depth-based filtering or reference fitting.

## Same station omission

```text
{table(om)}
```

## Frozen gates

```text
{table(pd.DataFrame([dict(gate=k,passed=v) for k,v in gates.items()]))}
```

## Reproduction

Run `python -u 03_experiments/05_catalog_optimization/28_test_near_stations.py` in seismoagent (eight CPU workers). design.json freezes inputs, radius and gates. Tables retain selection, all eligibility statuses, predictions, references and metrics; native/ retains controls, observations and logs. Comparison figure is PNG/PDF. No previous output or full v1 changed.
''')
    print(json.dumps(result,indent=2),flush=True);print(table(hm),flush=True);print(table(rs),flush=True)


def main():
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        data=prepare();run(data);report(data)

if __name__=='__main__':main()
