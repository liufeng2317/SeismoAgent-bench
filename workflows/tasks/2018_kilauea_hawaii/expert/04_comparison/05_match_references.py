#!/usr/bin/env python3
"""Match the expert catalog against the Kilauea 2018 summit references; round feedback.

References (all located): Shelly & Thelen (2019) data S1 hypocentroids
(primary; template matching + hypoDD), Wei et al. (2022) data S1 (3-D
NonLinLoc, island-wide), Matoza et al. (2021) GrowClust relocations
(relocated rows only, nbranch > 1) and ComCat/HVO. Runs after 04 full and
before 09/10; stage 10 imports this module.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
from pathlib import Path
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
BLUE, ORANGE, GREEN, PURPLE = '#0072B2', '#D55E00', '#009E73', '#7B5EA7'
CATALOGS = ['shelly', 'wei', 'matoza', 'comcat']
LOCATED = CATALOGS     # every Kilauea reference has hypocentres
COLORS = {'shelly': BLUE, 'wei': ORANGE, 'matoza': PURPLE, 'comcat': GREEN}
LABELS = {'shelly': 'Shelly 2019', 'wei': 'Wei 2022', 'matoza': 'Matoza 2021', 'comcat': 'ComCat/HVO'}


def read_comcat(path):
    s = pd.read_csv(path)
    s['time'] = pd.to_datetime(s.time, utc=True, format='ISO8601')
    s = s.rename(columns={'depth': 'depth_km', 'mag': 'magnitude', 'id': 'reference_id'})
    s = s[s.type.eq('earthquake')].copy()
    s['magnitude_type'] = s.magType.fillna('unknown').str.upper()
    s['depth_datum'] = 'comcat'
    return s


def read_shelly(path):
    """Data S1: yyyy mm dd HH MM SS.SSS lat lon depth x y z magnitude eventID ('%' header)."""
    s = pd.read_csv(path, sep=r'\s+', comment='%', header=None,
                    names=['y', 'mo', 'd', 'h', 'mi', 'sec', 'latitude', 'longitude', 'depth_km',
                           'x', 'yy', 'z', 'magnitude', 'reference_id'])
    s['time'] = (pd.to_datetime(dict(year=s.y, month=s.mo, day=s.d, hour=s.h, minute=s.mi), utc=True)
                 + pd.to_timedelta(s.sec, unit='s'))
    s['reference_id'] = 'sh_' + s.reference_id.astype(str)
    s['magnitude_type'] = 'unresolved'
    s['depth_datum'] = 'unstated'
    return s


def read_wei(path):
    """Data S1: SourceTime Lat Lon Dep ... Mag MagType StdMag; Mag may be 'Unk'; no event id."""
    s = pd.read_csv(path, sep=r'\s+', comment='#')
    s['time'] = pd.to_datetime(s.SourceTime, utc=True, format='ISO8601')
    s = s.rename(columns={'Lat': 'latitude', 'Lon': 'longitude', 'Dep': 'depth_km'})
    s['magnitude'] = pd.to_numeric(s.Mag, errors='coerce')
    s['magnitude_type'] = s.MagType.astype(str)
    s['reference_id'] = ['wei_%d' % i for i in range(len(s))]
    s['depth_datum'] = 'unstated'
    return s


def read_matoza(path):
    """GrowClust-format rows; relocated coordinates (cols 8-10) of relocated events (nbranch > 1)."""
    cols = ['y', 'mo', 'd', 'h', 'mi', 'sec', 'eid', 'latitude', 'longitude', 'depth_km', 'magnitude',
            'qid', 'cid', 'nbranch', 'npair', 'ndp', 'nds', 'rmsp', 'rmss', 'eh', 'ez', 'et',
            'latc', 'lonc', 'depc', 'poly']
    s = pd.read_csv(path, sep=r'\s+', header=None, names=cols)
    s = s[s.nbranch > 1].copy()
    s['time'] = (pd.to_datetime(dict(year=s.y, month=s.mo, day=s.d, hour=s.h, minute=s.mi), utc=True)
                 + pd.to_timedelta(s.sec, unit='s'))
    s['reference_id'] = 'mat_' + s.eid.astype(str)
    s['magnitude_type'] = 'unresolved'
    s['depth_datum'] = 'unstated'
    return s


def read_comcat(path):
    s = pd.read_csv(path)
    s['time'] = pd.to_datetime(s.time, utc=True, format='ISO8601')
    s = s.rename(columns={'depth': 'depth_km', 'mag': 'magnitude', 'id': 'reference_id'})
    s = s[s.type.eq('earthquake')].copy()
    s['magnitude_type'] = s.magType.fillna('unknown').str.upper()
    s['depth_datum'] = 'comcat'
    return s


def read_references(case_root, entries):
    readers = {'shelly_s1': read_shelly, 'wei_s1': read_wei, 'matoza_growclust': read_matoza,
               'comcat_csv': read_comcat}
    frames = {}; notes = {}
    for name, spec in entries.items():
        frames[name] = readers[spec['format']]((case_root / spec['path']).resolve())
        frames[name]['catalog'] = name
        assert frames[name].reference_id.is_unique, name
    return frames, notes


def region(frame, cfg):
    return (frame.latitude.between(*cfg['region']['latitude_bounds']) &
            frame.longitude.between(*cfg['region']['longitude_bounds']))


def reference_mask(frame, cfg):
    """Window for every reference; the box and depth limits only where located."""
    inside = ((frame.time >= pd.Timestamp(cfg['window']['start_utc'])) &
              (frame.time < pd.Timestamp(cfg['window']['end_utc'])))
    if frame.latitude.notna().any():
        inside &= region(frame, cfg) & frame.depth_km.between(*cfg['depth_bounds_km'])
    return inside


def match_catalog(events, ref, time_limit, distance_limit):
    """One fixed pairing for both locators; maximize count then minimize cost.

    An edge is eligible if either locator passes both gates. Cost is the smaller
    normalized time/distance norm among eligible locators. Ambiguity is retained.
    A reference without coordinates (time-only) passes the distance gate.
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
            located = np.isfinite(r.x_km)
            gd = np.hypot(e['gamma_x_km']-r.x_km, e['gamma_y_km']-r.y_km) if located else 0.
            nd = np.hypot(e['x_km']-r.x_km, e['y_km']-r.y_km) if located else 0.
            gt, ntime = et[i]-rt[j], nt[i]-rt[j]
            costs = []
            if abs(gt)<=time_limit and gd<=distance_limit: costs.append(np.hypot(gt/time_limit, gd/distance_limit))
            if abs(ntime)<=time_limit and nd<=distance_limit: costs.append(np.hypot(ntime/time_limit, nd/distance_limit))
            if costs: edges.append((i, int(j), min(costs), gt, ntime,
                                    gd if located else np.nan, nd if located else np.nan))
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
                   reference_depth_km=np.nan, reference_time='', reference_magnitude=np.nan,
                   reference_magnitude_type='')
        if i in selected:
            _, j, cost, gt, nt, gd, nd = selected[i];r=ref.iloc[j]
            row.update(reference_id=r.reference_id, matched=True, ambiguous=bool(degree_e[i]>1 or degree_r[j]>1),
                       reference_candidate_count=int(degree_r[j]),gamma_dt_s=gt,nll_dt_s=nt,
                       gamma_horizontal_km=gd,nll_horizontal_km=nd,reference_depth_km=r.depth_km,
                       reference_time=r.time.isoformat(),reference_magnitude=r.magnitude,
                       reference_magnitude_type=r.magnitude_type)
            # Reference depth datums are unstated (summit ~1.1 km ASL; HVO depth
            # datums are mixed historically): depth_km compared directly, caveated.
            if np.isfinite(r.depth_km):
                row.update(gamma_depth_difference_km=e['gamma_depth_km']-r.depth_km,
                           nll_depth_difference_km=e['depth_km']-r.depth_km)
        rows.append(row)
    result = pd.DataFrame(rows)
    assert result.loc[result.matched, 'reference_id'].is_unique
    unmatched = ref[~ref.reference_id.isin(result.loc[result.matched,'reference_id'])].copy()
    unmatched['candidate_count'] = degree_r[unmatched.index]
    return result, unmatched


