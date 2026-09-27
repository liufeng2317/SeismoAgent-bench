#!/usr/bin/env python3
"""Reference matching, bounded waveform review, and provisional quality flags."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import linear_sum_assignment
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from pyproj import Proj
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
CASE = HERE.parents[2] / 'benchmark_source/2019_ridgecrest_california'
OUT = HERE / 'export/05_review_catalog'
BLUE, ORANGE = '#0072B2', '#D55E00'


def dates(frame, names):
    cols = ['year', 'month', 'day', 'hour', 'minute']
    t = pd.to_datetime(frame[names[:5]].set_axis(cols, axis=1), utc=True)
    return t + pd.to_timedelta(frame[names[5]], unit='s')


def read_references():
    base = CASE / 'data/catalogs'
    files = {
        'Shelly': base/'SHELLY2020_0220190309/raw_article/SHELLY2020_0220190309__catalog_DataS1.txt',
        'Liu': base/'LIU2020_GL086189/LIU2020_GL086189__catalog_tableS1.txt',
        'Official': base/'USGS_SCSN_COMCAT_2019/USGS_SCSN_COMCAT_2019__catalog_operational_full.csv'}
    frames = {}
    s = pd.read_csv(files['Shelly'], sep=r'\s+', comment='#', header=None,
                    names=['year','month','day','hour','minute','second','latitude','longitude','depth_km','magnitude','reference_id'])
    s['time'] = dates(s, ['year','month','day','hour','minute','second'])
    s['reference_id'] = s.reference_id.astype(str)
    frames['Shelly'] = s
    s = pd.read_csv(files['Liu'], sep=r'\s+')
    s['time'] = dates(s, ['yr','mo','day','hr','min','sec'])
    s = s.rename(columns={'lat':'latitude','lon':'longitude','dep':'depth_km','mag':'magnitude'})
    s['reference_id'] = [f'liu_row_{i+1:05d}' for i in range(len(s))]
    frames['Liu'] = s
    s = pd.read_csv(files['Official'])
    s['time'] = pd.to_datetime(s.time, utc=True, format='ISO8601')
    s = s.rename(columns={'depth':'depth_km','mag':'magnitude','id':'reference_id'})
    frames['Official'] = s[s.type.eq('earthquake')].copy()
    for name, s in frames.items():
        s['catalog'] = name
        s['depth_datum'] = 'surface_0.7km_asl' if name=='Shelly' else 'unresolved_for_this_comparison'
    return frames, files


def region(frame, cfg):
    return (frame.latitude.between(*cfg['latitude_bounds']) &
            frame.longitude.between(*cfg['longitude_bounds']))


def match_catalog(events, ref, time_limit, distance_limit):
    """One fixed pairing for both locators; maximize count then minimize cost.

    An edge is eligible if either locator passes both gates. Cost is the smaller
    normalized time/distance norm among eligible locators. Ambiguity is retained.
    """
    rt = ref.time.astype('int64').to_numpy()/1e9
    et = events.time.astype('int64').to_numpy()/1e9
    nt = events.nll_time.astype('int64').to_numpy()/1e9
    edges = []
    for i, e in enumerate(events.to_dict('records')):
        js = np.union1d(np.arange(np.searchsorted(rt, et[i]-time_limit), np.searchsorted(rt, et[i]+time_limit, side='right')),
                        np.arange(np.searchsorted(rt, nt[i]-time_limit), np.searchsorted(rt, nt[i]+time_limit, side='right')))
        for j in js:
            r = ref.iloc[j]
            gd = np.hypot(e['gamma_x_km']-r.x_km, e['gamma_y_km']-r.y_km)
            nd = np.hypot(e['x_km']-r.x_km, e['y_km']-r.y_km)
            gt, ntime = et[i]-rt[j], nt[i]-rt[j]
            costs = []
            if abs(gt)<=time_limit and gd<=distance_limit: costs.append(np.hypot(gt/time_limit, gd/distance_limit))
            if abs(ntime)<=time_limit and nd<=distance_limit: costs.append(np.hypot(ntime/time_limit, nd/distance_limit))
            if costs: edges.append((i, int(j), min(costs), gt, ntime, gd, nd))
    degree_e = np.zeros(len(events), dtype=int)
    degree_r = np.zeros(len(ref), dtype=int)
    selected = {}
    if edges:
        ai, aj = np.array([(a,b) for a,b,*_ in edges]).T
        degree_e = np.bincount(ai, minlength=len(events))
        degree_r = np.bincount(aj, minlength=len(ref))
        graph = coo_matrix((np.ones(len(ai)), (ai, aj+len(events))), shape=(len(events)+len(ref),)*2)
        _, labels = connected_components(graph, directed=False)
        components = {}
        for edge in edges: components.setdefault(labels[edge[0]], []).append(edge)
        for component in components.values():
            ei = sorted({a[0] for a in component}); ri = sorted({a[1] for a in component})
            em = {v:k for k,v in enumerate(ei)}; rm = {v:k for k,v in enumerate(ri)}
            penalty = 2*min(len(ei), len(ri))+1
            cost = np.full((len(ei), len(ri)+len(ei)), float(penalty))
            cost[:, :len(ri)] = penalty*4
            lookup = {}
            for edge in component:
                i,j = edge[:2];cost[em[i],rm[j]] = edge[2];lookup[(i,j)] = edge
            rows, cols = linear_sum_assignment(cost)
            for a,b in zip(rows,cols):
                if b<len(ri) and (ei[a],ri[b]) in lookup: selected[ei[a]] = lookup[(ei[a],ri[b])]
    rows = []
    for i, e in enumerate(events.to_dict('records')):
        row = dict(event_id=e['event_id'], candidate_count=int(degree_e[i]), reference_id='',
                   matched=False, ambiguous=bool(degree_e[i]>1), reference_candidate_count=0,
                   gamma_dt_s=np.nan,nll_dt_s=np.nan,gamma_horizontal_km=np.nan,nll_horizontal_km=np.nan,
                   gamma_depth_difference_km=np.nan,nll_depth_difference_km=np.nan,
                   reference_depth_km=np.nan, reference_time='', reference_magnitude=np.nan)
        if i in selected:
            _, j, cost, gt, nt, gd, nd = selected[i];r=ref.iloc[j]
            row.update(reference_id=r.reference_id, matched=True, ambiguous=bool(degree_e[i]>1 or degree_r[j]>1),
                       reference_candidate_count=int(degree_r[j]),gamma_dt_s=gt,nll_dt_s=nt,
                       gamma_horizontal_km=gd,nll_horizontal_km=nd,reference_depth_km=r.depth_km,
                       reference_time=r.time.isoformat(),reference_magnitude=r.magnitude)
            if r.catalog=='Shelly' and 0<=r.depth_km<=40:
                row.update(gamma_depth_difference_km=e['gamma_depth_km']-r.depth_km,
                           nll_depth_difference_km=e['depth_km']-r.depth_km)
        rows.append(row)
    result = pd.DataFrame(rows)
    assert result.loc[result.matched, 'reference_id'].is_unique
    unmatched = ref[~ref.reference_id.isin(result.loc[result.matched,'reference_id'])].copy()
    unmatched['candidate_count'] = degree_r[unmatched.index]
    return result, unmatched


def quality(events, picks, matches, cfg):
    q = cfg['quality'];e=events.copy()
    bad = picks.assign(bad=picks.residual_s.abs()>q['residual_outlier_s']).groupby('event_id').bad.agg(['sum','mean'])
    e['residual_outlier_count'] = e.event_id.map(bad['sum']).astype(int)
    e['residual_outlier_fraction'] = e.event_id.map(bad['mean'])
    usable = matches[matches.matched & ~matches.ambiguous]
    e['unambiguous_reference_count'] = e.event_id.map(usable.groupby('event_id').size()).fillna(0).astype(int)
    flags=[];labels=[]
    for r in e.to_dict('records'):
        f=[]
        for name, cond in [
            ('nll_rejected',r['status']!='LOCATED'),
            ('depth_edge',r['depth_km']<q['depth_edge_km'] or r['depth_km']>25-q['depth_edge_km']),
            ('poor_azimuth_coverage',r['azimuth_gap_deg']>q['azimuth_gap_review_deg']),
            ('large_conditional_depth_sigma',r['posterior_sigma_depth_km']>q['depth_sigma_review_km']),
            ('large_locator_shift',r['horizontal_shift_km']>q['horizontal_shift_review_km']),
            ('large_rms',r['rms_unweighted_s']>q['rms_review_s'])]:
            if cond:f.append(name)
        association = (r['residual_outlier_count']>=q['association_review_min_outliers'] and
                       r['residual_outlier_fraction']>=q['association_review_fraction'])
        if association:f.append('multiple_arrival_residual_outliers')
        labels.append('association_review' if association else ('location_review' if f else 'provisionally_usable'))
        flags.append(';'.join(f))
    e['provisional_quality']=labels;e['review_reasons']=flags
    return e


def choose_examples(e, matches, refs):
    chosen=[];ids=set()
    def add(frame, reason, anchor=None):
        frame=frame[~frame.event_id.isin(ids)]
        if frame.empty:return
        r=frame.iloc[0];ids.add(r.event_id)
        chosen.append(dict(event_id=r.event_id, reason=reason,
                           anchor_time=(anchor if anchor is not None else r.nll_time).isoformat()))
    # Always inspect both mainshock windows; a nearby candidate is not an identity claim.
    official=refs['Official']
    for rid,label in [('ci38443183','M6.4'),('ci38457511','M7.1')]:
        r=official[official.reference_id.eq(rid)]
        if r.empty:raise ValueError(f'Missing mainshock anchor {rid}')
        anchor=r.iloc[0].time
        hits=matches[(matches.catalog=='Official') & (matches.reference_id==rid) & matches.matched]
        if len(hits):
            add(e[e.event_id.eq(hits.iloc[0].event_id)],f'{label}_matched_anchor',anchor)
        else:
            near=e.assign(anchor_distance_s=(e.nll_time-anchor).abs().dt.total_seconds()).sort_values(['anchor_distance_s','event_id'])
            add(near,f'{label}_window_nearest_candidate_not_identified',anchor)
    add(e[(e.provisional_quality=='provisionally_usable') & (e.unambiguous_reference_count>=2)].sort_values(['rms_unweighted_s','event_id']), 'ordinary_multi_reference_match')
    add(e[(e.depth_km<.5)&(e.unambiguous_reference_count>0)].sort_values(['n_stations','event_id'],ascending=[False,True]), 'shallow_matched')
    add(e[e.unambiguous_reference_count>0].sort_values(['horizontal_shift_km','event_id'],ascending=[False,True]), 'large_locator_shift_matched')
    add(e[e.provisional_quality.eq('association_review')].sort_values(['residual_outlier_fraction','event_id'],ascending=[False,True]), 'multiple_residual_outliers')
    add(e[e.status.ne('LOCATED')].sort_values(['rms_unweighted_s','event_id']), 'boundary_rejected')
    matched_ids=set(matches.loc[matches.matched,'event_id'])
    add(e[e.in_comparison_scope & ~e.event_id.isin(matched_ids) & e.provisional_quality.eq('provisionally_usable')].sort_values(['rms_unweighted_s','event_id']), 'unmatched_in_all_three_low_residual')
    assert len(chosen)==8
    return pd.DataFrame(chosen)


def save(fig, directory, name):
    directory.mkdir(exist_ok=True,parents=True)
    fig.savefig(directory/f'{name}.png',dpi=200)
    fig.savefig(directory/f'{name}.pdf',dpi=250)
    plt.close(fig)


def overview(matches, quality_table, stats, out):
    fig,axes=plt.subplots(1,3,figsize=(10,3.3),layout='constrained')
    catalogs=['Shelly','Liu','Official'];colors=[BLUE,ORANGE,'#009E73']
    for i,(catalog,color) in enumerate(zip(catalogs,colors)):
        m=matches[(matches.catalog==catalog)&matches.matched&~matches.ambiguous]
        for field,marker,offset in [('gamma_horizontal_km','o',-.1),('nll_horizontal_km','s',.1)]:
            v=m[field].quantile([.5,.9]).to_numpy()
            axes[0].plot([i+offset]*2,v,color=color,lw=1.5)
            axes[0].scatter(i+offset,v[0],color=color,marker=marker,s=20)
    axes[0].set(xticks=range(3),xticklabels=catalogs,ylabel='Horizontal difference (km)')
    axes[0].legend(handles=[Line2D([],[],marker='o',color='k',ls='',label='GaMMA'),Line2D([],[],marker='s',color='k',ls='',label='NonLinLoc')],frameon=False)
    s=matches[(matches.catalog=='Shelly')&matches.matched&~matches.ambiguous].dropna(subset=['nll_depth_difference_km'])
    lim=max(1,s[['gamma_depth_difference_km','nll_depth_difference_km']].abs().max().max())
    bins=np.linspace(-lim,lim,65)
    axes[1].hist([s.gamma_depth_difference_km,s.nll_depth_difference_km],bins=bins,histtype='step',color=[ORANGE,BLUE],label=['GaMMA','NonLinLoc'])
    axes[1].set(xlabel='Depth difference from Shelly (km)',ylabel='Matched events');axes[1].legend(frameon=False)
    counts=quality_table.provisional_quality.value_counts()
    labels=['provisionally_usable','location_review','association_review']
    axes[2].bar(range(3),[counts.get(x,0) for x in labels],color=[BLUE,'#E69F00',ORANGE])
    axes[2].set(xticks=range(3),xticklabels=['Provisional','Location\nreview','Association\nreview'],ylabel='Events')
    for ax,letter in zip(axes,'abc'):ax.text(-.12,1.03,letter,transform=ax.transAxes,weight='bold')
    save(fig,out,'01_reference_and_quality')
    fig,axes=plt.subplots(1,3,figsize=(10,3.1),layout='constrained')
    for ax,name in zip(axes,catalogs):
        m=matches[(matches.catalog==name)&matches.matched&~matches.ambiguous]
        ax.scatter(m.gamma_horizontal_km,m.nll_horizontal_km,s=3,alpha=.35,c=BLUE,linewidths=0,rasterized=True)
        hi=max(1,m[['gamma_horizontal_km','nll_horizontal_km']].max().max())*1.03
        ax.plot([0,hi],[0,hi],'k--',lw=.7)
        ax.set(xlim=(0,hi),ylim=(0,hi),xlabel='GaMMA horizontal difference (km)',ylabel='NonLinLoc horizontal difference (km)',title=name)
    save(fig,out,'02_paired_reference_differences')


def load_trace(task):
    """Read/display only; do not rewrite or response-correct raw observations."""
    from obspy import read, Stream, UTCDateTime
    rows, root, start, end, band = task
    st=Stream();paths=[]
    for r in rows:
        # Canonical filenames encode nominal file windows; table epochs can span days.
        times=re.findall(r'(\d{8}T\d{6})Z',r['path'])
        if len(times)!=2:raise ValueError(f'Unexpected waveform name: {r["path"]}')
        a,b=[UTCDateTime(t) for t in times]
        if b<=start-10 or a>=end+10:continue
        part=read(str(root/r['path']),starttime=start-10,endtime=end+10).select(id=r['seed_id'])
        if part:paths.append(r['path']);st+=part
    st.merge(method=-1)
    displayed=[]
    for tr in st:
        for segment in tr.split():
            if len(segment)<30:continue
            segment=segment.copy().detrend('linear').taper(max_percentage=.02,max_length=2.)
            segment.filter('bandpass',freqmin=band[0],freqmax=band[1],corners=3,zerophase=True)
            segment.trim(start,end)
            if segment.stats.npts:displayed.append(segment)
    return displayed,paths


def waveform_examples(examples,e,gp,npicks,stations,cfg,out):
    from obspy import UTCDateTime
    inputs=pd.read_csv(HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',keep_default_na=False)
    root=(CASE/'data/waveforms').resolve()
    alltimes=pd.to_datetime(gp.time_utc,utc=True,format='ISO8601')
    gp=gp.assign(t_seconds=alltimes.astype('int64')/1e9)
    records=[]
    for number,example in enumerate(examples.to_dict('records'),1):
        event=e.set_index('event_id').loc[example['event_id']]
        picks=gp[gp.event_id.eq(example['event_id'])].merge(npicks[['pick_id','predicted_travel_time_s']],on='pick_id',validate='one_to_one')
        ss=stations[stations.id.isin(picks.instrument_id)].copy()
        ss['distance_km']=np.hypot(ss['x(km)']-event.x_km,ss['y(km)']-event.y_km)
        ss=ss.sort_values(['distance_km','id'])
        ss=ss.iloc[np.unique(np.linspace(0,len(ss)-1,min(cfg['waveforms']['stations_per_example'],len(ss)),dtype=int))]
        anchor=UTCDateTime(example['anchor_time'])
        window=list(cfg['waveforms']['mainshock_window_s'] if example['reason'].startswith('M') else cfg['waveforms']['ordinary_window_s'])
        if not example['reason'].startswith('M'):
            # End shortly after selected arrivals so a later large event does not
            # hide this event through whole-window amplitude normalization.
            window[1]=min(window[1], float(picks.t_seconds.max()-float(anchor))+cfg['waveforms']['post_arrival_seconds'])
        start,end=anchor+window[0],anchor+window[1]
        tasks=[];labels=[]
        for s in ss.to_dict('records'):
            network,station,location,family=s['id'].split('.')
            rows=inputs[(inputs.station_id==s['station_id'])&(inputs.location==location)&(inputs.family==family)]
            components=set(rows.component)
            horizontal=next((x for x in ['N','1','E','2'] if x in components),None)
            for panel,comp in enumerate(['Z',horizontal]):
                selected=rows[rows.component.eq(comp)].to_dict('records')
                tasks.append((selected,root,start,end,cfg['waveforms']['bandpass_hz']))
                labels.append((s,panel,comp))
        with ThreadPoolExecutor(max_workers=cfg['waveforms']['workers']) as pool:
            loaded=list(pool.map(load_trace,tasks))
        fig,axes=plt.subplots(1,2,figsize=(11,6),sharex=True,sharey=True,layout='constrained')
        count=len(ss)
        for k,((s,panel,comp),(traces,paths)) in enumerate(zip(labels,loaded)):
            row=k//2;ax=axes[panel];level=count-1-row
            scale=max([np.max(np.abs(t.data)) for t in traces]+[1.])
            for tr in traces:
                x=np.arange(tr.stats.npts)/tr.stats.sampling_rate+float(tr.stats.starttime-anchor)
                ax.plot(x,level+.34*tr.data/scale,c='#252525',lw=.45,rasterized=True)
            pp=picks[picks.instrument_id.eq(s['id'])]
            for pick in pp.to_dict('records'):
                color=ORANGE if pick['phase']=='P' else BLUE
                actual=pick['t_seconds']-float(anchor)
                gamma=actual-float(pick['residual_s'])
                nll=float(UTCDateTime(event.origin_time)-anchor)+pick['predicted_travel_time_s']
                ax.vlines(actual,level-.38,level+.38,color=color,lw=1.)
                ax.vlines(nll,level-.38,level+.38,color=color,lw=.8,linestyles='--')
                ax.plot(gamma,level,marker='x',color=color,ms=4,mew=.8)
            other=gp[(gp.instrument_id==s['id'])&(gp.event_id!=example['event_id'])&gp.t_seconds.between(float(start),float(end))]
            ax.scatter(other.t_seconds-float(anchor),np.full(len(other),level-.44),c='#888888',marker='|',s=7,linewidths=.5)
            covered=sum(t.stats.npts/t.stats.sampling_rate for t in traces)
            records.append(dict(event_id=example['event_id'],instrument_id=s['id'],component=comp,
                                distance_km=s['distance_km'],start_utc=str(start),end_utc=str(end),
                                displayed_seconds=covered,display_scale_counts=scale,paths=';'.join(paths)))
        axes[0].set_yticks(range(count),[f"{s.station_id}  {s.distance_km:.0f} km" for s in ss.iloc[::-1].itertuples()])
        for ax,title in zip(axes,['Vertical component','Native horizontal component']):
            ax.set(xlim=window,ylim=(-.6,count-.4),xlabel='Time from window anchor (s)',title=title)
        title=f"{example['event_id']}  |  {str(anchor)[:23]} UTC"
        if example['reason'].startswith('M'):title=example['reason'].split('_')[0]+' window  |  '+title
        fig.suptitle(title,fontsize=10)
        handles=[Line2D([],[],color=ORANGE,label='P'),Line2D([],[],color=BLUE,label='S'),
                 Line2D([],[],color='k',label='Observed'),Line2D([],[],color='k',ls='--',label='NonLinLoc'),
                 Line2D([],[],color='k',ls='',marker='x',label='GaMMA'),Line2D([],[],color='#888888',ls='',marker='|',label='Other picks')]
        fig.legend(handles=handles,loc='outside lower center',ncol=6,frameon=False,fontsize=8)
        save(fig,out,f'{number:02d}_{example["event_id"]}')
        print('Waveform example',number,example['event_id'],example['reason'],flush=True)
    pd.DataFrame(records).to_csv(OUT/'waveform_windows.csv',index=False)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/validation.yaml').read_text())
    gpath=HERE/'export/03_associate_gamma/full';npath=HERE/'export/04_locate_nonlinloc/full'
    g=pd.read_csv(gpath/'events.csv');e=pd.read_csv(npath/'events.csv',keep_default_na=False)
    e=e.merge(g[['event_id','origin_time','longitude','latitude','x_km','y_km']].rename(columns={c:'gamma_'+c for c in ['origin_time','longitude','latitude','x_km','y_km']}),on='event_id',validate='one_to_one')
    e['time']=pd.to_datetime(e.gamma_origin_time,utc=True,format='ISO8601')
    e['nll_time']=pd.to_datetime(e.origin_time,utc=True,format='ISO8601')
    e['in_comparison_scope']=(e.time>=pd.Timestamp(cfg['common_start_utc']))&(e.time<pd.Timestamp(cfg['end_utc']))&region(e.rename(columns={'latitude':'nll_latitude','longitude':'nll_longitude','gamma_latitude':'latitude','gamma_longitude':'longitude'}),cfg)
    scoped=e[e.in_comparison_scope].sort_values('event_id').reset_index(drop=True)
    refs,files=read_references()
    proj=Proj(proj='aeqd',lon_0=-117.55,lat_0=35.75,datum='WGS84',units='km')
    all_matches=[];unmatched=[];summaries=[];reference_rows=[]
    for name,ref in refs.items():
        ref=ref[(ref.time>=pd.Timestamp(cfg['common_start_utc']))&(ref.time<pd.Timestamp(cfg['end_utc']))&region(ref,cfg)].sort_values(['time','reference_id']).reset_index(drop=True)
        ref['x_km'],ref['y_km']=proj(ref.longitude.to_numpy(),ref.latitude.to_numpy())
        reference_rows.append(ref[['catalog','reference_id','time','latitude','longitude','depth_km','magnitude','depth_datum']])
        for limits in [cfg['matching']['primary']]+cfg['matching']['sensitivity']:
            m,u=match_catalog(scoped,ref,*limits);m['catalog']=name
            pairs=m[m.matched];clear=pairs[~pairs.ambiguous]
            summaries.append(dict(catalog=name,time_gate_s=limits[0],distance_gate_km=limits[1],expert_scope_events=len(scoped),reference_scope_events=len(ref),matched=len(pairs),unambiguous=len(clear),unmatched_reference=len(u),
                                  median_gamma_horizontal_km=float(clear.gamma_horizontal_km.median()),median_nll_horizontal_km=float(clear.nll_horizontal_km.median()),
                                  median_gamma_abs_dt_s=float(clear.gamma_dt_s.abs().median()),median_nll_abs_dt_s=float(clear.nll_dt_s.abs().median())))
            if limits==cfg['matching']['primary']:all_matches.append(m);unmatched.append(u)
            print(name,limits,'matched',len(pairs),'unambiguous',len(clear),flush=True)
    matches=pd.concat(all_matches,ignore_index=True)
    matches.to_csv(OUT/'reference_matches.csv',index=False)
    pd.concat(reference_rows).to_csv(OUT/'reference_events.csv',index=False)
    pd.concat(unmatched)[['catalog','reference_id','time','latitude','longitude','depth_km','candidate_count']].to_csv(OUT/'unmatched_reference_events.csv',index=False)
    stats=pd.DataFrame(summaries);stats.to_csv(OUT/'matching_summary.csv',index=False)
    gp=pd.read_csv(gpath/'picks.csv',keep_default_na=False);npicks=pd.read_csv(npath/'picks.csv')
    q=quality(e,npicks,matches,cfg);q.to_csv(OUT/'event_quality.csv',index=False)
    examples=choose_examples(q,matches,refs)
    examples=examples.merge(q[['event_id','provisional_quality','status','depth_km','rms_unweighted_s','horizontal_shift_km','unambiguous_reference_count']],on='event_id',validate='one_to_one')
    examples.to_csv(OUT/'examples.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'axes.linewidth':.7})
    overview(matches,q,stats,OUT/'figures')
    waveform_examples(examples,q,gp,npicks,pd.read_csv(gpath/'stations.csv'),cfg,OUT/'figures/waveforms')
    paths=list(files.values())+[gpath/'events.csv',gpath/'picks.csv',gpath/'stations.csv',HERE/'export/01_prepare_inputs/full/waveform_inputs.csv',npath/'events.csv',npath/'picks.csv',HERE/'00_config/validation.yaml',Path(__file__)]
    record={'settings':cfg,'inputs':[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
            'events':len(q),'comparison_scope_events':len(scoped),'quality_counts':q.provisional_quality.value_counts().to_dict(),'waveform_examples':len(examples)}
    (OUT/'run.yaml').write_text(yaml.safe_dump(record,sort_keys=False))
    print(json.dumps(record['quality_counts']),flush=True)


if __name__=='__main__':main()
