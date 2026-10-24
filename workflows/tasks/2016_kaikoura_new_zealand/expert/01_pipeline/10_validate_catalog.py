#!/usr/bin/env python3
"""Freeze a provisional expert catalog and perform bounded descriptive validation."""
import os
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'): os.environ[key]='1'
from pathlib import Path
import importlib.util
import hashlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import yaml
from threadpoolctl import threadpool_limits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from obspy import UTCDateTime
HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
CFG=yaml.safe_load((HERE/'00_config/config.yaml').read_text())
EXP=HERE/CFG['export_root']; OUT=EXP/'10_validate_catalog'
CASE=(HERE/CFG['case_root']).resolve()
ROOT=(HERE/CFG['data_root']).resolve()
ANCHOR=CFG['mainshock']
T1=pd.Timestamp(ANCHOR['time_utc']); T2=T1+pd.Timedelta(hours=48)
SPEC=importlib.util.spec_from_file_location('review_helpers',HERE/'04_comparison/05_match_references.py')
review=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(review)

def times(values): return pd.to_datetime(values,format='ISO8601',utc=True)
def inside(lat,lon): return lat.between(*CFG['core_region']['latitude_bounds'])&lon.between(*CFG['core_region']['longitude_bounds'])
def periods(t): return np.where(t<T1,'pre_mainshock',np.where(t<T2,'first_48h','later'))
def zones(lat,lon): return np.char.add(np.char.add(np.where(lat>=ANCHOR['latitude'],'north','south'),'_'),np.where(lon>=ANCHOR['longitude'],'east','west'))
def magbins(x): return pd.cut(x,[-np.inf,1,2,3,np.inf],right=False,labels=['<1','1–2','2–3','>=3']).astype(str)
def save(fig,name):
    for ext in ['png','pdf']: fig.savefig(OUT/'figures'/f'{name}.{ext}',dpi=200,bbox_inches='tight')
    plt.close(fig)