def quality(events, picks, matches, cfg, depth_bounds):
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
            ('depth_edge',r['depth_km']<depth_bounds[0]+q['depth_edge_km'] or r['depth_km']>depth_bounds[1]-q['depth_edge_km']),
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


def choose_examples(e, matches, anchor_id, anchor_time):
    chosen=[];ids=set()
    def add(frame, reason, anchor=None):
        frame=frame[~frame.event_id.isin(ids)]
        if frame.empty:return
        r=frame.iloc[0];ids.add(r.event_id)
        chosen.append(dict(event_id=r.event_id, reason=reason,
                           anchor_time=(anchor if anchor is not None else r.nll_time).isoformat()))
    # The mainshock window first; a nearby candidate is not an identity claim.
    for catalog, rid in ([('comcat', anchor_id)] if anchor_id else []):
        hits=matches[(matches.catalog==catalog) & (matches.reference_id==rid) & matches.matched]
        if len(hits):
            add(e[e.event_id.eq(hits.iloc[0].event_id)],'mainshock_matched_anchor',anchor_time)
        else:
            near=e.assign(anchor_distance_s=(e.nll_time-anchor_time).abs().dt.total_seconds()).sort_values(['anchor_distance_s','event_id'])
            add(near,'mainshock_window_nearest_candidate_not_identified',anchor_time)
    add(e[(e.provisional_quality=='provisionally_usable') & (e.unambiguous_reference_count>=2)].sort_values(['rms_unweighted_s','event_id']), 'ordinary_multi_reference_match')
    add(e[(e.depth_km<2)&(e.unambiguous_reference_count>0)].sort_values(['n_stations','event_id'],ascending=[False,True]), 'shallow_matched')
    add(e[e.unambiguous_reference_count>0].sort_values(['horizontal_shift_km','event_id'],ascending=[False,True]), 'large_locator_shift_matched')
    add(e[e.provisional_quality.eq('association_review')].sort_values(['residual_outlier_fraction','event_id'],ascending=[False,True]), 'multiple_residual_outliers')
    add(e[e.status.ne('LOCATED')].sort_values(['rms_unweighted_s','event_id']), 'boundary_rejected')
    matched_ids=set(matches.loc[matches.matched,'event_id'])
    add(e[e.in_comparison_scope & ~e.event_id.isin(matched_ids) & e.provisional_quality.eq('provisionally_usable')].sort_values(['rms_unweighted_s','event_id']), 'unmatched_in_all_references_low_residual')
    return pd.DataFrame(chosen)


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


