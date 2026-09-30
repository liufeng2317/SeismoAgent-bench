#!/usr/bin/env python3
"""Reproduce three source-comparison figures without downloads or waveform inputs."""
import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from SeismoAgentBench.utils.source_prepare.catalog import sha256, utc, within
from SeismoAgentBench.utils.source_prepare.sources import load_case, select_subset
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'catalogs'))
from audit_references import read_events

CASE = Path(__file__).resolve().parents[2]
SPECS = [
    ('shelly', 'shelly', 'Shelly', '#0072B2'),
    ('liu', 'liu', 'Liu', '#D55E00'),
    ('ross_relocated', 'ross', 'Ross relocated', '#009E73'),
    ('awr_hypocenters', 'awr_hypocenters', 'AWR v2', '#CC79A7'),
    ('official_earthquake', 'official_snapshot', 'Official earthquakes', '#34383C'),
]
SHORT = ['Shelly', 'Liu', 'Ross rel.', 'AWR v2', 'Official']


# Layout and export choices for these Ridgecrest figures.
WIDTH_INCHES = 180 / 25.4


def publication_style():
    return matplotlib.rc_context({
        'font.family': 'DejaVu Sans', 'font.size': 7.5, 'axes.titlesize': 8,
        'axes.labelsize': 7.5, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
        'legend.fontsize': 6.5, 'axes.linewidth': .65,
        'lines.linewidth': 1.1, 'xtick.major.width': .6, 'ytick.major.width': .6,
        'xtick.major.size': 2.8, 'ytick.major.size': 2.8,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.unicode_minus': True, 'pdf.fonttype': 42, 'ps.fonttype': 42,
        'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    })


def panel_label(ax, letter, title):
    ax.set_title(title, loc='left', pad=9, fontweight='normal')
    ax.text(-.14, 1.065, letter, transform=ax.transAxes,
            fontsize=10, fontweight='bold', va='bottom', ha='left')


def save_figure(fig, stem):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix('.png'), dpi=320, pil_kwargs={'optimize': True})
    fig.savefig(stem.with_suffix('.pdf'), dpi=450,
                metadata={'Creator': 'SeismoAgentBench', 'CreationDate': None, 'ModDate': None})


def load_data(case):
    cfg = load_case(case)
    audit_path = case/'analysis/reference_audit.json'
    audit = json.loads(audit_path.read_text())
    if audit['config_sha256'] != sha256(case/'analysis/processing.yaml'):
        raise ValueError('Reference audit is stale; rerun audit_references.py first')
    window = cfg['scientific_design']['candidate_window']
    start, end = utc(window['start_utc']), utc(window['end_utc'])
    if start != utc('2019-07-04T00:00:00Z') or end != utc('2019-07-07T00:00:00Z'):
        raise ValueError('These case figures use 4–7 July 2019; update time axes for a new window')
    data = []; inputs = {}
    for key, source, label, color in SPECS:
        spec = cfg['sources'][source]; path = case/spec['path']
        checksum = sha256(path)
        if checksum != spec['expected_sha256'] or checksum != audit['sources'][source]['sha256']:
            raise ValueError(f'Source hash mismatch: {source}')
        rows, errors = read_events(path, spec['parser'])
        if errors:
            raise ValueError(f'Invalid source rows: {source}')
        rows = [r for r in rows if within(r,start,end,window['native_comparison_bounds'])]
        if key in cfg['reference_audit']['subsets']:
            rows = select_subset(rows,cfg['reference_audit']['subsets'][key])
        # Every plotted population must reproduce the existing five-stage audit.
        expected = sum(stage['native_mask_rows'][key] for stage in audit['stages'])
        if len(rows) != expected:
            raise ValueError(f'Count differs from reference audit: {key}')
        rows.sort(key=lambda r:r['time'])
        record = {'key':key,'label':label,'color':color,'rows':rows}
        for field in ('latitude','longitude','depth_km','magnitude'):
            record[field] = np.array([r[field] if r[field] is not None else np.nan for r in rows])
        record['hour'] = np.array([(r['time']-start).total_seconds()/3600 for r in rows])
        data.append(record)
        inputs[source] = {'path':spec['path'],'sha256':checksum,'plotted_records':len(rows),'selection':key}
    return cfg, audit, data, inputs


def map_axes(ax, bounds):
    ax.set_xlim(bounds['longitude']); ax.set_ylim(bounds['latitude'])
    ax.set_aspect(1/np.cos(np.deg2rad(np.mean(bounds['latitude']))))
    ax.set_xticks([-117.8,-117.5,-117.2]); ax.set_yticks([35.5,35.75,36.0])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{abs(x):.1f}'))
    ax.set_xlabel('Longitude (°W)'); ax.set_ylabel('Latitude (°N)')
    ax.grid(color='#e8e8e8',lw=.45,zorder=0); ax.set_axisbelow(True)
    for name in ('top','right'):ax.spines[name].set_visible(True)


def stars(ax, audit, annotate=False):
    for key in ('mw6_4','mw7_1'):
        row = audit['anchors'][key]; x,y = row['longitude'],row['latitude']
        ax.scatter(x,y,s=75 if annotate else 42,marker='*',c='#F0C94E',edgecolors='#222222',linewidths=.6,zorder=5)
        if annotate:
            dx,dy = ((.12,-.09) if key=='mw6_4' else (-.14,.095))
            ax.annotate(f'Mw {row["magnitude"]:.1f}',(x,y),xytext=(x+dx,y+dy),
                        ha='left' if dx>0 else 'right',fontsize=7.5,
                        arrowprops={'arrowstyle':'-','lw':.6,'color':'#333333'},
                        bbox={'fc':'white','ec':'none','alpha':.9,'pad':1.2},zorder=6)


def overview(out, cfg, audit, data):
    bounds = cfg['scientific_design']['candidate_window']['native_comparison_bounds']
    fig = plt.figure(figsize=(WIDTH_INCHES,4.5))
    grid = fig.add_gridspec(2,2,width_ratios=[1.15,1],left=.085,right=.97,bottom=.22,top=.93,wspace=.32,hspace=.55)
    axmap = fig.add_subplot(grid[:,0]); axtime = fig.add_subplot(grid[0,1]); axdepth = fig.add_subplot(grid[1,1])
    reference = data[0]; norm = Normalize(0,72)
    points = axmap.scatter(reference['longitude'],reference['latitude'],c=reference['hour'],norm=norm,cmap='cividis',s=1.5,linewidths=0,rasterized=True)
    map_axes(axmap,bounds); stars(axmap,audit,True)
    panel_label(axmap,'a',f'Shelly reference · {len(reference["rows"]):,} events')
    x=-117.84; y=35.495; length=10/(111.195*np.cos(np.deg2rad(y)))
    axmap.plot([x,x+length],[y,y],color='#222222',lw=1.8)
    axmap.text(x+length/2,y+.016,'10 km',ha='center',fontsize=6.5)
    axmap.annotate('N',xy=(.93,.92),xytext=(.93,.80),xycoords='axes fraction',ha='center',fontsize=7,
                   arrowprops={'arrowstyle':'-|>','lw':.8,'color':'#333333'})
    for record in data:
        counts, edges = np.histogram(record['hour'],bins=np.arange(73))
        axtime.stairs(counts,edges,color=record['color'],label=record['label'],lw=.95)
    start = utc(cfg['scientific_design']['candidate_window']['start_utc'])
    for key in ('mw6_4','mw7_1'):
        hour=(utc(audit['anchors'][key]['time'])-start).total_seconds()/3600
        axtime.axvline(hour,color='#999999',lw=.7,ls='--',zorder=0)
        axtime.text(hour+.7,.97,f'Mw {audit["anchors"][key]["magnitude"]:.1f}',transform=axtime.get_xaxis_transform(),fontsize=6,va='top')
    axtime.set_xlim(0,72);axtime.set_yscale('symlog',linthresh=1);axtime.set_ylim(0,1200)
    axtime.set_yticks([0,10,100,1000],labels=['0','10','100','1,000'])
    axtime.set_xticks([0,24,48,72],labels=['4 Jul','5 Jul','6 Jul','7 Jul'])
    axtime.set_ylabel('Events per hour');axtime.set_xlabel('2019 (UTC)')
    panel_label(axtime,'b','Recorded event rate')
    axtime.legend(ncol=2,frameon=False,fontsize=5.3,loc='lower right',columnspacing=.9,handlelength=1.6)
    axdepth.scatter(reference['longitude'],reference['depth_km'],c=reference['hour'],norm=norm,cmap='cividis',s=1.0,linewidths=0,rasterized=True)
    axdepth.set_xlim(bounds['longitude']);axdepth.set_ylim(20,0)
    axdepth.set_xticks([-117.8,-117.5,-117.2],labels=['117.8','117.5','117.2']);axdepth.set_yticks([0,10,20])
    axdepth.set_xlabel('Longitude (°W)');axdepth.set_ylabel('Native depth (km)')
    panel_label(axdepth,'c','Shelly depth projection')
    cax=fig.add_axes([.095,.085,.40,.017]);bar=fig.colorbar(points,cax=cax,orientation='horizontal',ticks=[0,24,48,72])
    bar.ax.set_xticklabels(['4 Jul','5 Jul','6 Jul','7 Jul']);bar.set_label('Origin time · 2019 (UTC)',labelpad=3)
    save_figure(fig,out/'01_sequence_overview');plt.close(fig)


def spatial(out, cfg, audit, data):
    fig = plt.figure(figsize=(WIDTH_INCHES,5.9))
    grid=fig.add_gridspec(2,3,left=.085,right=.975,bottom=.20,top=.93,wspace=.30,hspace=.38)
    bounds=cfg['scientific_design']['candidate_window']['native_comparison_bounds']
    for i,record in enumerate(data):
        ax=fig.add_subplot(grid[i//3,i%3])
        scatter=ax.scatter(record['longitude'],record['latitude'],c=record['depth_km'],norm=Normalize(0,20),cmap='viridis_r',s=1.0,linewidths=0,rasterized=True)
        map_axes(ax,bounds);stars(ax,audit)
        if i%3:ax.set_ylabel('')
        panel_label(ax,chr(97+i),record['label'])
        ax.text(.96,.04,f'n = {len(record["rows"]):,}',transform=ax.transAxes,ha='right',fontsize=7,bbox={'fc':'white','ec':'none','alpha':.9,'pad':1.2})
    ax=fig.add_subplot(grid[1,2]);y=np.arange(5)
    ax.barh(y,[len(r['rows']) for r in data],color=[r['color'] for r in data],height=.58)
    ax.set_yticks(y,labels=SHORT);ax.invert_yaxis();ax.set_xlim(0,10000)
    ax.set_xticks([0,4000,8000],labels=['0','4,000','8,000']);ax.set_xlabel('Selected catalog records')
    for i,record in enumerate(data):ax.text(len(record['rows'])+170,i,f'{len(record["rows"]):,}',va='center',fontsize=6.5)
    panel_label(ax,'f','Population size')
    cax=fig.add_axes([.09,.075,.51,.017]);bar=fig.colorbar(scatter,cax=cax,orientation='horizontal',ticks=[0,5,10,15,20]);bar.set_label('Native depth (km)',labelpad=3)
    save_figure(fig,out/'02_catalog_spatial_comparison');plt.close(fig)


def diagnostics(out, cfg, audit, data):
    fig=plt.figure(figsize=(WIDTH_INCHES,5.65))
    grid=fig.add_gridspec(2,2,left=.14,right=.96,bottom=.20,top=.93,wspace=.54,hspace=.52)
    amag=fig.add_subplot(grid[0,0]);adepth=fig.add_subplot(grid[0,1]);arate=fig.add_subplot(grid[1,0]);amatch=fig.add_subplot(grid[1,1])
    for r in data:
        magnitude=np.sort(r['magnitude'][np.isfinite(r['magnitude'])])
        values,first=np.unique(magnitude,return_index=True)
        amag.step(values,(len(magnitude)-first)/len(magnitude),where='pre',color=r['color'],label=r['label'])
        depths=np.sort(r['depth_km']);adepth.step(depths,np.arange(1,len(depths)+1)/len(depths),where='post',color=r['color'])
    amag.set_yscale('log');amag.set_ylim(1e-4,1.1);amag.set_xlim(-1,7.3)
    amag.set_xlabel('Native magnitude');amag.set_ylabel('Fraction with magnitude ≥ M')
    amag.legend(frameon=False,fontsize=6,loc='upper right',handlelength=1.8,labelspacing=.30)
    adepth.set_xlim(0,20);adepth.set_ylim(0,1);adepth.set_xlabel('Native depth (km)');adepth.set_ylabel('Cumulative fraction')
    panel_label(amag,'a','Magnitude populations');panel_label(adepth,'b','Depth distributions')
    rates=np.array([[stage['native_mask_rows'][r['key']]/stage['hours'] for r in data] for stage in audit['stages']])
    im=arate.imshow(rates,cmap='YlGnBu',norm=LogNorm(vmin=1,vmax=300),aspect='auto')
    arate.set_xticks(range(5),labels=SHORT,rotation=35,ha='right')
    arate.set_yticks(range(5),labels=['Before\nMw 6.4','Mw 6.4\nfirst hour','Between,\nlater','Mw 7.1\nfirst hour','After 7.1,\nlater'])
    arate.tick_params(length=0)
    for i in range(5):
        for j in range(5):arate.text(j,i,f'{rates[i,j]:.1f}',ha='center',va='center',fontsize=6.2,color='white' if rates[i,j]>45 else '#1c2e41')
    panel_label(arate,'c','Stage-specific rate (events h⁻¹)')
    pos=arate.get_position();cax=fig.add_axes([pos.x0,pos.y0-.115,pos.width,.013]);bar=fig.colorbar(im,cax=cax,orientation='horizontal',ticks=[1,10,100,300]);bar.ax.set_xticklabels(['1','10','100','300']);bar.ax.minorticks_off()
    pairs=[d for d in audit['reference_overlap_diagnostics'] if d['time_tolerance_s']==1 and d['horizontal_tolerance_km']==5]
    labels=['Shelly–Liu','Shelly–Ross rel.','Shelly–Official','Liu–Official']
    for i,d in enumerate(pairs):
        q=d['horizontal_difference_km'];amatch.plot([q['p50'],q['p90']],[i,i],color='#8996a3',lw=1.3)
        amatch.plot(q['p50'],i,'o',color='#245775',ms=4)
        amatch.plot(q['p90'],i,'D',mfc='white',mec='#245775',ms=4)
    amatch.set_yticks(range(4),labels=[f'{label}\nn = {d["reciprocal_unique_pairs"]:,}' for label,d in zip(labels,pairs)],fontsize=6.2)
    amatch.set_ylim(3.6,-.9);amatch.set_xlim(0,1.35);amatch.set_xlabel('Horizontal reference difference (km)')
    amatch.legend(handles=[Line2D([],[],marker='o',color='#245775',ls='',ms=4,label='Median'),Line2D([],[],marker='D',mfc='white',mec='#245775',ls='',ms=4,label='90th percentile')],frameon=False,fontsize=6,loc='upper left',bbox_to_anchor=(-.01,1.02))
    panel_label(amatch,'d','Unambiguous event correspondence')
    save_figure(fig,out/'03_catalog_population_diagnostics');plt.close(fig)
    return rates


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case-dir',type=Path,default=CASE)
    args=parser.parse_args();case=args.case_dir.resolve()
    cfg,audit,data,inputs=load_data(case)
    out=case/'analysis/figures/catalog_comparison'
    with publication_style():
        overview(out,cfg,audit,data)
        spatial(out,cfg,audit,data)
        rates=diagnostics(out,cfg,audit,data)
    report={'case_id':cfg['case_id'],'config_sha256':sha256(case/'analysis/processing.yaml'),
            'audit_sha256':sha256(case/'analysis/reference_audit.json'),
            'script_sha256':sha256(Path(__file__)),
            'versions':{'matplotlib':matplotlib.__version__,'numpy':np.__version__},
            'inputs':inputs,'selection':cfg['scientific_design']['candidate_window'],
            'stage_rates_per_hour':{stage['stage']:{r['key']:float(rates[i,j]) for j,r in enumerate(data)} for i,stage in enumerate(audit['stages'])},
            'output_policy':{'width_mm':180,'png_dpi':320,'pdf_raster_dpi':450,'pdf_text':'embedded TrueType','point_sampling':'none'},
            'figures':{p.name:{'sha256':sha256(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.suffix in ('.png','.pdf')}}
    (out/'figure_manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({r['label']:len(r['rows']) for r in data},ensure_ascii=False))
    print('Figures:',out)


if __name__=='__main__':main()
