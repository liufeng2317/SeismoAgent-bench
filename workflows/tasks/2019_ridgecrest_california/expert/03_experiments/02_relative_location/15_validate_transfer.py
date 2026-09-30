#!/usr/bin/env python3
"""Fixed-parameter spatial transfer check; no parameter search or reference selection."""
from pathlib import Path
import argparse
import importlib.util
import hashlib
import json
import shutil
import subprocess
import re
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pyproj import CRS,Transformer
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
threadpool_limits(1)
HERE = Path(__file__).resolve().parents[2]  # Expert root; independent of working directory.
OUT=HERE/'export/15_validate_transfer'
INPUT=OUT/'inputs'
PRE=HERE/'export/13_hypodd_cc_pilot'
TUNE=HERE/'export/14_tune_hypodd'
spec=importlib.util.spec_from_file_location('cc_pilot',HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py')
ccmod=importlib.util.module_from_spec(spec);spec.loader.exec_module(ccmod)
ccmod.PRE=INPUT;ccmod.OUT=OUT
XYZ=['x_km','y_km','depth_km']
PERIODS=['between_mainshocks','after_M7.1']


def prepare():
    INPUT.mkdir(parents=True,exist_ok=True)
    old=pd.read_csv(HERE/'export/12_relative_location_pilot/selection.csv')
    e=pd.read_csv(HERE/'export/10_validate_catalog/events.csv')
    p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv')
    e['nearest_development_event_km']=cKDTree(old[XYZ[:2]]).query(e[XYZ[:2]])[0]
    pool=e[e.in_v1_working_catalog & e.period.isin(PERIODS)&e.nearest_development_event_km.ge(10)&~e.event_id.isin(old.event_id)].copy()
    groups=[pool[pool.period.eq(period)].reset_index(drop=True) for period in PERIODS]
    if min(map(len,groups))<75:raise ValueError('Insufficient eligible events; do not relax selection silently')
    radii=[cKDTree(g[XYZ]).query(pool[XYZ],k=75)[0][:,-1] for g in groups]
    center=pool.iloc[np.argmin(np.max(radii,axis=0))][XYZ].to_numpy(float)
    selected=pd.concat([g.iloc[np.argsort(np.linalg.norm(g[XYZ].to_numpy()-center,axis=1),kind='stable')[:75]] for g in groups]).sort_values('event_id').reset_index(drop=True)
    p=p[p.event_id.isin(selected.event_id)&p.probability.ge(.5)&p.residual_s_nll.abs().le(.5)].copy()
    p=p[~p.duplicated(['event_id','instrument_id','phase'],keep=False)].reset_index(drop=True)
    p['key']=p.instrument_id+':'+p.phase
    lookup={eid:dict(zip(g.key,g.index)) for eid,g in p.groupby('event_id')}
    pairs=set();tree=cKDTree(selected[XYZ])
    for i,point in enumerate(selected[XYZ].to_numpy()):
        ds,js=tree.query(point,k=13)
        pairs.update(tuple(sorted((i,int(j)))) for d,j in zip(ds,js) if j!=i and d<=3)
    links=[]
    for i,j in sorted(pairs):
        a,b=lookup.get(selected.event_id[i],{}),lookup.get(selected.event_id[j],{})
        keys=sorted(a.keys()&b.keys())
        if len(keys)<6 or len({k.split(':')[0] for k in keys})<4:continue
        links.extend((i,j,a[k],b[k]) for k in keys)
    if not links:raise ValueError('No supported links')
    links=np.array(links)
    held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    train=~p.iloc[links[:,2]].instrument_id.isin(held).to_numpy()
    graph=coo_matrix((np.ones(train.sum()),(links[train,0],links[train,1])),shape=(150,150))
    _,labels=connected_components(graph,directed=False)
    keep=labels==np.argmax(np.bincount(labels))
    selected['included_connected_cohort']=keep;selected.to_csv(INPUT/'selection.csv',index=False)
    use=keep[links[:,0]]&keep[links[:,1]];links=links[use];train=train[use]
    selected=selected[keep].copy()
    if len(selected)<100:raise ValueError('Training-connected cohort <100; preserve this selection as an inconclusive transfer attempt')
    selected.to_csv(INPUT/'events.csv',index=False)
    pa=p.iloc[links[:,2]].reset_index(drop=True);pb=p.iloc[links[:,3]].reset_index(drop=True)
    ta=pd.to_datetime(pa.time_utc,utc=True,format='ISO8601').astype('int64').to_numpy()
    tb=pd.to_datetime(pb.time_utc,utc=True,format='ISO8601').astype('int64').to_numpy()
    edges=pd.DataFrame(dict(event_id_a=pa.event_id,event_id_b=pb.event_id,pick_id_a=pa.pick_id,pick_id_b=pb.pick_id,instrument_id=pa.instrument_id,phase=pa.phase,observed_dt_s=(ta-tb)/1e9,training=train))
    edges.to_csv(INPUT/'differential_times.csv',index=False)
    p=p.loc[np.unique(links[:,2:])];p.to_csv(INPUT/'picks.csv',index=False)
    design=dict(selection='Smallest 3-D neighborhood of 75 between-mainshock + 75 post-M7.1 events, every event >=10 km horizontally from all 150 development events. Largest training-only connected component. No reference or CC outcome used in selection.',connected_events=len(selected),min_separation_km=float(selected.nearest_development_event_km.min()),period_counts=selected.period.value_counts().to_dict(),held_out_stations=held,parameter_source=str(TUNE/'run.json'),configurations={'hypodd':'cc0_d1','hypodd_cc':'cc3_d1'},no_parameter_tuning=True)
    (INPUT/'run.json').write_text(json.dumps(design,indent=2)+'\n')
    print(json.dumps(design,indent=2),flush=True)


def locate():
    (OUT/'native').mkdir(exist_ok=True)
    for name,src in [('hypoDD',PRE/'native/src/hypoDD/hypoDD'),('evaluate',PRE/'native/evaluate')]:
        shutil.copy2(src,OUT/'native'/name)
    events,picks,stations,cc=ccmod.inputs();ev=events.set_index('event_id')
    writer=ccmod.load_module('cc_writer',ccmod.LIB/'hypodd_runner/mk_cc.py')
    for label,config in [('hypodd','cc0_d1'),('hypodd_cc','cc3_d1')]:
        directory=OUT/label;directory.mkdir(exist_ok=True)
        shutil.copy2(TUNE/'runs'/config/'hypoDD.inp',directory/'hypoDD.inp')
        with (directory/'event.dat').open('w') as f:
            for r in events.itertuples():
                t=r.native_origin;stamp=t.strftime('%H%M%S')+f'{t.microsecond//10000:02d}'
                f.write(f'{t:%Y%m%d} {stamp} {r.latitude:.7f} {r.longitude:.7f} {r.depth_km:.5f} 0 0 0 0 {r.native_id}\n')
        with (directory/'station.dat').open('w') as f:
            for _,r in stations.iterrows():f.write(f'{r.nll_station} {r.latitude:.7f} {r.longitude:.7f}\n')
        with (directory/'dt.ct').open('w') as f:
            for (a,b),g in cc[cc.training].groupby(['event_id_a','event_id_b'],sort=True):
                f.write(f'# {ev.loc[a,"native_id"]} {ev.loc[b,"native_id"]}\n')
                for r in g.itertuples():
                    ta=(pd.Timestamp(picks.loc[r.pick_id_a,'time_utc'])-ev.loc[a,'native_origin']).total_seconds()
                    tb=(pd.Timestamp(picks.loc[r.pick_id_b,'time_utc'])-ev.loc[b,'native_origin']).total_seconds()
                    f.write(f'{stations.loc[r.instrument_id,"nll_station"]} {ta:.6f} {tb:.6f} 1 {r.phase}\n')
        blocks=[]
        for (a,b),g in cc[cc.training&cc.accepted].groupby(['event_id_a','event_id_b'],sort=True):
            od=(ev.loc[a,'native_origin']-ev.loc[b,'native_origin']).total_seconds()
            blocks.append(dict(cusp1=int(ev.loc[a,'native_id']),cusp2=int(ev.loc[b,'native_id']),otc=0,rows=[(stations.loc[r.instrument_id,'nll_station'],r.cc_arrival_difference_s-od,r.cc**2,r.phase) for r in g.itertuples()]))
        if not blocks:raise ValueError('No accepted training CC; do not silently downgrade method')
        writer.write_dt_cc(str(directory/'dt.cc'),blocks)
        with (directory/'console.log').open('w') as log:
            subprocess.run([str(OUT/'native/hypoDD'),'hypoDD.inp'],cwd=directory,stdout=log,stderr=subprocess.STDOUT,timeout=180,check=True)
        if label=='hypodd_cc':
            res=pd.read_csv(directory/'hypoDD.res',sep=r'\s+',skiprows=1,header=None)
            assert ((res[4]<=2)&res[7].gt(0)).any()
        print(label,'finished',flush=True)


def report():
    events,picks,stations,cc=ccmod.inputs();base=events.set_index('event_id');base['origin_time']=base.native_origin.astype(str)
    solutions={'input':base};membership=base[['native_id','period']].copy()
    for label in ['hypodd','hypodd_cc']:
        f=pd.read_csv(OUT/label/'hypoDD.reloc',sep=r'\s+',header=None)
        f.columns=['native_id','latitude','longitude','depth_km','x_m','y_m','z_m','ex_m','ey_m','ez_m','year','month','day','hour','minute','second','magnitude_placeholder','nccp','nccs','nctp','ncts','rmscc','rmsct','cluster']
        f['origin_time']=[(pd.Timestamp(year=int(r.year),month=int(r.month),day=int(r.day),hour=int(r.hour),minute=int(r.minute),tz='UTC')+pd.Timedelta(seconds=r.second)).isoformat() for r in f.itertuples()]
        f=f.merge(events[['native_id','event_id']],on='native_id',validate='one_to_one').set_index('event_id')
        f.to_csv(OUT/label/'events.csv');solutions[label]=f
        membership[label+'_retained']=membership.index.isin(f.index)
        bad=set(map(int,re.findall(r'negative depth -\s+(\d+)',(OUT/label/'hypoDD.log').read_text(errors='replace'))))
        membership[label+'_negative_depth_rejection']=membership.native_id.isin(bad)
    common=sorted(set(solutions['hypodd'].index)&set(solutions['hypodd_cc'].index))
    membership['common']=membership.index.isin(common);membership.to_csv(OUT/'cohort.csv')
    pairs=cc[cc.event_id_a.isin(common)&cc.event_id_b.isin(common)].copy();metrics=[];stationrows=[]
    for name,f in solutions.items():
        pred=ccmod.evaluate_native(f,picks,stations);dt=pairs.pick_id_a.map(pred)-pairs.pick_id_b.map(pred)
        for kind,obs in [('ct',pairs.observed_dt_s),('cc',pairs.cc_arrival_difference_s)]:
            pairs[name+'_'+kind+'_residual_s']=obs-dt
            for train in [True,False]:
                g=pairs[pairs.training.eq(train)&(pairs.accepted if kind=='cc' else True)]
                residual=g[name+'_'+kind+'_residual_s'];assert residual.notna().all()
                metrics.append(dict(method=name,kind=kind,split='training' if train else 'withheld_stations',n=len(g),rms_s=float(np.sqrt(np.mean(residual**2))),median_abs_s=float(residual.abs().median())))
                if not train:
                    for station,h in g.groupby('instrument_id'):
                        stationrows.append(dict(method=name,kind=kind,instrument_id=station,n=len(h),rms_s=float(np.sqrt(np.mean(h[name+'_'+kind+'_residual_s']**2)))))
    metrics=pd.DataFrame(metrics);metrics.to_csv(OUT/'metrics.csv',index=False)
    pd.DataFrame(stationrows).to_csv(OUT/'station_metrics.csv',index=False);pairs.to_csv(OUT/'validation_pairs.csv',index=False)
    matches=pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv')
    refs=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    matched=matches[matches.event_id.isin(common)&matches.matched&~matches.ambiguous].merge(refs[['catalog','reference_id','latitude','longitude']],on=['catalog','reference_id'])
    proj=Transformer.from_crs(4326,CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km'),always_xy=True)
    rx,ry=proj.transform(matched.longitude.to_numpy(),matched.latitude.to_numpy());refrows=[]
    for name,f in solutions.items():
        x,y=proj.transform(f.loc[matched.event_id,'longitude'].to_numpy(),f.loc[matched.event_id,'latitude'].to_numpy())
        matched[name+'_horizontal_km']=np.hypot(x-rx,y-ry)
        matched[name+'_depth_difference_km']=np.where(matched.catalog.eq('Shelly'),f.loc[matched.event_id,'depth_km'].to_numpy()-matched.reference_depth_km,np.nan)
        for catalog,g in matched.groupby('catalog'):
            refrows.append(dict(method=name,catalog=catalog,n=len(g),median_horizontal_km=float(g[name+'_horizontal_km'].median()),median_abs_depth_km=float(g[name+'_depth_difference_km'].abs().median())))
    pd.DataFrame(refrows).to_csv(OUT/'reference_summary.csv',index=False);matched.to_csv(OUT/'reference_matches.csv',index=False)
    fig,axes=plt.subplots(2,3,figsize=(11,6.7),layout='constrained');coords={}
    for name,f in solutions.items():
        g=f.loc[common];x,y=proj.transform(g.longitude.to_numpy(),g.latitude.to_numpy());coords[name]=(x,y,g.depth_km.to_numpy())
    xyz=np.concatenate([np.column_stack(c) for c in coords.values()]);lo=xyz.min(axis=0)-.3;hi=xyz.max(axis=0)+.3
    for col,(name,title) in enumerate([('input','NonLinLoc input'),('hypodd','hypoDD: fixed control'),('hypodd_cc','hypoDD + CC: fixed candidate')]):
        x,y,z=coords[name]
        for period,color in zip(PERIODS,['tab:blue','tab:orange']):
            mask=base.loc[common,'period'].eq(period).to_numpy()
            axes[0,col].scatter(x[mask],y[mask],s=8,c=color,label=period.replace('_',' '));axes[1,col].scatter(x[mask],z[mask],s=8,c=color)
        axes[0,col].set(title=title,xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),xlabel='East (km)',ylabel='North (km)',aspect='equal')
        axes[1,col].set(xlim=(lo[0],hi[0]),ylim=(hi[2],0),xlabel='East (km)',ylabel='Depth (km)',aspect='equal')
    axes[0,0].legend(frameon=False,fontsize=8)
    fig.savefig(OUT/'01_transfer_locations.png',dpi=220);fig.savefig(OUT/'01_transfer_locations.pdf');plt.close(fig)
    previous=pd.read_csv(HERE/'export/12_relative_location_pilot/selection.csv');proposed=pd.read_csv(INPUT/'selection.csv')
    fig,ax=plt.subplots(figsize=(5,5),layout='constrained')
    ax.scatter(previous.x_km,previous.y_km,s=9,label='Development');ax.scatter(proposed.x_km,proposed.y_km,s=9,label='Transfer')
    ax.set(xlabel='East (km)',ylabel='North (km)',aspect='equal');ax.legend(frameon=False)
    fig.savefig(OUT/'02_cohort_separation.png',dpi=220);fig.savefig(OUT/'02_cohort_separation.pdf');plt.close(fig)
    config=json.loads((INPUT/'run.json').read_text())
    accepted=cc[cc.accepted];traincc=accepted[accepted.training]
    summary=dict(design=config,retained={name:len(f) for name,f in solutions.items()},common_events=len(common),accepted_cc=len(accepted),training_cc=len(traincc),withheld_cc=int((~accepted.training).sum()),training_cc_supported_events=len(set(traincc.event_id_a)|set(traincc.event_id_b)))
    files=[INPUT/'selection.csv',OUT/'cc_measurements.csv',HERE/'export/10_validate_catalog/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/12_relative_location_pilot/selection.csv',Path(__file__),HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py',TUNE/'run.json',INPUT/'events.csv',INPUT/'picks.csv',INPUT/'differential_times.csv',OUT/'native/hypoDD',OUT/'native/evaluate']
    for label,config in [('hypodd','cc0_d1'),('hypodd_cc','cc3_d1')]:
        assert (OUT/label/'hypoDD.inp').read_bytes()==(TUNE/'runs'/config/'hypoDD.inp').read_bytes()
        files.extend([OUT/label/'hypoDD.inp'])
    summary['source_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    (OUT/'run.json').write_text(json.dumps(summary,indent=2)+'\n')
    shown=metrics[metrics.split.eq('withheld_stations')]
    metric_index=metrics.set_index(['method','kind','split']).rms_s
    cc_before=float(metric_index.loc[('hypodd','cc','withheld_stations')]);cc_after=float(metric_index.loc[('hypodd_cc','cc','withheld_stations')])
    rs=pd.DataFrame(refrows).set_index(['method','catalog'])
    (OUT/'README.md').write_text(f'''# Fixed-parameter spatial transfer

Run `python -u 03_experiments/02_relative_location/15_validate_transfer.py --stage all` in seismoagent. Individual
stages: prepare, cc, locate, report. Expert v1 and development outputs stay unchanged.

## Selection and fixed methods

Propose 150 ordinary events (75 between mainshocks, 75 after M7.1), selecting the
smallest 3-D neighborhood from working events at least 10 km horizontally from
EVERY one of the 150 development proposals. Use NonLinLoc coordinates only;
references, CC acceptance and relocation outcomes do not determine selection.
Minimum observed separation: {summary['design']['min_separation_km']:.3f} km.
Use the largest training-only connected component: {len(events)} events.
`inputs/selection.csv` preserves every proposed event and connectivity exclusions.

Same pair rules, pick thresholds, CC windows/bands/acceptance and six withheld
stations as stages12--13. Reuse the unchanged stage13 CC implementation. Copy exact
stage14 native controls: hypoDD cc0_d1 and hypoDD+CC cc3_d1, damping 80 then 40.
No search or retuning is performed. Native station-elevation omission, constant
layer interpretation and 0.01-s origin-time output precision remain unchanged.
This is transfer to new event identities, not an entirely blind benchmark:
upstream picks/associations/quality selection used all stations and the same dates.

## Coverage and paired validation

Retained: {summary['retained']}; common comparison: {len(common)} events.
Accepted CC: {len(accepted)}; training {len(traincc)}, withheld {summary['withheld_cc']}.
Training CC supports {summary['training_cc_supported_events']}/{len(events)} events.
`cohort.csv` preserves all relocation exclusions and negative-depth flags.
All methods below use identical common-event observations. Conditional improvement
must be read together with event attrition; it does not validate removed events.

```text
{shown.to_string(index=False,float_format=lambda v:f'{v:.5f}')}
```

Fixed, unambiguous stage05 reference pairs; no rematching or reference tuning:

```text
{pd.DataFrame(refrows).to_string(index=False,float_format=lambda v:f'{v:.4f}')}
```

## Transfer conclusion

With parameters fixed, CC reduces withheld CC RMS from {cc_before*1000:.2f} to
{cc_after*1000:.2f} ms ({100*(1-cc_after/cc_before):.1f}%); all six withheld stations
have lower CC RMS than catalog-only hypoDD. Catalog residuals improve in aggregate,
although CI.WMF's catalog RMS slightly worsens. NN.QSM's CC RMS remains above the
input value and has only seven withheld CC rows; aggregate improvement is not
uniform improvement against the input at every station.

External absolute-location agreement does NOT improve further with CC here.
Median horizontal differences against Liu, Official and Shelly all slightly increase
relative to catalog-only hypoDD. For Shelly, horizontal difference changes from
{rs.loc[('hypodd','Shelly'),'median_horizontal_km']:.3f} to
{rs.loc[('hypodd_cc','Shelly'),'median_horizontal_km']:.3f} km, and absolute depth
difference changes from {rs.loc[('hypodd','Shelly'),'median_abs_depth_km']:.3f} to
{rs.loc[('hypodd_cc','Shelly'),'median_abs_depth_km']:.3f} km. References are not ground
truth, but these observations prevent claiming universal location improvement.

The differential-time benefit transfers to this new local cluster; this does not
establish a universally more accurate absolute catalog. Freeze both configurations
as comparison methods for subsequent tests. Stop tuning on this cluster, preserve
the depth/model caveats and expert v1, and avoid choosing a single method as truth
or launching a whole-catalog replacement based on these two clusters alone.

## Products and decision limits

- hypodd/events.csv, hypodd_cc/events.csv: complete retained catalogs with native logs/inputs.
- metrics.csv, station_metrics.csv, validation_pairs.csv: aggregate and per-station checks.
- reference_matches.csv, reference_summary.csv: frozen external comparisons.
- 01_transfer_locations.png/pdf: equal-cohort maps and east-depth projections.
- 02_cohort_separation.png/pdf: development/transfer spatial separation.
- cc_measurements.csv, cc_components.csv, waveform_windows.csv, cc_windows.npz: full CC provenance.

Do not retune on this cohort after seeing the result. A weak or negative transfer
result is a limitation to document, not a reason to search for a more favorable
cluster. Neither sharper plots nor lower fitting RMS proves absolute accuracy.
Depth and event retention must be judged separately. No whole-catalog adoption is
performed by this script; both configurations remain explicit comparison methods.
''')
    print(json.dumps({k:v for k,v in summary.items() if k!='source_sha256'},indent=2),flush=True);print(shown.to_string(index=False),flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['all','prepare','cc','locate','report'],default='all');stage=parser.parse_args().stage
    OUT.mkdir(parents=True,exist_ok=True)
    if stage in ['all','prepare']:prepare()
    if stage in ['all','cc']:ccmod.prepare_cc()
    if stage in ['all','locate']:locate()
    if stage in ['all','report']:report()


if __name__=='__main__':main()
