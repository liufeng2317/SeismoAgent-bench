#!/usr/bin/env python3
"""Frozen-location error attribution; no locator/picker parameter optimization."""
from pathlib import Path
import importlib.util,json,hashlib,subprocess
import numpy as np
import pandas as pd
from pyproj import CRS,Transformer
from scipy.stats import spearmanr
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threadpool_limits(1)
HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
OUT=HERE/'export/16_diagnose_systematics'
NLL=HERE/'export/04_locate_nonlinloc'
LAYER=HERE/'export/06_diagnose_depth/layered_grids'
XYZ=['x_km','y_km','depth_km']


def flat_grids():
    directory=OUT/'flat_grids';directory.mkdir(parents=True,exist_ok=True)
    for phase in ['P','S']:
        lines=[s for s in (LAYER/(phase+'.in')).read_text().splitlines() if not s.startswith('GTSRCE ')]
        lines.append('GTSRCE FLAT XYZ 0 0 0 0')
        control=directory/(phase+'.in');text='\n'.join(lines)+'\n'
        cached=control.exists() and control.read_text()==text and (directory/f'time.{phase}.FLAT.time.buf').exists()
        control.write_text(text)
        if not cached:
            for binary in ['Vel2Grid','Grid2Time']:
                with (directory/f'{phase}_{binary}.log').open('w') as log:
                    subprocess.run(['/liufeng1afs/software/NLLoc/NLL7.00_src/src/'+binary,control.name],cwd=directory,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
    return directory


def predict(directory,p,stations,flat=False):
    tt=np.zeros(len(p));grad=np.zeros((len(p),3))
    for (station,phase),g in p.groupby(['instrument_id','phase']):
        sid='FLAT' if flat else stations.loc[station,'nll_station']
        header=directory/f'time.{phase}.{sid}.time.hdr'
        fields=header.read_text().splitlines()[0].split();ny,nz=int(fields[1]),int(fields[2]);step=float(fields[7]);top=float(fields[5])
        grid=np.fromfile(header.with_suffix('.buf'),dtype=np.float32,count=ny*nz).reshape(ny,nz).astype(float)
        delta=g[['x_km','y_km']].to_numpy()-stations.loc[station,['x(km)','y(km)']].to_numpy(float)
        r=np.linalg.norm(delta,axis=1);ur=r/step;uz=(g.depth_km.to_numpy()-top)/step
        ir=np.floor(ur).astype(int);iz=np.floor(uz).astype(int);a=ur-ir;b=uz-iz
        assert np.all((ir>=0)&(ir<ny-1)&(iz>=0)&(iz<nz-1))
        v00=grid[ir,iz];v10=grid[ir+1,iz];v01=grid[ir,iz+1];v11=grid[ir+1,iz+1]
        tt[g.index]=(1-a)*((1-b)*v00+b*v01)+a*((1-b)*v10+b*v11)
        dr=((1-b)*(v10-v00)+b*(v11-v01))/step
        dz=((1-a)*(v01-v00)+a*(v11-v10))/step
        grad[g.index]=np.column_stack([dr[:,None]*delta/np.maximum(r[:,None],1e-12),dz])
    return tt,grad


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    dev=pd.read_csv(HERE/'export/12_relative_location_pilot/events.csv').event_id
    transfer=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv').event_id
    assert not set(dev)&set(transfer)
    events=pd.read_csv(HERE/'export/10_validate_catalog/events.csv')
    events=events[events.event_id.isin(set(dev)|set(transfer))].copy()
    events['cohort']=np.where(events.event_id.isin(dev),'development','transfer')
    # ALL associated observations for these events; do not reuse the DD residual cutoff.
    phases=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv')
    p=phases[phases.event_id.isin(events.event_id)].merge(events[['event_id','cohort','origin_time']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
    stations=pd.read_csv(NLL/'stations.csv').set_index('id')
    picktime=pd.to_datetime(p.time_utc,utc=True,format='ISO8601').astype('int64').to_numpy()
    origin=pd.to_datetime(p.origin_time,utc=True,format='ISO8601').astype('int64').to_numpy()
    obs=(picktime-origin)/1e9
    flat=flat_grids();grads=None
    for label,directory,isflat in [('linear_elevated',NLL/'grids',False),('layered_elevated',LAYER,False),('layered_flat',flat,True)]:
        tt,grad=predict(directory,p,stations,isflat)
        p[label+'_tt_s']=tt;p[label+'_residual_s']=obs-tt
        p[label+'_centered_s']=p[label+'_residual_s']-p.groupby('event_id')[label+'_residual_s'].transform('median')
        if label=='linear_elevated':grads=grad
    mismatch=float(np.max(np.abs(p.linear_elevated_tt_s-p.predicted_travel_time_s)))
    assert mismatch<.002
    st=stations.loc[p.instrument_id]
    dx=p.x_km.to_numpy()-st['x(km)'].to_numpy();dy=p.y_km.to_numpy()-st['y(km)'].to_numpy()
    p['distance_km']=np.hypot(dx,dy);p['source_to_station_azimuth_deg']=(np.degrees(np.arctan2(-dx,-dy))+360)%360
    p['receiver_z_km']=st['z(km)'].to_numpy()
    p['layer_interpretation_delta_s']=p.layered_elevated_tt_s-p.linear_elevated_tt_s
    p['receiver_height_delta_s']=p.layered_elevated_tt_s-p.layered_flat_tt_s
    # Model changes in DIFFERENTIAL times, where common station terms can cancel.
    differential=[];idx=p.set_index('pick_id')
    for cohort,path in [('development',HERE/'export/12_relative_location_pilot/differential_times.csv'),('transfer',HERE/'export/15_validate_transfer/inputs/differential_times.csv')]:
        edge=pd.read_csv(path)
        for effect in ['layer_interpretation_delta_s','receiver_height_delta_s']:
            values=edge.pick_id_a.map(idx[effect])-edge.pick_id_b.map(idx[effect])
            for phase,g in edge.groupby('phase'):
                d=values.loc[g.index]
                differential.append(dict(cohort=cohort,phase=phase,effect=effect,n=len(d),median_abs_s=d.abs().median(),p95_abs_s=d.abs().quantile(.95)))
    pd.DataFrame(differential).to_csv(OUT/'differential_model_effects.csv',index=False)
    rows=[];correction=[]
    models=['linear_elevated','layered_elevated','layered_flat']
    for model in models:
        col=model+'_centered_s'
        table=p.groupby(['cohort','instrument_id','phase'])[col].agg(n='size',median_s='median',rms_s=lambda v:np.sqrt(np.mean(v*v))).reset_index()
        table['model']=model;rows.extend(table.to_dict('records'))
        a=table[table.cohort.eq('development')&table.n.ge(20)].set_index(['instrument_id','phase'])
        b=table[table.cohort.eq('transfer')&table.n.ge(20)].set_index(['instrument_id','phase'])
        keys=a.index.intersection(b.index)
        for key in keys:
            correction.append(dict(model=model,instrument_id=key[0],phase=key[1],development_n=int(a.loc[key,'n']),transfer_n=int(b.loc[key,'n']),development_median_s=a.loc[key,'median_s'],transfer_median_s=b.loc[key,'median_s']))
    pd.DataFrame(rows).to_csv(OUT/'station_phase_residuals.csv',index=False)
    correction=pd.DataFrame(correction);correction.to_csv(OUT/'station_phase_transfer.csv',index=False)
    checks=[]; correction_groups=[]
    for model in models:
        t=correction[correction.model.eq(model)].set_index(['instrument_id','phase'])
        q=p[p.cohort.eq('transfer')].copy()
        q['correction_s']=[t.loc[(r.instrument_id,r.phase),'development_median_s'] if (r.instrument_id,r.phase) in t.index else np.nan for r in q.itertuples()]
        q=q.dropna(subset=['correction_s'])
        before=q[model+'_centered_s'];after=before-q.correction_s
        # Same origin-time nuisance removal on identical supported rows in both branches.
        before=before-before.groupby(q.event_id).transform('median')
        after=after-after.groupby(q.event_id).transform('median')
        q['before_s']=before;q['after_s']=after
        for (instrument,phase),g in q.groupby(['instrument_id','phase']):
            correction_groups.append(dict(model=model,instrument_id=instrument,phase=phase,n=len(g),before_rms_s=float(np.sqrt(np.mean(g.before_s**2))),after_rms_s=float(np.sqrt(np.mean(g.after_s**2)))))
        checks.append(dict(model=model,supported_station_phases=len(t),n=len(q),station_median_correlation=t.development_median_s.corr(t.transfer_median_s),before_rms_s=np.sqrt(np.mean(before**2)),after_rms_s=np.sqrt(np.mean(after**2)),before_median_abs_s=before.abs().median(),after_median_abs_s=after.abs().median()))
    pd.DataFrame(correction_groups).to_csv(OUT/'station_correction_groups.csv',index=False)
    pd.DataFrame(checks).to_csv(OUT/'station_correction_diagnostic.csv',index=False)
    trends=[]
    p['distance_bin']=pd.cut(p.distance_km,[0,20,40,60,80,120,220],right=False).astype(str)
    p['azimuth_sector']=(np.floor(p.source_to_station_azimuth_deg/90)*90).astype(int)
    for model in models:
        for (cohort,phase),g in p.groupby(['cohort','phase']):
            r=g[model+'_centered_s']
            trends.append(dict(model=model,cohort=cohort,phase=phase,n=len(g),distance_spearman=float(spearmanr(g.distance_km,r).statistic),median_s=r.median(),median_abs_s=r.abs().median(),rms_s=np.sqrt(np.mean(r**2))))
    pd.DataFrame(trends).to_csv(OUT/'residual_trends.csv',index=False)
    bins=[]
    for model in models:
        for dimension in ['distance_bin','azimuth_sector']:
            b=p.groupby(['cohort','phase',dimension],observed=True)[model+'_centered_s'].agg(n='size',median_s='median',median_abs_s=lambda v:v.abs().median()).reset_index().rename(columns={dimension:'bin'})
            b['model']=model;b['dimension']=dimension;bins.extend(b.to_dict('records'))
    pd.DataFrame(bins).to_csv(OUT/'residual_bins.csv',index=False)
    # Geometry-only local depth sensitivity after removing origin and horizontal effects.
    geometry=[]
    for eid,g in p.groupby('event_id'):
        grad=grads[g.index];sigma=np.sqrt(.3**2+np.where(g.phase.eq('P'),.1,.2)**2)
        nuisance=np.column_stack([grad[:,:2],np.ones(len(g))])/sigma[:,None]
        depth=grad[:,2]/sigma
        remaining=depth-nuisance@np.linalg.lstsq(nuisance,depth,rcond=None)[0]
        geometry.append(dict(event_id=eid,cohort=g.cohort.iloc[0],n_picks=len(g),nearest_station_km=g.distance_km.min(),depth_km=g.depth_km.iloc[0],conditional_depth_scale_km=1/max(np.linalg.norm(remaining),1e-12)))
    geometry=pd.DataFrame(geometry)
    geometry.to_csv(OUT/'depth_geometry.csv',index=False)
    geometry.groupby('cohort').agg(n=('event_id','size'),median_nearest_station_km=('nearest_station_km','median'),median_conditional_depth_scale_km=('conditional_depth_scale_km','median'),p90_conditional_depth_scale_km=('conditional_depth_scale_km',lambda v:v.quantile(.9))).to_csv(OUT/'depth_geometry_summary.csv')
    # Common-event spatial differences, with rigid translation removal ONLY as a diagnostic.
    proj=Transformer.from_crs(4326,CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km'),always_xy=True)
    matches=pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv')
    references=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    vectors=[];summaries=[]
    for cohort,basepath,paths in [('development',HERE/'export/14_tune_hypodd',{'hypodd':'hypodd/events.csv','hypodd_cc':'hypodd_cc/events.csv'}),('transfer',HERE/'export/15_validate_transfer',{'hypodd':'hypodd/events.csv','hypodd_cc':'hypodd_cc/events.csv'})]:
        solutions={'nll':events[events.cohort.eq(cohort)].set_index('event_id')}
        for name,path in paths.items():solutions[name]=pd.read_csv(basepath/path).set_index('event_id')
        common=set.intersection(*(set(v.index) for v in solutions.values()))
        m=matches[matches.event_id.isin(common)&matches.matched&~matches.ambiguous].merge(references[['catalog','reference_id','latitude','longitude']],on=['catalog','reference_id'])
        for name,f in solutions.items():
            x,y=proj.transform(f.loc[m.event_id,'longitude'].to_numpy(),f.loc[m.event_id,'latitude'].to_numpy());rx,ry=proj.transform(m.longitude.to_numpy(),m.latitude.to_numpy())
            v=m[['event_id','catalog','reference_id']].copy();v['cohort']=cohort;v['method']=name;v['reference_x_km']=rx;v['reference_y_km']=ry
            v['dx_km']=x-rx;v['dy_km']=y-ry
            v['dz_km']=np.where(m.catalog.eq('Shelly'),f.loc[m.event_id,'depth_km'].to_numpy()-m.reference_depth_km,np.nan)
            for catalog,g in v.groupby('catalog'):
                mx,my=g.dx_km.median(),g.dy_km.median()
                summaries.append(dict(cohort=cohort,method=name,catalog=catalog,n=len(g),median_dx_km=mx,median_dy_km=my,translation_km=np.hypot(mx,my),median_horizontal_km=np.hypot(g.dx_km,g.dy_km).median(),median_detranslated_horizontal_km=np.hypot(g.dx_km-mx,g.dy_km-my).median(),median_signed_depth_km=g.dz_km.median(),median_abs_depth_km=g.dz_km.abs().median()))
            vectors.extend(v.to_dict('records'))
    vectors=pd.DataFrame(vectors);summaries=pd.DataFrame(summaries)
    vectors.to_csv(OUT/'reference_vectors.csv',index=False);summaries.to_csv(OUT/'reference_offsets.csv',index=False)
    p.to_csv(OUT/'pick_diagnostics.csv',index=False)
    effects=[]
    for (cohort,phase),g in p.groupby(['cohort','phase']):
        for effect in ['layer_interpretation_delta_s','receiver_height_delta_s']:
            effects.append(dict(cohort=cohort,phase=phase,effect=effect,n=len(g),median_signed_s=g[effect].median(),median_abs_s=g[effect].abs().median(),p95_abs_s=g[effect].abs().quantile(.95)))
    pd.DataFrame(effects).to_csv(OUT/'absolute_model_effects.csv',index=False)
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(11,7),layout='constrained')
    for col,model in enumerate(models):
        t=correction[correction.model.eq(model)]
        for phase,color in [('P','tab:blue'),('S','tab:orange')]:
            g=t[t.phase.eq(phase)];axes[0,col].scatter(g.development_median_s,g.transfer_median_s,c=color,s=15,label=phase)
        lim=max(.1,float(t[['development_median_s','transfer_median_s']].abs().max().max()))*1.1
        axes[0,col].plot([-lim,lim],[-lim,lim],c='black',lw=.7)
        axes[0,col].set(title=model.replace('_',' '),xlabel='Development median residual (s)',ylabel='Transfer median residual (s)',xlim=(-lim,lim),ylim=(-lim,lim),aspect='equal')
        for cohort,color in [('development','tab:blue'),('transfer','tab:orange')]:
            for phase,style in [('P','-'),('S','--')]:
                g=p[(p.cohort==cohort)&(p.phase==phase)].copy();g['bin']=pd.cut(g.distance_km,[0,20,40,60,80,120,220],right=False)
                med=g.groupby('bin',observed=True).agg(distance=('distance_km','median'),residual=(model+'_centered_s','median'))
                axes[1,col].plot(med.distance,med.residual,style+'o',color=color,ms=3,label=cohort+' '+phase)
        axes[1,col].set(xlabel='Epicentral distance (km)',ylabel='Median centered residual (s)')
    axes[0,0].legend(frameon=False);axes[1,0].legend(frameon=False,fontsize=7)
    fig.savefig(OUT/'01_residual_structure.png',dpi=220);fig.savefig(OUT/'01_residual_structure.pdf');plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(11,6.5),layout='constrained')
    for row,cohort in enumerate(['development','transfer']):
        group=vectors[(vectors.cohort==cohort)&(vectors.catalog=='Shelly')]
        for col,method in enumerate(['nll','hypodd','hypodd_cc']):
            g=group[group.method==method]
            axes[row,col].quiver(g.reference_x_km,g.reference_y_km,g.dx_km,g.dy_km,angles='xy',scale_units='xy',scale=1,width=.004)
            axes[row,col].set(title=cohort+' / '+method,xlabel='East (km)',ylabel='North (km)',aspect='equal')
        x0,x1=group.reference_x_km.min()-3,group.reference_x_km.max()+3;y0,y1=group.reference_y_km.min()-3,group.reference_y_km.max()+3
        for ax in axes[row]:ax.set(xlim=(x0,x1),ylim=(y0,y1))
    fig.savefig(OUT/'02_reference_vectors.png',dpi=220);fig.savefig(OUT/'02_reference_vectors.pdf');plt.close(fig)
    files=[Path(__file__),HERE/'export/10_validate_catalog/events.csv',HERE/'export/10_validate_catalog/phases.csv',NLL/'stations.csv',HERE/'export/10_validate_catalog/reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv']
    files+=list((NLL/'grids').glob('time.*.time.buf'))+list(LAYER.glob('time.*.time.buf'))+list(flat.glob('time.*.time.buf'))
    chosen=correction[correction.model.eq('linear_elevated')][['instrument_id','phase','development_n','development_median_s']].rename(columns={'development_median_s':'proposed_tt_correction_s'})
    chosen['status']='diagnostic_estimate_not_applied_to_locations'
    chosen.to_csv(OUT/'proposed_station_corrections.csv',index=False)
    result=dict(selected_improvement='Empirical station-phase travel-time corrections in the existing elevation-aware linear NonLinLoc absolute-location model; fixed development estimates, no picker/association/model changes.',n_events=len(events),n_all_associated_picks=len(p),native_linear_tt_max_error_s=mismatch,no_locations_modified=True,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
    (OUT/'run.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUT/'README.md').write_text(f'''# Fixed-input systematic-error diagnosis

Run `python -u 02_diagnostics/16_diagnose_systematics.py` in seismoagent. This report uses the two
existing spatial cohorts: {len(events)} ordinary events and ALL {len(p)} associated
picks, including observations excluded by the earlier DD residual/probability cut.
No event locations, picks, associations, model parameters or final catalogs change.

## Controlled attribution

At identical NonLinLoc xyz/origin times, compare three forward calculations:
linear-interpolated model with receiver elevations; original constant-layer model
with receiver elevations; the SAME constant-layer grid with every receiver on the
nominal surface. Existing elevated grids are reused; only two flat-receiver grids
are generated. Grid spacing, solver and nominal depth datum are identical. This
isolates layer interpretation and receiver elevation without confounding native
hypoDD ray tracing/geodesy. Linear predictions reproduce archived native times to
{mismatch:.7f} s. Model changes in absolute AND differential times are exported;
a common station delay can cancel between nearby events.

Residual = observed arrival minus origin minus predicted time. Per-event median
removal diagnoses station/phase/distance structure with a common-origin nuisance
removed; it is not a fitted location correction. No 0.5-s residual truncation is
used. Station-phase medians require >=20 observations in EACH cohort. Development
medians are applied to transfer arrivals only as a fixed-location prediction check,
with identical supported rows and median origin centering before/after. No correction
is estimated on transfer data. Existing location/selection bias means this is not
independent proof of a true instrument or station delay.

```text
{pd.DataFrame(checks).to_string(index=False,float_format=lambda v:f'{v:.4f}')}
```

## Reference differences and depth geometry

Frozen unambiguous reference pairs on identical retained event sets; no rematching.
Export east/north residual vectors and depth differences only for Shelly's compatible
datum. Coordinate-wise median translation removal is a DIAGNOSTIC only; it is never
applied to a catalog. A reduced discrepancy after translation does not prove which
catalog has the correct absolute location.

```text
{summaries[summaries.catalog.eq('Shelly')].to_string(index=False,float_format=lambda v:f'{v:.3f}')}
```

Depth geometry uses the local linear-model gradient after projecting out horizontal
location and origin-time derivatives, scaled by the existing P/S/model error terms.
The resulting conditional depth scale assumes independent errors and a correct
model; it is a geometry diagnostic, not calibrated total uncertainty. It does not
prove that a residual outlier is a mistaken phase or a misassociated event.

## Selected single improvement

**Test empirical station-by-phase travel-time corrections in the existing absolute
NonLinLoc workflow.** Keep the current linear velocity interpolation, receiver
elevations, observation errors, picks, associations and search settings unchanged.
Apply `T_corrected = T_model + c_station,phase`; a positive c means the observed
arrival is systematically later than predicted. Do not rewrite original pick times.
`proposed_station_corrections.csv` contains the 61 supported development-only
estimates. Transfer counts determine supported diagnostic comparisons, never the
correction values. No correction has yet been applied to a location solution.

The linear elevated model's station-phase medians correlate at 0.791 between the
two clusters. On 5,267 identically supported transfer observations, centered RMS
falls from 0.390 to 0.304 s (about 22%), and median absolute residual from 0.211 to
0.134 s. This fixed-position, origin-centered prediction check supports selecting
the intervention; it does not demonstrate improved earthquake locations. Corrections
may absorb near-station structure, path errors or systematic picking offsets; they
are not established clock/instrument delays and must remain model-specific.

Other findings constrain the choice:

- Cluster translation accounts for a substantial part of horizontal reference
  differences. Relative to Shelly, hypoDD+CC has northward median offsets of about
  0.314 km (development) and 0.627 km (transfer). Median horizontal discrepancies
  after diagnostic translation removal are 0.140 and 0.212 km. This is not a license
  to translate catalogs to references; other catalogs have their own offsets.
- The development cluster retains a median shallow depth bias of about 2.742 km
  against Shelly. A single horizontal shift cannot resolve it.
- Layer interpretation changes individual predicted times by about 0.07--0.18 s
  in median across the cohort/phase groups, and receiver elevations by about
  0.03--0.055 s. In nearby-event differential times, the receiver-height effect
  has p95 only about 0.001--0.002 s. Elevation omission alone is therefore unlikely
  to explain the current CC-versus-catalog difference in these two cohorts.
- Distance trends are phase dependent; constant layers reduce the P trend but
  strengthen the negative S trend. Merely swapping the layer interpretation is
  not a demonstrated universal correction. Station correction is selected as one
  bounded observation-model improvement, not as a replacement for future velocity
  model work or proof that phase misassociation is absent.

For the next controlled implementation, freeze these development corrections,
perform one corrected versus uncorrected absolute-location comparison on the
transfer events, and keep the complete event set and retention flags. Judge
geometry/depth stability, residuals and frozen reference differences together.
The transfer cluster has already been inspected and remains development validation.
Do not use reference coordinates to estimate c, tune correction strength, discard
adverse results, or assume reduced RMS proves accuracy. Retain unsupported station
phases unchanged with explicit flags. Broader use still needs a new independent set.

Local geometry also differs between cohorts: median nearest-receiver distances
are about 10.14 km (development) and 5.10 km (transfer), with conditional local
depth scales about 1.50 and 1.12 km respectively. This supports retaining depth
uncertainty, especially for the shallower development cluster; these scales are
model-conditional and should not be reported as validated confidence intervals.
`residual_bins.csv` records both distance and azimuth sectors with sample counts;
uneven ray coverage and station identity confound their physical interpretation.
`station_correction_groups.csv` preserves station-phase improvements AND worsening,
so an aggregate residual reduction does not hide adverse receiver-specific effects.

## Outputs

- pick_diagnostics.csv: every associated pick, three predictions/residuals and geometry.
- station_phase_residuals.csv / station_phase_transfer.csv: supported station patterns.
- station_correction_diagnostic.csv: development-to-transfer prediction check.
- absolute_model_effects.csv / differential_model_effects.csv: isolated physical effects.
- residual_trends.csv / depth_geometry.csv: distance/phase and depth-sensitivity diagnostics.
- reference_vectors.csv / reference_offsets.csv: fixed-pair spatial bias and scatter.
- 01_residual_structure.png/pdf; 02_reference_vectors.png/pdf: diagnostic figures.

Numerical improvement is not sufficient to authorize a new truth catalog. Select
one physical/observational improvement after inspecting these diagnostics; do not
resume broad locator or picker parameter search.
''')
    print('Station prediction check\n',pd.DataFrame(checks).to_string(index=False),flush=True)
    print('Absolute effects\n',pd.DataFrame(effects).to_string(index=False),flush=True)
    print('Differential effects\n',pd.DataFrame(differential).to_string(index=False),flush=True)
    print('Shelly offsets\n',summaries[summaries.catalog.eq('Shelly')].to_string(index=False),flush=True)


if __name__=='__main__':main()
