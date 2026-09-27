#!/usr/bin/env python3
"""Finite native hypoDD weight/damping comparison; reused holdouts are validation."""
from pathlib import Path
import importlib.util
import json
import argparse
import hashlib
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threadpool_limits(1)
HERE = Path(__file__).resolve().parents[2]  # Expert root; independent of working directory.
PRE=HERE/'export/13_hypodd_cc_pilot'
OUT=HERE/'export/14_tune_hypodd'
spec=importlib.util.spec_from_file_location('stage13',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
CONFIGS=[dict(name=f'cc{c}_d{d:g}',cc_factor=c,damping_factor=d) for d in [.5,1.,2.] for c in [0,1,3,10]]


def run(config):
    directory=OUT/'runs'/config['name'];directory.mkdir(parents=True,exist_ok=True)
    for name in ['dt.ct','dt.cc','event.dat','station.dat']:
        if REUSE:
            assert (directory/name).read_bytes()==(PRE/'catalog_cc'/name).read_bytes()
        else:shutil.copy2(PRE/'catalog_cc'/name,directory/name)
    text=(PRE/'catalog_cc/hypoDD.inp').read_text().splitlines()
    c=config['cc_factor'];d=config['damping_factor']
    text[9]=f'{3 if c else 2} 3 200'
    text[12]=f'4 {c if c else -9} {c/2 if c else -9} -9 -9 1 .5 -9 -9 {80*d:g}'
    text[13]=f'8 {c if c else -9} {c/2 if c else -9} -9 -9 1 .5 -9 -9 {40*d:g}'
    control='\n'.join(text)+'\n'
    if REUSE:assert (directory/'hypoDD.inp').read_text()==control
    else:
        (directory/'hypoDD.inp').write_text(control)
        with (directory/'console.log').open('w') as log:
            subprocess.run([str(PRE/'native/src/hypoDD/hypoDD'),'hypoDD.inp'],cwd=directory,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
    f=pd.read_csv(directory/'hypoDD.reloc',sep=r'\s+',header=None)
    f.columns=['native_id','latitude','longitude','depth_km','x_m','y_m','z_m','ex_m','ey_m','ez_m','year','month','day','hour','minute','second','magnitude_placeholder','nccp','nccs','nctp','ncts','rmscc','rmsct','cluster']
    f['origin_time']=[(pd.Timestamp(year=int(r.year),month=int(r.month),day=int(r.day),hour=int(r.hour),minute=int(r.minute),tz='UTC')+pd.Timedelta(seconds=r.second)).isoformat() for r in f.itertuples()]
    f=f.merge(pd.read_csv(PRE/'event_mapping.csv')[['native_id','event_id']],on='native_id',validate='one_to_one').set_index('event_id')
    residual=pd.read_csv(directory/'hypoDD.res',sep=r'\s+',skiprows=1,header=None)
    if c:assert ((residual[4]<=2)&(residual[7]>0)).any()
    print(config['name'],len(f),'events',flush=True)
    return config['name'],f


def main():
    global REUSE
    parser=argparse.ArgumentParser()
    parser.add_argument('--reuse-native',action='store_true',help='Regenerate reports from existing native outputs after checking exact input files.')
    REUSE=parser.parse_args().reuse_native
    OUT.mkdir(parents=True,exist_ok=True)
    design=dict(configurations=CONFIGS,selection='No reference catalog in selection. Retain >=138 events, use station-balanced CT score for catalog-only and equal CT/CC normalized score for CC. No validation station/type RMS may exceed input by >10%. Use identical all-configuration common rows. Previously seen holdouts are validation, not a fresh test.',limits='One local cohort only; no full-catalog adoption or independent generalization claim.')
    (OUT/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    with ThreadPoolExecutor(max_workers=2) as pool: solutions=dict(pool.map(run,CONFIGS))
    mapping=pd.read_csv(PRE/'event_mapping.csv').set_index('event_id')
    baseline=mapping.copy();baseline['origin_time']=baseline.native_origin
    solutions={'input':baseline,**solutions}
    # Repeated controls must reproduce previous native results numerically.
    for name,previous in [('cc0_d1','catalog_only'),('cc1_d1','catalog_cc')]:
        expected=pd.read_csv(PRE/(previous+'_events.csv')).set_index('event_id')
        current=solutions[name].loc[expected.index]
        assert set(solutions[name].index)==set(expected.index)
        assert np.allclose(current[['latitude','longitude','depth_km']],expected[['latitude','longitude','depth_km']],atol=1e-8,rtol=0)
        assert (pd.to_datetime(current.origin_time,utc=True,format='ISO8601')==pd.to_datetime(expected.origin_time,utc=True,format='ISO8601')).all()
    common=sorted(set.intersection(*(set(v.index) for v in solutions.values())))
    membership=mapping[['native_id','period']].copy()
    for name,f in solutions.items():membership[name]=membership.index.isin(f.index)
    membership['common']=membership.index.isin(common);membership.to_csv(OUT/'cohort.csv')
    picks=pd.read_csv(HERE/'export/12_relative_location_pilot/picks.csv').set_index('pick_id')
    stations=pd.read_csv(HERE/'export/04_locate_nonlinloc/stations.csv').set_index('id')
    cc=pd.read_csv(PRE/'cc_measurements.csv')
    pairs=cc[cc.event_id_a.isin(common)&cc.event_id_b.isin(common)].copy()
    aggregate=[];station_metrics=[];predictions={}
    for name,f in solutions.items():
        pred=old.evaluate_native(f,picks,stations)
        predictions[name]=pred
        dt=pairs.pick_id_a.map(pred)-pairs.pick_id_b.map(pred)
        for kind,observed in [('ct',pairs.observed_dt_s),('cc',pairs.cc_arrival_difference_s)]:
            pairs[name+'_'+kind+'_residual_s']=observed-dt
            for training in [False,True]:
                subset=pairs[pairs.training.eq(training)&(pairs.accepted if kind=='cc' else True)]
                residual=subset[name+'_'+kind+'_residual_s']
                aggregate.append(dict(variant=name,kind=kind,split='training' if training else 'validation',n=len(subset),rms_s=np.sqrt(np.mean(residual**2))))
                if not training:
                    for station,g in subset.groupby('instrument_id'):
                        r=g[name+'_'+kind+'_residual_s']
                        station_metrics.append(dict(variant=name,kind=kind,instrument_id=station,n=len(g),rms_s=np.sqrt(np.mean(r**2))))
    metrics=pd.DataFrame(aggregate);sm=pd.DataFrame(station_metrics)
    metrics.to_csv(OUT/'metrics.csv',index=False);sm.to_csv(OUT/'station_metrics.csv',index=False)
    pairs.to_csv(OUT/'validation_pairs.csv',index=False)
    reference=sm[sm.variant.eq('input')].set_index(['kind','instrument_id']).rms_s
    records=[]
    for config in CONFIGS:
        name=config['name'];m=sm[sm.variant.eq(name)].set_index(['kind','instrument_id'])
        ratio=m.rms_s/reference
        ct=float(ratio.loc['ct'].mean());xc=float(ratio.loc['cc'].mean())
        score=ct if config['cc_factor']==0 else (ct+xc)/2
        records.append(dict(**config,retained=len(solutions[name]),ct_normalized=ct,cc_normalized=xc,selection_score=score,worst_station_ratio=float(ratio.max()),eligible=len(solutions[name])>=138 and ratio.max()<=1.1))
    scores=pd.DataFrame(records)
    selected={}
    for label,is_cc in [('hypodd',False),('hypodd_cc',True)]:
        eligible=scores[scores.eligible & (scores.cc_factor.gt(0) if is_cc else scores.cc_factor.eq(0))]
        # If nothing passes, explicitly retain the prior pilot, without claiming improvement.
        selected[label]=eligible.sort_values(['selection_score','cc_factor','damping_factor']).iloc[0]['name'] if len(eligible) else ('cc1_d1' if is_cc else 'cc0_d1')
    selection_status={label:('validation_candidate' if bool(scores.set_index('name').loc[name,'eligible']) else 'prior_control_fallback_no_candidate_passed') for label,name in selected.items()}
    scores['selected']=scores.name.isin(selected.values());scores.to_csv(OUT/'parameter_scores.csv',index=False)
    # Sensitivity of selection to which validation station participates in scoring.
    sensitivity=[]
    for omitted in sm.instrument_id.unique():
        for label,is_cc in [('hypodd',False),('hypodd_cc',True)]:
            candidates=[]
            for config in CONFIGS:
                if bool(config['cc_factor'])!=is_cc:continue
                name=config['name']
                if len(solutions[name])<138:continue
                m=sm[sm.variant.eq(name)&sm.instrument_id.ne(omitted)].set_index(['kind','instrument_id'])
                ratio=m.rms_s/reference.reindex(m.index)
                if ratio.max()>1.1:continue
                score=(ratio.loc['ct'].mean()+ratio.loc['cc'].mean())/2 if is_cc else ratio.loc['ct'].mean()
                candidates.append((float(score),name))
            sensitivity.append(dict(omitted_validation_station=omitted,method=label,selected=min(candidates)[1] if candidates else 'none_eligible'))
    pd.DataFrame(sensitivity).to_csv(OUT/'selection_sensitivity.csv',index=False)
    # Evaluate the chosen methods on their larger pairwise intersection without re-selection.
    final_common=sorted(set(solutions[selected['hypodd']].index)&set(solutions[selected['hypodd_cc']].index))
    final_pairs=cc[cc.event_id_a.isin(final_common)&cc.event_id_b.isin(final_common)].copy()
    final_metrics=[]
    for label,name in [('input','input'),('hypodd',selected['hypodd']),('previous_cc','cc1_d1'),('hypodd_cc',selected['hypodd_cc'])]:
        pred=predictions[name]
        dt=final_pairs.pick_id_a.map(pred)-final_pairs.pick_id_b.map(pred)
        for kind,obs in [('ct',final_pairs.observed_dt_s),('cc',final_pairs.cc_arrival_difference_s)]:
            mask=~final_pairs.training & (final_pairs.accepted if kind=='cc' else True)
            residual=(obs-dt)[mask]
            assert residual.notna().all()
            final_metrics.append(dict(method=label,variant=name,kind=kind,common_events=len(final_common),n=int(mask.sum()),rms_s=float(np.sqrt(np.mean(residual**2)))))
    final_metrics=pd.DataFrame(final_metrics);final_metrics.to_csv(OUT/'selected_comparison.csv',index=False)
    membership['selected_common']=membership.index.isin(final_common);membership.to_csv(OUT/'cohort.csv')
    # Fixed reference pairs are inspected only AFTER selection, never used to rank parameters.
    refs=pd.read_csv(HERE/'export/12_relative_location_pilot/reference_comparison.csv');refs=refs[refs.event_id.isin(common)].copy()
    proj=Transformer.from_crs(4326,CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km'),always_xy=True)
    rx,ry=proj.transform(refs.longitude_ref.to_numpy(),refs.latitude_ref.to_numpy());refrows=[]
    for name,f in solutions.items():
        x,y=proj.transform(f.loc[refs.event_id,'longitude'].to_numpy(),f.loc[refs.event_id,'latitude'].to_numpy())
        for catalog,idx in refs.groupby('catalog').groups.items():
            positions=refs.index.get_indexer(idx);g=refs.loc[idx]
            refrows.append(dict(variant=name,catalog=catalog,n=len(g),median_horizontal_km=float(np.median(np.hypot(x[positions]-rx[positions],y[positions]-ry[positions]))),median_abs_depth_km=float(np.median(np.abs(f.loc[g.event_id,'depth_km'].to_numpy()-g.reference_depth_km))) if catalog=='Shelly' else np.nan))
    pd.DataFrame(refrows).to_csv(OUT/'reference_summary.csv',index=False)
    for label,name in selected.items():
        target=OUT/label;target.mkdir(exist_ok=True)
        solutions[name].to_csv(target/'events.csv')
        shutil.copy2(OUT/'runs'/name/'hypoDD.inp',target/'hypoDD.inp')
        (target/'README.md').write_text(f'# {label} candidate baseline\n\nSelected configuration: `{name}`. Status: `{selection_status[label]}`.\nNative inputs/logs remain in `../runs/{name}/`.\nRetain the relative filenames in hypoDD.inp and run from that directory.\nSee the parent report for selection limits and cohort exclusions.\nThese events are not a replacement for expert v1.\n')
    fig,axes=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
    for d,g in scores.groupby('damping_factor'):
        for ax,col in zip(axes,['ct_normalized','cc_normalized']):
            g=g.sort_values('cc_factor');ax.plot(g.cc_factor,g[col],'-o',ms=4,label=f'Damping ×{d:g}')
            ax.set(xlabel='CC row-weight multiplier',ylabel='Normalized station-balanced RMS')
    axes[0].set_title('Catalog validation');axes[1].set_title('CC validation');axes[0].legend(frameon=False)
    for ax in axes:ax.spines[['top','right']].set_visible(False)
    fig.savefig(OUT/'01_parameter_comparison.png',dpi=220);fig.savefig(OUT/'01_parameter_comparison.pdf');plt.close(fig)
    names=['input',selected['hypodd'],selected['hypodd_cc']]
    fig,axes=plt.subplots(2,3,figsize=(11,6.7),layout='constrained');coords={}
    for name in names:
        f=solutions[name].loc[common];x,y=proj.transform(f.longitude.to_numpy(),f.latitude.to_numpy());coords[name]=(x,y,f.depth_km.to_numpy())
    allxyz=np.concatenate([np.column_stack(c) for c in coords.values()]);lo=allxyz.min(axis=0)-.3;hi=allxyz.max(axis=0)+.3
    for col,(name,title) in enumerate(zip(names,['NonLinLoc input','hypoDD candidate','hypoDD + CC candidate'])):
        x,y,z=coords[name]
        for period,color in [('between_mainshocks','tab:blue'),('after_M7.1','tab:orange')]:
            mask=mapping.loc[common,'period'].eq(period).to_numpy()
            axes[0,col].scatter(x[mask],y[mask],s=8,c=color,label=period.replace('_',' '));axes[1,col].scatter(x[mask],z[mask],s=8,c=color)
        axes[0,col].set(title=title,xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),xlabel='East (km)',ylabel='North (km)',aspect='equal')
        axes[1,col].set(xlim=(lo[0],hi[0]),ylim=(hi[2],0),xlabel='East (km)',ylabel='Depth (km)',aspect='equal')
    axes[0,0].legend(frameon=False,fontsize=8)
    fig.savefig(OUT/'02_selected_comparison.png',dpi=220);fig.savefig(OUT/'02_selected_comparison.pdf');plt.close(fig)
    manifest=dict(design=design,selected=selected,selection_status=selection_status,common_events=len(common),selected_common_events=len(final_common),control_reproduction_passed=True,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py',PRE/'run.json',PRE/'cc_measurements.csv',PRE/'native/src/hypoDD/hypoDD',PRE/'native/evaluate']})
    (OUT/'run.json').write_text(json.dumps(manifest,indent=2)+'\n')
    chosen=metrics[metrics.variant.isin(names+['cc0_d1','cc1_d1'])&metrics.split.eq('validation')]
    (OUT/'README.md').write_text(f'''# Fixed-cohort hypoDD tuning

Run `python -u 03_experiments/02_relative_location/14_tune_hypodd.py` in seismoagent. Twelve predeclared settings:
CC row multipliers 0/1/3/10 and damping multipliers 0.5/1/2. Catalog P/S factors
remain 1/0.5; CC P/S factors are multiplier × CC² × 1/0.5. All settings use the
same 144 inputs, phases, CC lags, training stations, 4+8 iterations and model.
No new waveforms, picks, correlation thresholds, or velocity models are tuned.
Two CPU native jobs run concurrently. Previous catalog and CC controls reproduce
exactly in location, origin time and event membership.

## Selection rules

Retain at least the previous 138 events; no validation station/type RMS may exceed
the input prediction RMS by more than 10%. Catalog-only rank uses mean per-station
CT RMS normalized to input. CC rank equally averages station-balanced normalized
CT and CC RMS. This avoids treating repeated event pairs as independent evidence.
References are inspected after ranking, not used for selection. The all-setting
intersection is {len(common)} events; every setting uses identical rows for metrics.
Attrition is separate in cohort.csv and parameter_scores.csv. These conditional
metrics do not validate excluded events. The original selection already used
validation stations and these stations were seen in earlier stages: this is
parameter DEVELOPMENT, not an independent benchmark test.

Selected configurations: {selected}. Status: {selection_status}. If no configuration passes the gates, the prior
pilot is retained as a fallback without claiming successful optimization.
Selection sensitivity omits one validation station from ranking at a time; this
is not station-deletion inversion or a calibrated location uncertainty estimate.

```text
{scores.to_string(index=False,float_format=lambda v:f'{v:.4f}')}
```

Validation metrics on identical events/observations:

```text
{chosen.to_string(index=False,float_format=lambda v:f'{v:.5f}')}
```

## Decision for subsequent tests

Keep the previous catalog-only configuration as a CONTROL: none of the tested
catalog-only settings passes every predeclared station gate. Use CC row multiplier
3, damping 80 then 40 (`cc3_d1`) as the provisional CC candidate. All six leave-one-
validation-station-out rankings select this same CC configuration. This is ranking
stability, not an independent-data result or a station-removal location test.

A CC factor of 10 further reduces CC misfit but fails retention or station-error
gates. Therefore a lower CC misfit alone is not used to choose the configuration.
Both methods remain useful controls for future experiments; neither is declared
a validated final catalog. Shelly depth differences on the 129-event search cohort
increase from about 2.631 km (catalog) to 2.836 km (CC ×3), despite better horizontal
agreement. Preserve the depth uncertainty instead of claiming universal improvement.

After selection, the chosen methods share {len(final_common)} events. This larger
pairwise cohort is reported separately; it does not change the parameter choice:

```text
{final_metrics.to_string(index=False,float_format=lambda v:f'{v:.5f}')}
```

Do not mix these counts with the smaller intersection across all twelve settings.
No parameters were retuned after examining this post-selection table.

## Reusable outputs and limitations

- hypodd/events.csv and hypodd_cc/events.csv: candidate catalogs for later tests;
  exact runnable native inputs and logs remain in runs/<configuration>/.
- cohort.csv: all 144 input identities, retention in every variant and both comparison masks.
- selected_comparison.csv: comparison on the larger intersection of the chosen pair.
- parameter_scores.csv, metrics.csv, station_metrics.csv: complete comparison.
- selection_sensitivity.csv: dependence of configuration choice on validation stations.
- reference_summary.csv: frozen external-pair comparisons, not selection scores.
- 01_parameter_comparison.png/pdf and 02_selected_comparison.png/pdf: weight tradeoffs
  and common-cohort maps/profiles. Profile is an east-depth projection of all events.

The native constant-layer model omits receiver elevations; these constraints are
shared between native variants but differ from NonLinLoc. No sub-sample CC or
new magnitude estimates are introduced. Native origin-time output is quantized
at 0.01 s, so tiny changes should not be interpreted as decisive improvements.
CC-only supported events and noise assumptions are inherited from stage13. Confirm
results on another fixed cluster before whole-catalog adoption. Expert v1 remains
unchanged. A candidate's native error columns are not validated total uncertainties.
''')
    print(scores.to_string(index=False),flush=True);print('Selected',selected,'Common',len(common),flush=True);print(chosen.to_string(index=False),flush=True)


if __name__=='__main__':main()
