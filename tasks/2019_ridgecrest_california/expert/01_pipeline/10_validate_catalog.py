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
EXP=HERE/'export'; OUT=EXP/'10_validate_catalog'
CASE=HERE.parents[2]/'benchmark_source/2019_ridgecrest_california'
MAIN=['gamma_0000046','gamma_0005482']
T1=pd.Timestamp('2019-07-04T17:33:49Z'); T2=pd.Timestamp('2019-07-06T03:19:53.04Z')
SPEC=importlib.util.spec_from_file_location('review_helpers',HERE/'02_diagnostics/05_review_catalog.py')
review=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(review)

def times(values): return pd.to_datetime(values,format='ISO8601',utc=True)
def inside(lat,lon): return lat.between(35.45,36.05)&lon.between(-117.90,-117.20)
def periods(t): return np.where(t<T1,'before_M6.4',np.where(t<T2,'between_mainshocks','after_M7.1'))
def zones(lat,lon): return np.char.add(np.char.add(np.where(lat>=35.75,'north','south'),'_'),np.where(lon>=-117.55,'east','west'))
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
        anchor=UTCDateTime(pd.Timestamp(ex['anchor_time']).isoformat()); start=max(anchor-12,UTCDateTime('2019-07-04'))
        end=min(anchor+65,UTCDateTime('2019-07-07')-.000001)
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
                tasks.append((rows[rows.component.eq(comp)].to_dict('records'),(CASE/'data/waveforms').resolve(),start,end,[1.,15.]))
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
    sources=[EXP/'09_estimate_magnitude/catalog.csv',EXP/'05_review_catalog/reference_matches.csv',EXP/'05_review_catalog/reference_events.csv',
             EXP/'05_review_catalog/unmatched_reference_events.csv',EXP/'03_associate_gamma/full/picks.csv',EXP/'04_locate_nonlinloc/full/picks.csv',
             CASE/'data/catalogs/USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_full.csv',HERE/'02_diagnostics/05_review_catalog.py',Path(__file__),
             EXP/'01_prepare_inputs/full/waveform_inputs.csv',EXP/'03_associate_gamma/full/stations.csv',EXP/'09_estimate_magnitude/station_magnitudes.csv']
    fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    e=pd.read_csv(sources[0]); matches=pd.read_csv(sources[1],dtype={'reference_id':str}); refs=pd.read_csv(sources[2],dtype={'reference_id':str})
    unmatched=pd.read_csv(sources[3],dtype={'reference_id':str})
    gp=pd.read_csv(sources[4]); npicks=pd.read_csv(sources[5]); official=pd.read_csv(sources[6],dtype={'id':str})
    e['in_region_nll']=inside(e.latitude,e.longitude); e['in_region_gamma']=inside(e.gamma_latitude,e.gamma_longitude)
    e['region_disagreement']=e.in_region_nll!=e.in_region_gamma
    e['is_mainshock']=e.event_id.isin(MAIN)
    e['in_v1_working_catalog']=e.in_region_nll&e.provisional_quality.eq('provisionally_usable')&~e.is_mainshock
    e['magnitude']=e.ml_provisional.where(e.magnitude_status.eq('provisional')); e['magnitude_type']=np.where(e.magnitude.notna(),'ML','')
    e['period']=periods(times(e.origin_time)); e['subregion']=zones(e.latitude,e.longitude)
    e.to_csv(OUT/'events.csv',index=False)
    phases=gp[gp.event_id.notna()].merge(npicks,on=['event_id','pick_id','instrument_id','phase'],suffixes=('_gamma','_nll'),validate='one_to_one')
    assert len(phases)==len(npicks)==288431 and phases.pick_id.is_unique
    assert set(phases.event_id)==set(e.event_id)
    phases.to_csv(OUT/'phases.csv',index=False)
    # Preserve the stage-05 cohort and matching; no rematching after quality filtering.
    refs['period']=periods(times(refs.time)); refs['subregion']=zones(refs.latitude,refs.longitude); refs['reference_magnitude_bin']=magbins(refs.magnitude)
    refs['magnitude_type']='unspecified_mixed'
    refs.loc[refs.catalog.eq('Liu'),'magnitude_type']='ML'
    mt=official.set_index('id').magType.str.upper()
    mask=refs.catalog.eq('Official'); refs.loc[mask,'magnitude_type']=refs.loc[mask,'reference_id'].map(mt).fillna('unknown')
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
    u=rs[rs.catalog.eq('Official')&~rs.matched&rs.candidate_count.eq(0)&~rs.reference_id.isin(['ci38443183','ci38457511'])].sort_values(['magnitude','reference_id'],ascending=[False,True])
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
    order=['before_M6.4','between_mainshocks','after_M7.1']
    for name,g in stats[stats.grouping.eq('period')].groupby('catalog'):
        g=g.set_index('group').reindex(order); axes[0].plot(range(3),g.matched_fraction,'o-',label=name,lw=1,ms=3)
    axes[0].set(xticks=range(3),xticklabels=['Before M6.4','Between','After M7.1'],ylabel='Reference matched fraction',ylim=(0,1)); axes[0].legend(frameon=False,fontsize=8)
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
    assert len(e)==9942 and e.event_id.is_unique
    assert e.set_index('event_id').loc[MAIN,'magnitude'].isna().all()
    assert e.set_index('event_id').loc[MAIN,'mainshock_uncertainty'].notna().all()
    assert rs.groupby('catalog').size().sum()==len(refs)
    for p in sources: assert fingerprints[str(p)]==hashlib.sha256(p.read_bytes()).hexdigest(),p
    summary=dict(events=len(e),working_events=int(e.in_v1_working_catalog.sum()),working_events_with_ml=int((e.in_v1_working_catalog&e.magnitude.notna()).sum()),
        usable_outside_nll_region=int((~e.in_region_nll&e.provisional_quality.eq('provisionally_usable')).sum()),region_disagreements=int(e.region_disagreement.sum()),
        associated_picks=len(phases),waveform_examples=len(examples),input_sha256=fingerprints,checks_passed=True)
    (OUT/'run.yaml').write_text(yaml.safe_dump(summary,sort_keys=False))
    table=stats[stats.grouping.eq('all')].to_string(index=False)
    report=f'''# Ridgecrest expert reference v1: provisional\n\nThe complete three-day pipeline is now exported as a provisional reference, not ground truth. No picks, locations, magnitude thresholds or reference pair identities were changed. Both mainshock limitations and catalog-wide velocity-model uncertainty remain explicit.\n\n## Products\n\n- `events.csv`: all {len(e):,} candidates, original fields and independent region/working-catalog flags. `magnitude` is populated only for provisional ML; `ml_provisional` retains the previous candidate estimate even when magnitude review is required. Always consult `magnitude_status`.\n- `phases.csv`: all {len(phases):,} associated picks, original PhaseNet identities/probabilities, GaMMA and NLL residuals and NLL travel times. Unassociated picks remain in stage 03.\n- `reference_status.csv`, `reference_matches.csv`, `comparison_groups.csv`: reference denominators, fixed pair identities, ambiguity and grouped comparisons.\n- `examples.csv`, `example_observations.csv`, `waveform_windows.csv`, `figures/`: four purpose-selected diagnostic cases and their source windows. These are observations for review, not manual event labels.\n- `run.yaml`: input/code identities, checks and counts.\n\n## Scope and interpretation\n\nEvent window: [2019-07-04, 2019-07-07) UTC. Study box: latitude 35.45–36.05, longitude -117.90–-117.20 (inclusive). NLL coordinates define the working export only; both locator coordinates and region-membership disagreement are preserved. This choice does not establish superior NLL accuracy.\n\nThere are **{summary['working_events']:,} working ordinary events**, of which **{summary['working_events_with_ml']:,} have provisional ML**. The {summary['usable_outside_nll_region']} numerically usable events outside the NLL study box remain in the master table. All location/association-review candidates and both mainshocks remain visible.\n\nReference comparisons deliberately retain the frozen stage-05 cohort: start 2019-07-04 15:35:29.4 UTC, end July 7, expert region membership based on GaMMA, reference membership based on native reference coordinates. They are not recall/precision estimates for the newly filtered working subset or for the full three days. Gates remain 2 s and 5 km using either locator, no depth gate; ambiguous assignments remain separate. Group fractions use the number of reference events in each group as denominator. Unmatched is not synonymous with missed/false. Geographic quadrants use latitude 35.75 and longitude -117.55.\n\nMagnitude bins in matching summaries use reference magnitudes, with potentially mixed types. Actual ML-difference statistics/plots use only Liu's declared ML and operational rows explicitly labeled ML; Shelly is excluded from same-type ML statistics because per-event types were not established. No magnitude calibration was fitted. Horizontal/time differences are descriptive; unresolved depth datums prevent pooled depth scoring.\n\n```text\n{table}\n```\n\n## Bounded waveform review\n\nSelect one case per category, breaking ties by ID: highest reference magnitude among operational unmatched references with zero candidate edges; most stations among usable expert events with zero candidate edges in all frozen comparisons; largest unambiguous reference horizontal discrepancy among usable events; largest candidate ML among magnitude-review working events. Exclude both mainshocks and avoid duplicate expert examples. Selection is intentionally diagnostic and cannot estimate an error rate.\n\nDisplay the nearest six eligible receivers (for the magnitude-support case, reserve places for the accepted amplitude receiver before filling by distance), vertical and one native horizontal component, 1–15 Hz, separately normalized counts, -12 to +65 s around the stated anchor. No response correction or physical-amplitude inference is made from these plots. Solid marks are target picks; circles are picks assigned elsewhere; short marks are unassociated picks. For an unmatched reference, all picks are non-target: its known origin time does not supply observed arrival times. Read padding uses only the original three-day file index.\n\nWaveform presence, pick support and competing associations can be examined, but visual alignment alone does not establish event identity, correct depth or a true/false label. Findings from these four cases must remain local.\n\n## Completion and remaining limits\n\nThis fixes a first provisional expert version with traceable event/pick links and explicit missing magnitudes. It does not resolve the velocity representation, mainshock depth, false-event rate, magnitude completeness or b-value. Ross is not included in these inherited comparisons; reference ingestion and equivalent scope/type checks remain required before making a Ross comparison. Do not tune parameters to force reference agreement. Subsequent modifications should produce a separate version.\n'''
    (OUT/'README.md').write_text(report)
    print(yaml.safe_dump({k:v for k,v in summary.items() if k!='input_sha256'},sort_keys=False),flush=True)
if __name__=='__main__': main()