def save(fig, directory, name):
    directory.mkdir(exist_ok=True,parents=True)
    fig.savefig(directory/f'{name}.png',dpi=200)
    fig.savefig(directory/f'{name}.pdf',dpi=250)
    plt.close(fig)


def figures(matches, stats, quality_table, out):
    fig,axes=plt.subplots(1,3,figsize=(10,3.3),layout='constrained')
    primary=stats[stats.gate.eq('primary')].set_index('catalog')
    x=np.arange(len(CATALOGS))
    axes[0].bar(x-.2,[primary.loc[c,'matched_fraction'] for c in CATALOGS],width=.4,color=[COLORS[c] for c in CATALOGS])
    axes[0].bar(x+.2,[primary.loc[c,'matched_fraction_v1'] for c in CATALOGS],width=.4,color=[COLORS[c] for c in CATALOGS],alpha=.45,hatch='//')
    axes[0].set(xticks=x,xticklabels=[LABELS[c] for c in CATALOGS],ylim=(0,1),ylabel='Reference matched fraction')
    axes[0].tick_params(axis='x',labelsize=6)
    from matplotlib.patches import Patch
    axes[0].legend(handles=[Patch(facecolor='k',label='All candidates'),Patch(facecolor='k',alpha=.5,hatch='////',label='v1 working')],frameon=False,fontsize=7)
    for axis,fields,xlabel,catalogs in [(axes[1],('gamma_dt_s','nll_dt_s'),'|Origin-time difference| (s)',CATALOGS),
                                        (axes[2],('gamma_horizontal_km','nll_horizontal_km'),'Epicentral difference (km)',LOCATED)]:
        for catalog in catalogs:
            m=matches[(matches.catalog==catalog)&matches.matched&~matches.ambiguous]
            for field,ls,locator in [(fields[0],'--','GaMMA'),(fields[1],'-','NLL')]:
                v=np.sort(np.abs(m[field].dropna()))
                if len(v):axis.plot(v,np.arange(1,len(v)+1)/len(v),ls,color=COLORS[catalog],lw=1,
                                    label=f'{LABELS[catalog]} {locator}')
        axis.set(xlabel=xlabel,ylabel='Cumulative fraction',xlim=(0,None))
        axis.legend(frameon=False,fontsize=5.5)
    for ax,letter in zip(axes,'abc'):ax.text(-.12,1.03,letter,transform=ax.transAxes,weight='bold')
    save(fig,out,'01_matched_fractions_and_differences')
    fig,axes=plt.subplots(1,len(LOCATED),figsize=(3.6*len(LOCATED),3.1),layout='constrained',squeeze=False)
    for ax,name in zip(axes[0],LOCATED):
        m=matches[(matches.catalog==name)&matches.matched&~matches.ambiguous]
        ax.scatter(m.gamma_horizontal_km,m.nll_horizontal_km,s=3,alpha=.35,c=BLUE,linewidths=0,rasterized=True)
        hi=max(1,m[['gamma_horizontal_km','nll_horizontal_km']].max().max())*1.03
        ax.plot([0,hi],[0,hi],'k--',lw=.7)
        ax.set(xlim=(0,hi),ylim=(0,hi),xlabel='GaMMA horizontal difference (km)',ylabel='NonLinLoc horizontal difference (km)',title=LABELS[name])
    save(fig,out,'02_paired_reference_differences')