def examples_plot(examples,events,gp,npicks):
    inputs=pd.read_csv(EXP/'01_prepare_inputs/full/waveform_inputs.csv',keep_default_na=False)
    stations=pd.read_csv(EXP/'03_associate_gamma/full/stations.csv')
    gp=gp.copy(); gp['epoch']=times(gp.time_utc).astype('int64')/1e9
    amplitudes=pd.read_csv(EXP/'09_estimate_magnitude/station_magnitudes.csv')
    records=[]; audits=[]
    for number,ex in enumerate(examples.to_dict('records'),1):
        anchor=UTCDateTime(pd.Timestamp(ex['anchor_time']).isoformat()); start=max(anchor-12,UTCDateTime(CFG['candidate_window']['start_utc']))
        end=min(anchor+65,UTCDateTime(CFG['candidate_window']['end_utc'])-.000001)
        ss=stations.copy()
        ss['distance_km']=np.hypot((ss.latitude-ex['latitude'])*111.2,(ss.longitude-ex['longitude'])*111.2*np.cos(np.deg2rad(ex['latitude'])))
        target=gp[gp.event_id.eq(ex['event_id'])] if ex['event_id'] else gp.iloc[:0]
        if len(target): ss=ss[ss.id.isin(target.instrument_id)]
        ss=ss.sort_values(['distance_km','id'])
        # Fixed nearest six receivers; these examples are not a random sample.
        if ex['case']=='limited_magnitude_support':
            used=amplitudes[amplitudes.event_id.eq(ex['event_id'])&amplitudes.accepted].instrument_id
            ss['amplitude_used']=ss.id.isin(used)
            ss=ss.sort_values(['amplitude_used','distance_km','id'],ascending=[False,True,True])
        ss=ss.head(6).sort_values(['distance_km','id'])
        labels=[]; tasks=[]
        for station in ss.to_dict('records'):
            net,sta,loc,fam=station['id'].split('.')
            rows=inputs[(inputs.station_id==station['station_id'])&(inputs.location==loc)&(inputs.family==fam)]
            horizontal=next((c for c in ['N','1','E','2'] if c in set(rows.component)),None)
            for panel,comp in enumerate(['Z',horizontal]):
                tasks.append((rows[rows.component.eq(comp)].to_dict('records'),ROOT,start,end,[1.,15.]))
                labels.append((station,panel,comp))
        with ThreadPoolExecutor(max_workers=4) as pool: loaded=list(pool.map(review.load_trace,tasks))
        fig,axes=plt.subplots(1,2,figsize=(10,5),sharex=True,sharey=True,layout='constrained')
        displayed_picks=gp[gp.instrument_id.isin(ss.id)&gp.epoch.between(float(start),float(end))]
        for k,((station,panel,comp),(traces,paths)) in enumerate(zip(labels,loaded)):
            level=len(ss)-1-k//2; scale=max([np.max(abs(tr.data)) for tr in traces]+[1.])
            for tr in traces:
                axes[panel].plot(tr.times()+float(tr.stats.starttime-anchor),level+.35*tr.data/scale,c='#252525',lw=.45,rasterized=True)
            picks=displayed_picks[displayed_picks.instrument_id.eq(station['id'])]
            for pick in picks.itertuples():
                is_target=bool(ex['event_id']) and pick.event_id==ex['event_id']
                color='#D55E00' if pick.phase=='P' else '#0072B2'
                if is_target: axes[panel].vlines(pick.epoch-float(anchor),level-.4,level+.4,color=color,lw=.9)
                else: axes[panel].plot(pick.epoch-float(anchor),level-.43,marker='|' if pd.isna(pick.event_id) else 'o',ms=3,color=color,mew=.6,fillstyle='none')
            records.append(dict(case=ex['case'],event_id=ex['event_id'],reference_id=ex['reference_id'],instrument_id=station['id'],component=comp,
                distance_km=station['distance_km'],start_utc=str(start),end_utc=str(end),displayed_seconds=sum(tr.stats.npts/tr.stats.sampling_rate for tr in traces),paths=';'.join(paths)))
        axes[0].set_yticks(range(len(ss)),[f'{r.station_id}  {r.distance_km:.0f} km' for r in ss.iloc[::-1].itertuples()])
        for ax,title in zip(axes,['Vertical','Native horizontal']): ax.set(xlim=(float(start-anchor),float(end-anchor)),xlabel='Time from anchor (s)',title=title)
        fig.suptitle(f"{ex['case']} | {str(anchor)[:23]} UTC",fontsize=10)
        fig.legend(handles=[Line2D([],[],color='#D55E00',label='P'),Line2D([],[],color='#0072B2',label='S'),Line2D([],[],color='k',label='Target pick'),Line2D([],[],color='k',ls='',marker='o',fillstyle='none',label='Other event pick'),Line2D([],[],color='k',ls='',marker='|',label='Unassociated pick')],loc='outside lower center',ncol=5,frameon=False,fontsize=8)
        save(fig,f'{number+1:02d}_{ex["case"]}')
        audits.append(dict(case=ex['case'],displayed_stations=len(ss),target_picks_in_window=int(displayed_picks.event_id.eq(ex['event_id']).sum()) if ex['event_id'] else 0,
            other_associated_picks=int((displayed_picks.event_id.notna()&~displayed_picks.event_id.eq(ex['event_id'])).sum()),unassociated_picks=int(displayed_picks.event_id.isna().sum())))
        print('Rendered',ex['case'],flush=True)
    pd.DataFrame(records).to_csv(OUT/'waveform_windows.csv',index=False)
    return pd.DataFrame(audits)

