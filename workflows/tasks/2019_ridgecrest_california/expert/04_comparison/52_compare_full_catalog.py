"""Export the complete candidate and compare fixed identities without rematching."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize

HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'export/52_full_catalog'
FIG=OUT/'figures'
XYZ=['x_km','y_km','depth_km']
LOCAL=CRS.from_proj4('+proj=aeqd +lat_0=35.75 +lon_0=-117.55 +datum=WGS84 +units=km')
TOXY=Transformer.from_crs(4326,LOCAL,always_xy=True)
TOLL=Transformer.from_crs(LOCAL,4326,always_xy=True)
COLORS={'original_nll':'#777777','absolute_all':'#E69F00','joint_all':'#0072B2'}
LABELS={'original_nll':'Original NLL','absolute_all':'Absolute only','joint_all':'Joint candidate'}


def save(fig,name):
    for ext in ['png','pdf']:fig.savefig(FIG/(name+'.'+ext),dpi=240,bbox_inches='tight')
    plt.close(fig)


def main():
    FIG.mkdir(exist_ok=True)
    status=pd.read_csv(OUT/'solver_status.csv');assert len(status)==4
    base=pd.read_csv(HERE/'export/10_validate_catalog/events.csv').set_index('event_id')
    work=base[base.in_v1_working_catalog].copy()
    positions=pd.read_csv(OUT/'branch_locations.csv')
    joint=positions[positions.branch.eq('joint_all')].set_index('event_id').loc[work.index]
    absolute=positions[positions.branch.eq('absolute_all')].set_index('event_id').loc[work.index]
    assert len(joint)==6520 and joint.index.is_unique and set(joint.index)==set(work.index)
    assert np.isfinite(joint[XYZ]).all().all()
    cc=pd.read_csv(OUT/'cc_measurements.csv');cc=cc[cc.accepted]
    incident=pd.concat([cc[['event_id_a','instrument_id','training']].rename(columns={'event_id_a':'event_id'}),cc[['event_id_b','instrument_id','training']].rename(columns={'event_id_b':'event_id'})])
    coverage=pd.DataFrame(index=work.index)
    for label,frame in [('all',incident),('training',incident[incident.training])]:
        g=frame.groupby('event_id')
        coverage['cc_'+label+'_edges']=g.size().reindex(work.index,fill_value=0)
        coverage['cc_'+label+'_instruments']=g.instrument_id.nunique().reindex(work.index,fill_value=0)
    available=pd.read_csv(OUT/'inputs/all_phases.csv',low_memory=False)
    additions=available[available.pick_id.str.startswith(('vp42_','mp44_','lb45_','eqs47_'))]
    coverage['additional_picks']=additions.groupby('event_id').size().reindex(work.index,fill_value=0)
    absolute_picks=available[~available.pick_id.str.startswith('eqs47_')]
    coverage['absolute_picks']=absolute_picks.groupby('event_id').size().reindex(work.index,fill_value=0)
    coverage['absolute_instruments']=absolute_picks.groupby('event_id').instrument_id.nunique().reindex(work.index,fill_value=0)
    coverage['relative_only_picks']=available[available.pick_id.str.startswith('eqs47_')].groupby('event_id').size().reindex(work.index,fill_value=0)
    coverage['horizontal_change_km']=np.hypot(joint.x_km-work.x_km,joint.y_km-work.y_km)
    coverage['depth_change_km']=joint.depth_km-work.depth_km
    coverage['original_depth_boundary']=(work.depth_km<.5)|(work.depth_km>24.5)
    coverage['candidate_depth_boundary']=(joint.depth_km<.5)|(joint.depth_km>24.5)
    coverage['weak_differential_geometry']=coverage.cc_all_instruments.between(1,2)
    coverage.to_csv(OUT/'event_quality.csv',index_label='event_id')
    # Preserve baseline diagnostics with explicit names; never relabel old posterior/errors as new.
    candidate=joint.copy();candidate['longitude'],candidate['latitude']=TOLL.transform(candidate.x_km.to_numpy(),candidate.y_km.to_numpy())
    candidate['depth_below_sea_level_km']=candidate.depth_km-.7
    candidate=candidate.join(coverage)
    for key in ['magnitude','magnitude_type','magnitude_status','period','mainshock_uncertainty']:
        candidate[key]=work[key]
    candidate['magnitude_geometry']='original_v1_not_recomputed'
    candidate['location_status']='experimental_full_joint_candidate'
    candidate['solver_success']=bool(status[status.branch.eq('joint_all')].success.iloc[0])
    candidate['new_location_uncertainty']='not_calibrated'
    candidate.to_csv(OUT/'working_catalog.csv',index_label='event_id')
    master=base.copy()
    # Only the new authoritative location columns are unprefixed in the master.
    keep={'origin_time','longitude','latitude','x_km','y_km','depth_km','depth_below_sea_level_km'}
    basecols={k:'v1_'+k for k in master.columns if k not in {'in_v1_working_catalog','magnitude','magnitude_type','magnitude_status','mainshock_uncertainty'}}
    master=master.rename(columns=basecols)
    for key in keep:
        master[key]=base[key]
        master.loc[candidate.index,key]=candidate[key]
    master['relocation_scope']=np.where(master.index.isin(candidate.index),'working_joint_candidate','unchanged_outside_working_scope')
    master['location_status']='unchanged_v1_review_only'
    master.loc[candidate.index,'location_status']='experimental_full_joint_candidate'
    master['magnitude_geometry']='original_v1_not_recomputed'
    master=master.join(coverage)
    assert len(master)==9942 and master.index.is_unique and set(master.index)==set(base.index)
    master.to_csv(OUT/'events.csv',index_label='event_id')
    matches=pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv')
    matches=matches[matches.event_id.isin(work.index)&matches.matched&~matches.ambiguous].copy()
    refs=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv')
    matches=matches.merge(refs[['catalog','reference_id','longitude','latitude']],on=['catalog','reference_id'],validate='many_to_one')
    matches['rx'],matches['ry']=TOXY.transform(matches.longitude.to_numpy(),matches.latitude.to_numpy())
    details=[];summary=[];strata=[]
    for branch,frame in [('original_nll',work),('absolute_all',absolute),('joint_all',joint)]:
        q=matches.merge(frame[XYZ+['origin_time']],left_on='event_id',right_index=True,validate='many_to_one')
        q['horizontal_km']=np.hypot(q.x_km-q.rx,q.y_km-q.ry)
        q['depth_comparison_eligible']=q.catalog.eq('Shelly') & q.reference_depth_km.between(0,40)
        q['nominal_depth_difference_km']=np.where(q.depth_comparison_eligible,q.depth_km-q.reference_depth_km,np.nan)
        q['absolute_depth_km']=q.nominal_depth_difference_km.abs()
        q['origin_difference_s']=(pd.to_datetime(q.origin_time,utc=True,format='ISO8601')-pd.to_datetime(q.reference_time,utc=True,format='ISO8601')).dt.total_seconds()
        q['branch']=branch;q['cc_supported']=q.event_id.map(coverage.cc_all_edges.gt(0));q['period']=q.event_id.map(work.period)
        details.append(q)
        for cat,h in q.groupby('catalog'):
            summary.append(dict(branch=branch,catalog=cat,n=len(h),n_depth=int(h.absolute_depth_km.notna().sum()),median_horizontal_km=h.horizontal_km.median(),p90_horizontal_km=h.horizontal_km.quantile(.9),median_abs_depth_km=h.absolute_depth_km.median(),p90_abs_depth_km=h.absolute_depth_km.quantile(.9),median_abs_origin_s=h.origin_difference_s.abs().median()))
        for (cat,period,support),h in q.groupby(['catalog','period','cc_supported']):
            strata.append(dict(branch=branch,catalog=cat,period=period,cc_supported=support,n=len(h),median_horizontal_km=h.horizontal_km.median(),median_abs_depth_km=h.absolute_depth_km.median()))
    detail=pd.concat(details,ignore_index=True);summary=pd.DataFrame(summary)
    detail.to_csv(OUT/'reference_comparison.csv',index=False);summary.to_csv(OUT/'reference_summary.csv',index=False);pd.DataFrame(strata).to_csv(OUT/'reference_strata.csv',index=False)
    timing=pd.read_csv(OUT/'metrics.csv')
    counts={b:int(((f.depth_km<.5)|(f.depth_km>24.5)).sum()) for b,f in [('original_nll',work),('absolute_all',absolute),('joint_all',joint)]}
    result={'master_events':len(master),'working_events':len(candidate),'unchanged_review_events':len(master)-len(candidate),'all_fits_successful':bool(status.success.all()),'accepted_cc_edges':len(cc),'cc_supported_events':int(coverage.cc_all_edges.gt(0).sum()),'without_cc_events':int(coverage.cc_all_edges.eq(0).sum()),'weak_differential_geometry_events':int(coverage.weak_differential_geometry.sum()),'events_with_added_picks':int(coverage.additional_picks.gt(0).sum()),'depth_boundary_counts':counts,'median_depth_change_km':float(coverage.depth_change_km.median()),'p90_abs_depth_change_km':float(coverage.depth_change_km.abs().quantile(.9)),'median_horizontal_change_km':float(coverage.horizontal_change_km.median()),'adopted_as_validated_v2':False,'status':'experimental_full_working_catalog','comparison_policy':'Original unambiguous fixed pairs, no rematching. Previously exposed catalogs, not blind validation. No new detections; inherited ML and mainshock limitations.','uncertainty':'No new posterior; original v1 diagnostics explicitly prefixed.','depth_comparison_policy':'Retain the stage05 reference-depth eligibility range 0..40 km; preserve every horizontal/time pair and fitted event.','excluded_shelly_depth_pairs':int(((detail.branch=='joint_all') & (detail.catalog=='Shelly') & ~detail.depth_comparison_eligible).sum())}
    (OUT/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    # Native-population reference maps: identical scope and symbols, not paired subsets.
    mapframes=[('Original NLL',work.reset_index().assign(time=work.origin_time.to_numpy())),('Joint candidate',candidate.reset_index().assign(time=candidate.origin_time.to_numpy()))]
    for name in ['Official','Liu','Shelly']:mapframes.append(('Reference: '+name,refs[refs.catalog.eq(name)].copy()))
    oldmaps=pd.read_csv(HERE/'export/11_plot_catalog_maps/plotted_events.csv')
    ross=oldmaps[(oldmaps.figure=='working_subset')&(oldmaps.catalog=='Ross_relocated')].copy()
    mapframes.append(('Reference: Ross relocated',ross))
    fig,axes=plt.subplots(2,3,figsize=(10,8),sharex=True,sharey=True,layout='constrained');pop=[]
    for i,((label,d),ax) in enumerate(zip(mapframes,axes.ravel())):
        t=pd.to_datetime(d.time,utc=True,format='ISO8601');mask=t.ge(pd.Timestamp('2019-07-04T15:35:29.4Z'))&t.lt(pd.Timestamp('2019-07-07T00:00:00Z'))&d.longitude.between(-117.9,-117.2)&d.latitude.between(35.45,36.05);d=d[mask]
        ax.scatter(d.longitude,d.latitude,s=.8,c='#252525',alpha=.35,linewidths=0,rasterized=True)
        ax.set(xlim=(-117.9,-117.2),ylim=(35.45,36.05));ax.set_aspect(1/np.cos(np.deg2rad(35.75)))
        ax.set_title(f'{"abcdef"[i]}  {label}',loc='left');ax.text(.97,.97,f'N = {len(d):,}',ha='right',va='top',transform=ax.transAxes)
        if i>=3:ax.set_xlabel('Longitude (°)')
        if i%3==0:ax.set_ylabel('Latitude (°N)')
        pop.append({'catalog':label,'plotted_events':len(d)})
    save(fig,'01_catalog_maps');pd.DataFrame(pop).to_csv(OUT/'map_populations.csv',index=False)
    # Same IDs and complete coordinate ranges for the depth sections.
    fig,axes=plt.subplots(2,3,figsize=(12,8),layout='constrained');norm=Normalize(0,25)
    ranges={k:(min(work[k].min(),joint[k].min())-1,max(work[k].max(),joint[k].max())+1) for k in ['x_km','y_km']}
    flags=coverage.candidate_depth_boundary
    for row,(frame,name) in enumerate([(work,'Original NLL'),(joint,'Joint candidate')]):
        for col,(x,y) in enumerate([('x_km','y_km'),('x_km','depth_km'),('y_km','depth_km')]):
            ax=axes[row,col];sc=ax.scatter(frame[x],frame[y],c=frame.depth_km,cmap='viridis_r',norm=norm,s=2,alpha=.55,linewidths=0,rasterized=True)
            ax.scatter(frame.loc[flags,x],frame.loc[flags,y],s=12,facecolors='none',edgecolors='#D55E00',linewidths=.5,rasterized=True)
            ax.set_xlim(ranges[x]);ax.set_ylim(ranges[y] if col==0 else (25.5,-.5));ax.set_xlabel('East (km)' if x=='x_km' else 'North (km)');ax.set_ylabel('North (km)' if col==0 else 'Model depth (km)');ax.set_title(f'{"abcdef"[row*3+col]}  {name}',loc='left')
            if col==0:ax.set_aspect('equal',adjustable='box')
    fig.colorbar(sc,ax=axes,label='Model depth (km)',shrink=.75);save(fig,'02_depth_sections')
    # Fixed-pair horizontal and nominal depth distributions; no x-axis truncation.
    fig,axes=plt.subplots(2,2,figsize=(9,7),layout='constrained')
    for ax,cat in zip(axes.ravel()[:3],['Liu','Official','Shelly']):
        for branch in COLORS:
            values=np.sort(detail[(detail.branch==branch)&(detail.catalog==cat)].horizontal_km.to_numpy());ax.plot(values,np.arange(1,len(values)+1)/len(values),color=COLORS[branch],label=LABELS[branch],lw=1.3)
        ax.set_title(cat,loc='left');ax.set_xlabel('Horizontal discrepancy (km)');ax.set_ylabel('Cumulative fraction')
    ax=axes[1,1]
    for branch in COLORS:
        values=np.sort(detail[(detail.branch==branch)&(detail.catalog=='Shelly')].absolute_depth_km.dropna().to_numpy());ax.plot(values,np.arange(1,len(values)+1)/len(values),color=COLORS[branch],label=LABELS[branch],lw=1.3)
    ax.set_title('Shelly: nominal depth',loc='left');ax.set_xlabel('Absolute depth discrepancy (km)');ax.set_ylabel('Cumulative fraction');axes[0,0].legend(frameon=False,fontsize=8);save(fig,'03_reference_discrepancies')
    # Same matched event population per reference: reference positions alongside ours.
    fig,axes=plt.subplots(3,3,figsize=(10,11),layout='constrained')
    for row,cat in enumerate(['Liu','Official','Shelly']):
        q=detail[(detail.catalog==cat)&(detail.branch=='joint_all')];ids=q.event_id
        frames=[('Original NLL',work.loc[ids,'x_km'],work.loc[ids,'y_km']),('Reference: '+cat,q.rx,q.ry),('Joint candidate',joint.loc[ids,'x_km'],joint.loc[ids,'y_km'])]
        xx=np.concatenate([np.asarray(f[1]) for f in frames]);yy=np.concatenate([np.asarray(f[2]) for f in frames])
        for col,(name,x,y) in enumerate(frames):
            ax=axes[row,col];ax.scatter(x,y,s=1.2,c='#252525',alpha=.4,linewidths=0,rasterized=True);ax.set(xlim=(xx.min()-1,xx.max()+1),ylim=(yy.min()-1,yy.max()+1));ax.set_aspect('equal',adjustable='box');ax.set_title(name,loc='left');ax.set_xlabel('East (km)');ax.set_ylabel('North (km)')
    save(fig,'04_matched_reference_maps')
    lines=['# Full working-catalog candidate','', '**Status: experimental full-scale result, not an adopted validated v2.** The stage51 depth failure remains part of the evidence. This user-authorized application fixes the scientific method and expands its event-pair graph; it is not optimization round31 or a fresh blind confirmation.','',
        '## Products','',f'- `working_catalog.csv`: all {len(candidate):,} relocated ordinary working events, with per-event CC coverage and depth flags.',f'- `events.csv`: all {len(master):,} original master IDs; {len(master)-len(candidate):,} non-working records retain their original locations. Original diagnostic fields are prefixed `v1_`.', '- `phases.csv`: observations for the full working candidate, candidate residuals and explicit absolute-use flags. Original master phases remain in stage10.', '- `event_quality.csv`: per-event coverage, changes and boundary flags; none are removed.', '- Magnitudes are inherited v1 estimates at original geometry, not newly calculated ML. Mainshock uncertainties are not resolved by this ordinary-event application. No new location posterior is claimed.','', '## Scope and coverage','',f'All four fits successful: {bool(status.success.all())}. Accepted CC edges: {len(cc):,}; events with CC: {result["cc_supported_events"]:,}/{len(candidate):,}; events without CC: {result["without_cc_events"]:,}. Added-pick coverage: {result["events_with_added_picks"]:,} events. No new picker inference was run; previously admitted additions are heterogeneous across the full catalog.',f'Depth-boundary counts (model depth <0.5 or >24.5 km): original {counts["original_nll"]}, matched absolute {counts["absolute_all"]}, joint {counts["joint_all"]}. Median signed depth change: {result["median_depth_change_km"]:.3f} km; P90 absolute change: {result["p90_abs_depth_change_km"]:.3f} km. These flags are numerical safeguards, not ground-truth errors.','', '## Fixed-reference comparisons','', '| Catalog | Branch | Pairs | Median horizontal km | P90 horizontal km | Depth pairs | Nominal median depth km | Median absolute origin difference s |','| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for r in summary.itertuples():lines.append(f'| {r.catalog} | {LABELS[r.branch]} | {r.n} | {r.median_horizontal_km:.3f} | {r.p90_horizontal_km:.3f} | {r.n_depth} | {format(r.median_abs_depth_km, ".3f") if r.n_depth else "—"} | {r.median_abs_origin_s:.3f} |')
    lines += ['', 'Reference pairs are inherited stage10 unambiguous matches, never rematched using candidate outcomes. Different catalogs have different matched populations. Shelly depth differences retain the existing nominal common-datum convention and the pre-existing stage05 eligibility range 0–40 km; references are not truth. The local raw Shelly file contains24 matched depth values outside that range (41.640–239.530 km). They remain in the horizontal/time comparisons and all event tables, but are excluded from depth scoring for every branch. Thus depth statistics use4,377 pairs versus4,401 horizontal/time pairs; `depth_comparison_eligible` makes this explicit. This fixes the initial full-report depth eligibility omission and does not alter any fit or historic stage51 score. Ross provides native relocated spatial context only; it has no frozen pairwise score in this workflow. No event-detection or completeness gain is inferred from relocation.', '', '## Held-instrument predictions', '', '| Branch | Observation | N | RMS s |','| --- | --- | ---: | ---: |']
    for r in timing[timing.heldout].itertuples():lines.append(f'| {r.branch} | {r.kind} | {r.n} | {r.rms_s:.6f} |')
    lines += ['', 'Only withheld branches are prediction tests. All-station branch residuals are fitted diagnostics. This full application does not rerun the earlier common-start perturbation suite or establish independent generalization.', '', '## Figures','', '- [Native-population maps](figures/01_catalog_maps.png): common July4 15:35:29.4–July7 UTC interval and common geographic box, identical symbols. Native-population sizes differ.', '- [Same-event map and depth sections](figures/02_depth_sections.png): all6,520 IDs, identical ranges; orange rings identify the same joint boundary flags in both rows. All-event EW/NS projections, not narrow fault-normal profiles. Model depth is relative to the +0.7km datum plane.', '- [Reference discrepancy distributions](figures/03_reference_discrepancies.png): fixed pairs, full ranges including tails.', '- [Matched-population maps](figures/04_matched_reference_maps.png): each row has identical matched event identities in baseline/reference/candidate panels; no thinning.', '', 'PDF versions accompany each PNG. `reference_summary.csv`, `reference_strata.csv`, `reference_comparison.csv` and `map_populations.csv` retain quantitative results and population definitions. Logs: `01_pipeline/logs/52_full_catalog/`. Reproduce using `01_pipeline/run_52_full_catalog.sh`.']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(result,indent=2),flush=True);print(summary.to_string(index=False),flush=True)

if __name__=='__main__':main()