def locations_figure(q, refs, stations, anchor, out, cfg):
    """Epicentre map and depth sections (below the model datum) vs the Shelly catalog."""
    box = cfg['region']
    lon = box['longitude_bounds']; lat = box['latitude_bounds']
    pad = 0.05
    extent = [lon[0]-pad, lon[1]+pad, lat[0]-pad, lat[1]+pad]
    v1 = q[q.in_v1_working_catalog]
    cc = refs[refs.catalog.eq('shelly')]
    fig, axes = plt.subplots(2, 2, figsize=(8, 6.6), layout='constrained')
    ax = axes[0, 0]
    ax.scatter(v1.longitude, v1.latitude, s=1.3, c='0.6', alpha=.45, linewidths=0, rasterized=True, label='Expert v1')
    ax.scatter(cc.longitude, cc.latitude, s=1.6, c=COLORS['shelly'], alpha=.5, linewidths=0, rasterized=True, label=LABELS['shelly'])
    ax.plot(anchor['longitude'], anchor['latitude'], marker='*', ms=9, mfc='none', mec='k', mew=.9, ls='none', label=f"M{anchor['magnitude']:g} mainshock")
    ax.scatter(stations.longitude, stations.latitude, marker='^', s=14, c='k', alpha=.6, linewidths=0, label='Stations')
    ax.plot([lon[0], lon[1], lon[1], lon[0], lon[0]], [lat[0], lat[0], lat[1], lat[1], lat[0]], c='k', lw=.6, ls=':')
    ax.set(xlim=extent[:2], ylim=extent[2:], xlabel='Longitude', ylabel='Latitude')
    ax.legend(frameon=False, fontsize=5.5, loc='lower left', markerscale=2.5, handletextpad=.2, borderaxespad=.2)
    for ax, axis, key in [(axes[0, 1], 'longitude', 'Longitude'), (axes[1, 0], 'latitude', 'Latitude')]:
        ax.scatter(v1[axis], v1.depth_km, s=1.3, c='0.6', alpha=.45, linewidths=0, rasterized=True)
        ax.scatter(cc[axis], cc.depth_km, s=1.6, c=COLORS['shelly'], alpha=.5, linewidths=0, rasterized=True)
        ax.plot([anchor[axis]], [anchor['depth_km']], marker='*', ms=9, mfc='none', mec='k', mew=.9, ls='none')
        ax.set(xlim=extent[:2] if axis == 'longitude' else extent[2:], ylim=(20, -1),
               xlabel=key, ylabel='Depth below local surface (km)')
    ax = axes[1, 1]
    bins = np.linspace(-1, 20, 43)
    ax.hist(v1.depth_km, bins=bins, color='0.6', alpha=.7, label='Expert v1')
    ax.hist(cc.depth_km, bins=bins, histtype='step', lw=1, color=COLORS['shelly'], label=LABELS['shelly'])
    ax.set(xlabel='Depth below local surface (km)', ylabel='Events', yscale='log')
    ax.legend(frameon=False, fontsize=5.5)
    for ax, letter in zip(axes.flat, 'abcd'):
        ax.text(-.14, 1.04, letter, transform=ax.transAxes, weight='bold')
    save(fig, out, '03_location_maps_and_depth_sections')