def main():
    threadpool_limits(1)
    (OUT/'figures').mkdir(parents=True,exist_ok=True)
    sources=[EXP/'09_estimate_magnitude/catalog.csv',EXP/'05_match_references/reference_matches.csv',EXP/'05_match_references/reference_events.csv',
             EXP/'05_match_references/unmatched_reference_events.csv',EXP/'03_associate_gamma/full/picks.csv',EXP/'04_locate_nonlinloc/full/picks.csv',
             HERE/'04_comparison/05_match_references.py',Path(__file__),
             EXP/'01_prepare_inputs/full/waveform_inputs.csv',EXP/'03_associate_gamma/full/stations.csv',EXP/'09_estimate_magnitude/station_magnitudes.csv']
    fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    e=pd.read_csv(sources[0]); matches=pd.read_csv(sources[1],dtype={'reference_id':str}); refs=pd.read_csv(sources[2],dtype={'reference_id':str})
    unmatched=pd.read_csv(sources[3],dtype={'reference_id':str})
    gp=pd.read_csv(sources[4]); npicks=pd.read_csv(sources[5])
    e['in_region_nll']=inside(e.latitude,e.longitude); e['in_region_gamma']=inside(e.gamma_latitude,e.gamma_longitude)
    e['region_disagreement']=e.in_region_nll!=e.in_region_gamma
    # The mainshock is the located event nearest the configured anchor.
    near=(times(e.origin_time)-T1).abs()
    # Prague: the mainshock (2011-11-06) precedes the window -> no mainshock row.
    MAIN=sorted(e.event_id[near<=pd.Timedelta(seconds=ANCHOR['proximity_s'])]) if ANCHOR.get('in_window',True) else []
    assert MAIN or not ANCHOR.get('in_window',True),f'No located event within {ANCHOR["proximity_s"]} s of the anchor'
    e['is_mainshock']=e.event_id.isin(MAIN)
    e['in_v1_working_catalog']=e.in_region_nll&e.provisional_quality.eq('provisionally_usable')&~e.is_mainshock
    e['magnitude']=e.ml_provisional.where(e.magnitude_status.eq('provisional')); e['magnitude_type']=np.where(e.magnitude.notna(),'ML','')
    e['period']=periods(times(e.origin_time)); e['subregion']=zones(e.latitude,e.longitude)
    e.to_csv(OUT/'events.csv',index=False)
    phases=gp[gp.event_id.notna()].merge(npicks,on=['event_id','pick_id','instrument_id','phase'],suffixes=('_gamma','_nll'),validate='one_to_one')
    assert len(phases)==len(npicks) and phases.pick_id.is_unique
    assert set(phases.event_id)==set(e.event_id)
    phases.to_csv(OUT/'phases.csv',index=False)
    # Preserve the stage-05 cohort and matching; no rematching after quality filtering.
    refs['period']=periods(times(refs.time)); refs['reference_magnitude_bin']=magbins(refs.magnitude)
    refs['subregion']=np.where(refs.latitude.notna(),zones(refs.latitude,refs.longitude),'time_only')
    refs['magnitude_type']=refs.magnitude_type.fillna('unknown')
    pairs=matches[matches.matched].copy()
    assert not pairs.duplicated(['catalog','reference_id']).any()
    rs=refs.merge(pairs[['catalog','reference_id','event_id','ambiguous']],on=['catalog','reference_id'],how='left',validate='one_to_one')
    rs['matched']=rs.event_id.notna(); rs['unambiguous']=rs.matched&rs.ambiguous.eq(False)
    rs['match_status']=np.where(~rs.matched,'unmatched',np.where(rs.unambiguous,'unambiguous','ambiguous'))
    rs=rs.merge(unmatched[['catalog','reference_id','candidate_count']],on=['catalog','reference_id'],how='left',validate='one_to_one')
    rs.to_csv(OUT/'reference_status.csv',index=False)
    enriched=matches.merge(refs[['catalog','reference_id','magnitude_type']],on=['catalog','reference_id'],how='left',validate='many_to_one').merge(
        e[['event_id','provisional_quality','magnitude_status','magnitude','in_v1_working_catalog']],on='event_id',validate='many_to_one')
    enriched['ml_difference']=enriched.magnitude-enriched.reference_magnitude
    enriched.to_csv(OUT/'reference_matches.csv',index=False)
    stats=[]
    for catalog,r in rs.groupby('catalog'):
        for grouping in ['all','period','subregion','reference_magnitude_bin']:
            groups=[('all',r)] if grouping=='all' else r.groupby(grouping,observed=True)
            for label,g in groups:
                ids=set(g.loc[g.unambiguous,'event_id']); clear=enriched[enriched.catalog.eq(catalog)&enriched.event_id.isin(ids)&enriched.matched&~enriched.ambiguous]
                ml=clear[clear.magnitude_type.eq('ML')&clear.magnitude_status.eq('provisional')]
                stats.append(dict(catalog=catalog,grouping=grouping,group=str(label),reference_events=len(g),matched=int(g.matched.sum()),
                    unambiguous=int(g.unambiguous.sum()),matched_fraction=float(g.matched.mean()),
                    median_gamma_horizontal_km=clear.gamma_horizontal_km.median(),median_nll_horizontal_km=clear.nll_horizontal_km.median(),
                    median_abs_gamma_dt_s=clear.gamma_dt_s.abs().median(),median_abs_nll_dt_s=clear.nll_dt_s.abs().median(),
                    same_type_ml_pairs=len(ml),median_ml_difference=ml.ml_difference.median()))
    stats=pd.DataFrame(stats); stats.to_csv(OUT/'comparison_groups.csv',index=False)
    examples=[]; used=set()
    def add_event(frame,name):
        frame=frame[~frame.event_id.isin(used|set(MAIN))]
        if len(frame):
            r=frame.iloc[0]; used.add(r.event_id)
            examples.append(dict(case=name,event_id=r.event_id,reference_id='',anchor_time=r.origin_time,latitude=r.latitude,longitude=r.longitude))
    u=rs[rs.catalog.eq('comcat')&~rs.matched&rs.candidate_count.eq(0)&~rs.reference_id.eq(ANCHOR['event_id'])].sort_values(['magnitude','reference_id'],ascending=[False,True])
    if len(u):
        r=u.iloc[0]; examples.append(dict(case='unmatched_reference',event_id='',reference_id=r.reference_id,anchor_time=r.time,latitude=r.latitude,longitude=r.longitude))
    degrees=matches.groupby('event_id').candidate_count.max()
    add_event(e[e.in_v1_working_catalog&e.event_id.map(degrees).eq(0)].sort_values(['n_stations','event_id'],ascending=[False,True]),'unmatched_expert')
    distances=enriched[enriched.matched&~enriched.ambiguous].groupby('event_id').nll_horizontal_km.max()
    add_event(e[e.in_v1_working_catalog].assign(reference_distance=e.event_id.map(distances)).dropna(subset=['reference_distance']).sort_values(['reference_distance','event_id'],ascending=[False,True]),'large_location_difference')
    add_event(e[e.in_v1_working_catalog&e.magnitude_status.eq('review_station_support_or_dispersion')].sort_values(['ml_provisional','event_id'],ascending=[False,True]),'limited_magnitude_support')
    examples=pd.DataFrame(examples); examples.to_csv(OUT/'examples.csv',index=False)
    plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,3,figsize=(11,3.2),layout='constrained')
    order=['pre_mainshock','first_48h','later']
    for name,g in stats[stats.grouping.eq('period')].groupby('catalog'):
        g=g.set_index('group').reindex(order); axes[0].plot(range(3),g.matched_fraction,'o-',label=name,lw=1,ms=3)
    axes[0].set(xticks=range(3),xticklabels=['Pre-mainshock','First 48 h','Later'],ylabel='Reference matched fraction',ylim=(0,1)); axes[0].legend(frameon=False,fontsize=8)
    clear=enriched[enriched.matched&~enriched.ambiguous]
    for name,g in clear.groupby('catalog'):
        values=np.sort(g.nll_horizontal_km.dropna()); axes[1].plot(values,np.arange(1,len(values)+1)/len(values),label=name,lw=1)
    axes[1].set(xlabel='NLL–reference horizontal distance (km)',ylabel='Cumulative fraction')
    for name,g in clear[clear.magnitude_type.eq('ML')&clear.magnitude.notna()].groupby('catalog'):
        axes[2].scatter(g.reference_magnitude,g.magnitude,s=3,alpha=.25,label=name)
    axes[2].plot([0,6],[0,6],c='k',lw=.7); axes[2].set(xlabel='Reference ML',ylabel='Expert provisional ML'); axes[2].legend(frameon=False,fontsize=8,markerscale=3)
    for i,ax in enumerate(axes): ax.set_title(chr(97+i),loc='left',fontweight='bold')
    save(fig,'01_catalog_validation')
    audits=examples_plot(examples,e,gp,npicks); audits.to_csv(OUT/'example_observations.csv',index=False)
    assert e.event_id.is_unique
    assert e.set_index('event_id').loc[MAIN,'magnitude'].isna().all()
    assert e.set_index('event_id').loc[MAIN,'mainshock_uncertainty'].notna().all()
    assert rs.groupby('catalog').size().sum()==len(refs)
    for p in sources: assert fingerprints[str(p)]==hashlib.sha256(p.read_bytes()).hexdigest(),p
    v1_05=yaml.safe_load((EXP/'05_match_references/run.yaml').read_text())['v1_working_events']
    assert int(e.in_v1_working_catalog.sum())==v1_05,'v1 count disagrees with stage 05'
    summary=dict(events=len(e),working_events=int(e.in_v1_working_catalog.sum()),working_events_with_ml=int((e.in_v1_working_catalog&e.magnitude.notna()).sum()),
        usable_outside_nll_region=int((~e.in_region_nll&e.provisional_quality.eq('provisionally_usable')).sum()),region_disagreements=int(e.region_disagreement.sum()),
        associated_picks=len(phases),waveform_examples=len(examples),mainshock_events=MAIN,input_sha256=fingerprints,checks_passed=True)
    (OUT/'run.yaml').write_text(yaml.safe_dump(summary,sort_keys=False))
    table=stats[stats.grouping.eq('all')].to_string(index=False)
    report=f'''# Kaikoura 2016 expert reference v1 (round {CFG['round']}): provisional

The complete eight-day pipeline exported as a provisional reference, not ground truth. No picks, locations, magnitude thresholds or reference pair identities were changed here.

## Products

- `events.csv`: all {len(e):,} candidates with region/working-catalog flags; `magnitude` only for provisional ML (consult `magnitude_status`).
- `phases.csv`: all {len(phases):,} associated picks with PhaseNet probabilities, GaMMA and NLL residuals.
- `reference_status.csv`, `reference_matches.csv`, `comparison_groups.csv`: reference denominators, pair identities, grouped comparisons.
- `examples.csv`, `example_observations.csv`, `waveform_windows.csv`, `figures/`: purpose-selected diagnostic cases (observations, not labels).
- `run.yaml`: input/code identities, checks and counts.

## Scope and interpretation

Event window: [{CFG['candidate_window']['start_utc']}, {CFG['candidate_window']['end_utc']}), 18 days after the Mw 7.8, with the STREWN temporary array active. Study box: the frozen common mask, latitude {CFG['core_region']['latitude_bounds'][0]}–{CFG['core_region']['latitude_bounds'][1]}, longitude {CFG['core_region']['longitude_bounds'][0]}–{CFG['core_region']['longitude_bounds'][1]}, depth to 60 km. The in-window anchor is the M 5.5 of 2016-12-04 03:15:47 (GeoNet 2016p913880).

There are **{summary['working_events']:,} working ordinary events**, of which **{summary['working_events_with_ml']:,} have provisional ML**; {summary['usable_outside_nll_region']} usable events outside the box stay in the master table.

References (stage 05 cohort): Tan et al. (2024) SUGAR S10 (detection primary), Lanza et al. (2019) HypoDD (location primary, ~M>=3), Chamberlain et al. (2021) corrected GrowClust, GeoNet; gates 4 s / 15 km (sensitivity 2 s / 5 km, 1 s / 3 km). Unmatched is not synonymous with missed or false.

```text
{table}
```

## Remaining limits

The 1-D NZ3D average cannot represent the subduction-margin 3-D structure (Lanza located with 3-D NZ3D). Stations span ~260 km with a median ~120 km from the anchor. The Hutton–Boore ML is provisional for New Zealand. Parameter changes belong to a new round with its own export root.
'''
    (OUT/'README.md').write_text(report)
    print(yaml.safe_dump({k:v for k,v in summary.items() if k!='input_sha256'},sort_keys=False),flush=True)
if __name__=='__main__': main()