def main():
    cfg=yaml.safe_load((HERE/'00_config/validation.yaml').read_text())
    settings=yaml.safe_load((HERE/'00_config/association.yaml').read_text())
    main_cfg=yaml.safe_load((HERE/'00_config/config.yaml').read_text())
    OUT=(HERE/main_cfg['export_root']/'05_match_references');OUT.mkdir(parents=True,exist_ok=True)
    case_root=(HERE/main_cfg['case_root']).resolve()
    datum=float(settings['reference_elevation_km']);depth_bounds=settings['depth_bounds_km']
    gpath=HERE/main_cfg['export_root']/'03_associate_gamma/full';npath=HERE/main_cfg['export_root']/'04_locate_nonlinloc/full'
    # Since r8, stage 45 (depth prior for weakly constrained events) refines the
    # stage-04 table; use it when the round has it.
    epath=HERE/main_cfg['export_root']/'45_depth_prior/events.csv'
    epath=epath if epath.is_file() else npath/'events.csv'
    print(f'locations from {epath.relative_to(HERE)}',flush=True)
    g=pd.read_csv(gpath/'events.csv');e=pd.read_csv(epath,keep_default_na=False)
    e=e.merge(g[['event_id','origin_time','longitude','latitude','x_km','y_km']].rename(columns={c:'gamma_'+c for c in ['origin_time','longitude','latitude','x_km','y_km']}),on='event_id',validate='one_to_one')
    e['time']=pd.to_datetime(e.gamma_origin_time,utc=True,format='ISO8601')
    e['nll_time']=pd.to_datetime(e.origin_time,utc=True,format='ISO8601')
    e['in_comparison_scope']=(e.time>=pd.Timestamp(cfg['window']['start_utc']))&(e.time<pd.Timestamp(cfg['window']['end_utc']))&region(e.rename(columns={'latitude':'nll_latitude','longitude':'nll_longitude','gamma_latitude':'latitude','gamma_longitude':'longitude'}),cfg)
    scoped=e[e.in_comparison_scope].sort_values('event_id').reset_index(drop=True)
    refs,notes=read_references(case_root,cfg['references'])
    anchor=pd.Timestamp(main_cfg['mainshock']['time_utc'])
    # in_window false (Prague: before the window; Kilauea: Mw 6.9 outside the summit box).
    anchor_id=main_cfg['mainshock']['event_id'] if main_cfg['mainshock'].get('in_window',True) else None
    proj=Proj(proj='aeqd',lon_0=settings['projection_center'][0],lat_0=settings['projection_center'][1],datum='WGS84',units='km')
    all_matches=[];unmatched=[];summaries=[];reference_rows=[];mainshock_by_catalog={};chance_by_catalog={}
    for name,raw in refs.items():
        ref=raw[reference_mask(raw,cfg)].sort_values(['time','reference_id']).reset_index(drop=True)
        expected=cfg['expected_reference_counts'][name]
        assert len(ref)==expected,f'{name}: masked {len(ref)} reference events, expected {expected}'
        located=name in LOCATED
        ref['x_km'],ref['y_km']=proj(ref.longitude.to_numpy(),ref.latitude.to_numpy()) if located else (np.nan,np.nan)
        reference_rows.append(ref[['catalog','reference_id','time','latitude','longitude','depth_km','magnitude','magnitude_type','depth_datum']])
        # The mainshock is identified by its ComCat event id (time-only
        # detections are too dense near the anchor to identify by time).
        mainshock_row=ref[ref.reference_id.eq(anchor_id)]
        gates=cfg['references'][name].get('gates') or (cfg['matching'] if located else cfg['matching']['time_only'])
        for limits in [gates['primary']]+gates['sensitivity']:
            m,u=match_catalog(scoped,ref,*limits);m['catalog']=name
            pairs=m[m.matched];clear=pairs[~pairs.ambiguous]
            summaries.append(dict(catalog=name,gate='primary' if limits==gates['primary'] else f'{limits[0]:g}s_{limits[1]:g}km',
                                  time_gate_s=limits[0],distance_gate_km=limits[1],expert_scope_events=len(scoped),reference_scope_events=len(ref),matched=len(pairs),unambiguous=len(clear),unmatched_reference=len(u),
                                  matched_fraction=len(pairs)/len(ref),
                                  median_gamma_horizontal_km=float(clear.gamma_horizontal_km.median()),median_nll_horizontal_km=float(clear.nll_horizontal_km.median()),
                                  median_gamma_abs_dt_s=float(clear.gamma_dt_s.abs().median()),median_nll_abs_dt_s=float(clear.nll_dt_s.abs().median())))
            if limits==gates['primary']:
                all_matches.append(m);unmatched.append(u);primary_m=m;primary_pairs=pairs;primary_clear=clear
        if not located:
            # Chance coincidences: the same matcher against the reference moved
            # in time; an event population unrelated to the reference by
            # construction, with the same rate history (shift << swarm phases).
            shift=pd.Timedelta(seconds=cfg['matching']['time_only']['control_shift_s'])
            control,_=match_catalog(scoped,ref.assign(time=ref.time+shift),*gates['primary'])
            chance_by_catalog[name]=int(control.matched.sum())
        if len(mainshock_row):
            hit=primary_m[primary_m.matched & primary_m.reference_id.eq(mainshock_row.iloc[0].reference_id)]
            assert len(hit),f'{name}: mainshock {mainshock_row.iloc[0].reference_id} not matched at primary gates'
            mainshock=dict(reference_id=str(mainshock_row.iloc[0].reference_id),matched=True,
                           dt_s=float(hit.nll_dt_s.iloc[0]),horizontal_km=float(hit.nll_horizontal_km.iloc[0]),
                           depth_difference_km=float(hit.nll_depth_difference_km.iloc[0]))
        else:
            mainshock=dict(reference_id=None,matched=False,dt_s=None,horizontal_km=None)
        mainshock_by_catalog[name]=mainshock
        print(name,'masked',len(ref),'matched',len(primary_pairs),'unambiguous',len(primary_clear),
              *(('chance (shifted control)',chance_by_catalog[name]) if name in chance_by_catalog else ()),flush=True)
    matches=pd.concat(all_matches,ignore_index=True)
    matches.to_csv(OUT/'reference_matches.csv',index=False)
    pd.concat(reference_rows).to_csv(OUT/'reference_events.csv',index=False)
    pd.concat(unmatched)[['catalog','reference_id','time','latitude','longitude','depth_km','candidate_count']].to_csv(OUT/'unmatched_reference_events.csv',index=False)
    npicks=pd.read_csv(npath/'picks.csv')
    q=quality(e,npicks,matches,cfg,depth_bounds)
    # v1 working subset, mirroring stage 10's deterministic rule (NLL region,
    # provisionally usable, mainshock excluded).
    anchor_event=set(q.event_id[(q.nll_time-anchor).abs()<=pd.Timedelta(seconds=main_cfg['mainshock']['proximity_s'])])
    q['is_mainshock']=q.event_id.isin(anchor_event)
    q['in_v1_working_catalog']=region(q,cfg)&q.provisional_quality.eq('provisionally_usable')&~q.is_mainshock
    q.to_csv(OUT/'event_quality.csv',index=False)
    v1_ids=set(q.loc[q.in_v1_working_catalog,'event_id'])
    clear=matches[matches.matched&~matches.ambiguous].copy()
    clear['in_v1']=clear.event_id.isin(v1_ids)
    rtime=pd.to_datetime(clear.reference_time,utc=True,format='ISO8601')
    clear['reference_period']=np.where(rtime<anchor,'pre_mainshock',
                                       np.where(rtime<anchor+pd.Timedelta(hours=48),'first_48h','later'))
    clear.to_csv(OUT/'matches.csv',index=False)
    stats=pd.DataFrame(summaries)
    for catalog in CATALOGS:
        sub=clear[clear.catalog.eq(catalog)&clear.in_v1]
        stats.loc[stats.catalog.eq(catalog)&stats.gate.eq('primary'),'matched_fraction_v1']=len(sub)/cfg['expected_reference_counts'][catalog]
    stats.to_csv(OUT/'matching_summary.csv',index=False)
    examples=choose_examples(q,matches,anchor_id,anchor)
    examples=examples.merge(q[['event_id','provisional_quality','status','depth_km','rms_unweighted_s','horizontal_shift_km','unambiguous_reference_count']],on='event_id',validate='one_to_one')
    examples.to_csv(OUT/'examples.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'axes.linewidth':.7})
    refs_all=pd.concat(reference_rows,ignore_index=True)
    figures(matches,stats,q,OUT/'figures')
    locations_figure(q,refs_all,pd.read_csv(gpath/'stations.csv'),main_cfg['mainshock'],OUT/'figures',cfg)
    # Per-period matched fractions with reference-event denominators.
    refs_all['period']=np.where(refs_all.time<anchor,'pre_mainshock',np.where(refs_all.time<anchor+pd.Timedelta(hours=48),'first_48h','later'))
    period_fractions={}
    for c in CATALOGS:
        den=refs_all[refs_all.catalog.eq(c)].groupby('period').size().sort_index()
        num=clear[clear.catalog.eq(c)&clear.in_v1].groupby('reference_period').size().reindex(den.index,fill_value=0)
        period_fractions[c]={str(k):dict(reference_events=int(den[k]),matched_v1=int(num[k]),matched_fraction_v1=float(num[k]/den[k])) for k in den.index}
    primary=stats[stats.gate.eq('primary')].set_index('catalog')
    report=dict(round=main_cfg['round'],gates=cfg['matching'],
                mask=cfg['window']|cfg['region']|{'depth_bounds_km':cfg['depth_bounds_km'],'magnitude_floor':None,
                                                  'time_only_references':'window only'},
                expert_scope_events=len(scoped),v1_working_events=len(v1_ids),
                references={c:dict(masked=int(primary.loc[c,'reference_scope_events']),matched=int(primary.loc[c,'matched']),
                                   unambiguous=int(primary.loc[c,'unambiguous']),
                                   matched_fraction=float(primary.loc[c,'matched_fraction']),
                                   matched_fraction_v1=float(primary.loc[c,'matched_fraction_v1']),
                                   mainshock=mainshock_by_catalog[c],
                                   **({'chance_matches':chance_by_catalog[c],
                                       'matched_fraction_net_of_chance':float((primary.loc[c,'matched']-chance_by_catalog[c])/primary.loc[c,'reference_scope_events'])}
                                      if c in chance_by_catalog else {})) for c in CATALOGS},
                depth_vs_reference={c:(lambda v:dict(n=int(len(v)),median_km=float(v.median()) if len(v) else None,
                                                      mad_km=float((v-v.median()).abs().median()) if len(v) else None))(
                                        clear[clear.catalog.eq(c)].nll_depth_difference_km.dropna()) for c in LOCATED},
                medians={c:dict(gamma_dt_s=float(primary.loc[c,'median_gamma_abs_dt_s']),nll_dt_s=float(primary.loc[c,'median_nll_abs_dt_s']),
                                gamma_horizontal_km=float(primary.loc[c,'median_gamma_horizontal_km']),nll_horizontal_km=float(primary.loc[c,'median_nll_horizontal_km'])) for c in CATALOGS},
                period_matched_fractions=period_fractions,notes=notes)
    (OUT/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    lines=[f'# Round {main_cfg["round"]} reference matching','',
           f'Expert candidates in comparison scope: {len(scoped):,}; v1 working events: {len(v1_ids):,}.','',
           '| Reference | Masked | Matched | Unambiguous | Matched fraction | v1 fraction | median NLL \\|dt\\| (s) | median NLL epicentral (km) |','|---|---|---|---|---|---|---|---|']
    for c in CATALOGS:
        r=report['references'][c];md=report['medians'][c]
        lines.append(f'| {c} | {r["masked"]:,} | {r["matched"]:,} | {r["unambiguous"]:,} | {r["matched_fraction"]:.3f} | {r["matched_fraction_v1"]:.3f} | {md["nll_dt_s"]:.2f} | {md["nll_horizontal_km"]:.2f} |')
    for c,n in chance_by_catalog.items():
        lines.append(f'\n{c}: {n:,} chance matches in the shifted control ({cfg["matching"]["time_only"]["control_shift_s"]} s); matched fraction net of chance {report["references"][c]["matched_fraction_net_of_chance"]:.3f}.')
    for c,d in report['depth_vs_reference'].items():
        if d['n']:lines.append(f'\nNLL depth vs {c} (unambiguous pairs): median {d["median_km"]:+.2f} km, MAD {d["mad_km"]:.2f} km, n {d["n"]:,}.')
    lines+=['','Per-period v1 matched fractions:']
    for c in CATALOGS:
        row='; '.join(f'{k} {v["matched_fraction_v1"]:.3f} ({v["matched_v1"]}/{v["reference_events"]})' for k,v in report['period_matched_fractions'][c].items())
        lines.append(f'- {c}: {row}')
    lines+=['',f'Mainshock (ComCat {anchor_id}) matched: {report["references"]["comcat"]["mainshock"]["matched"]}.' if anchor_id
            else 'No in-window mainshock for this task (config mainshock.in_window false); no identity check.']
    (OUT/'summary.md').write_text('\n'.join(lines)+'\n')
    paths=[(case_root/spec['path']).resolve() for spec in cfg['references'].values()]+[gpath/'events.csv',gpath/'picks.csv',gpath/'stations.csv',HERE/main_cfg['export_root']/'01_prepare_inputs/full/waveform_inputs.csv',epath,npath/'picks.csv',HERE/'00_config/validation.yaml',HERE/'00_config/association.yaml',HERE/'00_config/config.yaml',Path(__file__)]
    record={'round':main_cfg['round'],'settings':cfg,'association':settings,
            'inputs':[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
            'events':len(q),'comparison_scope_events':len(scoped),'v1_working_events':len(v1_ids),
            'quality_counts':{str(k):int(v) for k,v in q.provisional_quality.value_counts().to_dict().items()},'report':report}
    (OUT/'run.yaml').write_text(yaml.safe_dump(record,sort_keys=False))
    print(json.dumps(report['references'],indent=2),flush=True)


if __name__=='__main__':main()
