#!/usr/bin/env python3
"""Plot the initial GaMMA catalog and association diagnostics, without altering results."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
BLUE, ORANGE, BLACK = '#0072B2', '#D55E00', '#252525'


def save(fig, out, name):
    fig.savefig(out / f'{name}.png', dpi=240)
    fig.savefig(out / f'{name}.pdf', dpi=300)
    plt.close(fig)


def letter(ax, label):
    ax.text(-0.10, 1.03, label, transform=ax.transAxes, fontsize=11, weight='bold')


def time_axis(ax):
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.set_xlabel('Time (UTC)')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, default=HERE / 'export/03_associate_gamma/full')
    args = ap.parse_args()
    source = args.input.resolve()
    out = source / 'figures'
    out.mkdir(exist_ok=True)
    e = pd.read_csv(source / 'events.csv', keep_default_na=False)
    p = pd.read_csv(source / 'picks.csv', keep_default_na=False)
    s = pd.read_csv(source / 'stations.csv')
    e['time'] = pd.to_datetime(e.origin_time, utc=True, format="ISO8601")
    p['time'] = pd.to_datetime(p.time_utc, utc=True, format="ISO8601")
    assigned = p.association_status.eq('associated')
    p['residual_s'] = pd.to_numeric(p.residual_s, errors='coerce')
    bound = e.quality_flags.str.contains('near_depth_bound')
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8,
                         'axes.titlesize': 9, 'axes.labelsize': 8,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'axes.linewidth': .7, 'xtick.direction': 'out', 'ytick.direction': 'out',
                         'pdf.fonttype': 42, 'savefig.facecolor': 'white'})

    # Show every event; profiles are whole-region projections, not narrow sections.
    fig, axes = plt.subplots(2,3,figsize=(10,6.4),layout='constrained')
    ax=axes[0,0]
    sc=ax.scatter(e.longitude,e.latitude,c=e.depth_km,s=3,cmap='viridis',vmin=0,vmax=25,
                  alpha=.65,linewidths=0,rasterized=True)
    ax.plot([-117.9,-117.2,-117.2,-117.9,-117.9],[35.45,35.45,36.05,36.05,35.45],color=BLACK,lw=.8,ls='--')
    lonlim=(min(-118.15,e.longitude.min()-.01),max(-116.95,e.longitude.max()+.01))
    latlim=(min(35.2,e.latitude.min()-.01),max(36.3,e.latitude.max()+.01))
    nearby=s[s.longitude.between(*lonlim)&s.latitude.between(*latlim)]
    ax.scatter(nearby.longitude,nearby.latitude,marker='^',s=18,facecolors='white',edgecolors=BLACK,linewidths=.6)
    ax.set(xlim=lonlim,ylim=latlim,xlabel='Longitude (°)',ylabel='Latitude (°)')
    ax.set_aspect(1/np.cos(np.deg2rad(35.75)))
    ax.xaxis.set_major_locator(plt.MaxNLocator(4))
    fig.colorbar(sc,ax=ax,label='Depth (km)',fraction=.045,pad=.025)
    for column,x,label in [(1,'longitude','Longitude (°)'),(2,'latitude','Latitude (°)')]:
        ax=axes[0,column]
        ax.scatter(e.loc[~bound,x],e.loc[~bound,'depth_km'],s=2,c=BLACK,alpha=.25,linewidths=0,rasterized=True)
        ax.scatter(e.loc[bound,x],e.loc[bound,'depth_km'],s=3,c=ORANGE,alpha=.45,linewidths=0,rasterized=True)
        ax.set(xlabel=label,ylabel='Depth (km)',ylim=(25,0))
    ax=axes[1,0]
    ax.hist([e.loc[~bound,'depth_km'],e.loc[bound,'depth_km']],bins=np.arange(0,25.5,.5),
            stacked=True,color=[BLUE,ORANGE],label=['Interior','Near depth bound'])
    ax.set(xlabel='Depth (km)',ylabel='Events',xlim=(0,25));ax.legend(frameon=False,fontsize=7)
    ax=axes[1,1]
    ax.scatter(e.time,e.depth_km,s=2,c=np.where(bound,ORANGE,BLACK),alpha=.3,linewidths=0,rasterized=True)
    ax.set(ylim=(25,0),ylabel='Depth (km)');time_axis(ax)
    ax=axes[1,2]
    ordered=e.sort_values('time')
    ax.step(ordered.time,np.arange(1,len(ordered)+1),where='post',color=BLACK,lw=1)
    ax.set(ylabel='Cumulative events');time_axis(ax)
    for ax,label in zip(axes.flat,'abcdef'):letter(ax,label)
    save(fig,out,'01_catalog_distribution')

    fig, axes = plt.subplots(2,3,figsize=(10,6),layout='constrained')
    hours = pd.date_range('2019-07-04','2019-07-07',freq='h',tz='UTC')
    ec = e.set_index('time').resample('h').size().reindex(hours[:-1],fill_value=0)
    total = p.set_index('time').resample('h').size().reindex(hours[:-1],fill_value=0)
    used = p.loc[assigned].set_index('time').resample('h').size().reindex(hours[:-1],fill_value=0)
    ax = axes[0,0];ax.step(ec.index,ec.values,where='post',color=BLACK,lw=1)
    ax.set(ylabel='Events per hour');time_axis(ax)
    ax = axes[0,1];ax.step(total.index,total.values,where='post',color=BLACK,label='All picks',lw=1)
    ax.step(used.index,used.values,where='post',color=BLUE,label='Associated',lw=1)
    ax.set(ylabel='Picks per hour');time_axis(ax);ax.legend(frameon=False)
    ax = axes[0,2];ax.hist(e.rms_residual_s,bins=np.arange(0,1.55,.05),color=BLUE)
    ax.axvline(e.rms_residual_s.median(),color=ORANGE,lw=1,ls='--');ax.set(xlabel='Event RMS residual (s)',ylabel='Events')
    ax = axes[1,0]
    for phase,color in [('P',BLUE),('S',ORANGE)]:
        ax.hist(p.loc[assigned & p.phase.eq(phase),'residual_s'],bins=np.linspace(-1.51,1.51,62),
                density=True,histtype='step',color=color,label=phase,lw=1)
    ax.axvline(0,color=BLACK,lw=.6);ax.set(xlabel='Observed − predicted arrival (s)',ylabel='Density');ax.legend(frameon=False)
    ax = axes[1,1];ax.hist(e.n_stations,bins=np.arange(5.5,38.5),color=BLUE)
    ax.set(xlabel='Stations per event',ylabel='Events')
    ax = axes[1,2];ax.hist(e.azimuth_gap_deg,bins=np.arange(0,361,10),color=BLUE)
    ax.axvline(180,color=ORANGE,ls='--',lw=1);ax.set(xlabel='Maximum azimuth gap (°)',ylabel='Events',xlim=(0,360))
    for ax,l in zip(axes.flat,'abcdef'):letter(ax,l)
    save(fig,out,'02_association_diagnostics')

    # Deterministic illustrative examples; no claim that these establish pick accuracy.
    well = e[(~bound) & (e.azimuth_gap_deg<180) & (e.n_stations>=15)]
    boundary = e[(e.depth_km<.5) & (e.n_stations>=15)]
    wide = e[e.azimuth_gap_deg>180]
    examples=[]
    for label, group in [('Interior',well),('Shallow bound',boundary),('Wide azimuth gap',wide)]:
        if group.empty:continue
        chosen=group.assign(delta=(group.rms_residual_s-group.rms_residual_s.median()).abs()).sort_values(['delta','event_id']).iloc[0]
        examples.append((label,chosen))
    fig, axes = plt.subplots(len(examples),2,figsize=(9,2.4*len(examples)),layout='constrained',squeeze=False)
    selections=[]
    for i,(label,event) in enumerate(examples):
        q=p[p.event_id.eq(event.event_id)].merge(s,left_on='instrument_id',right_on='id',validate='many_to_one')
        distance=np.hypot(q['x(km)']-event.x_km,q['y(km)']-event.y_km)
        relative=(q.time-event.time).dt.total_seconds()
        ax=axes[i,0]
        for phase,color in [('P',BLUE),('S',ORANGE)]:
            mask=q.phase.eq(phase)
            ax.scatter(distance[mask],relative[mask],s=16,facecolors='none',edgecolors=color,linewidths=.8,label=phase)
            ax.scatter(distance[mask],(relative-q.residual_s)[mask],s=16,marker='x',c=color,linewidths=.7)
        ax.set(xlabel='Epicentral distance (km)',ylabel='Time after origin (s)',title=f'{label}: {event.event_id}')
        ax.legend(handles=[Line2D([],[],color=BLUE,marker='o',mfc='none',ls='',label='P'),
                           Line2D([],[],color=ORANGE,marker='o',mfc='none',ls='',label='S'),
                           Line2D([],[],color=BLACK,marker='o',mfc='none',ls='',label='Observed'),
                           Line2D([],[],color=BLACK,marker='x',ls='',label='Predicted')],frameon=False,ncol=2,fontsize=7)
        ax=axes[i,1]
        ax.scatter(s['x(km)']-event.x_km,s['y(km)']-event.y_km,s=15,marker='^',facecolors='none',edgecolors='#777777',linewidths=.6)
        used_st=q.drop_duplicates('instrument_id')
        ax.scatter(used_st['x(km)']-event.x_km,used_st['y(km)']-event.y_km,s=22,marker='^',c=BLUE)
        ax.scatter([0],[0],marker='*',s=75,c=ORANGE,zorder=4)
        ax.set(xlabel='East of event (km)',ylabel='North of event (km)',aspect='equal')
        for j in range(2):letter(axes[i,j],'abcdef'[2*i+j])
        selections.append(dict(example=label,event_id=event.event_id,origin_time=event.origin_time,depth_km=event.depth_km,
                               rms_residual_s=event.rms_residual_s,n_stations=event.n_stations,azimuth_gap_deg=event.azimuth_gap_deg))
    pd.DataFrame(selections).to_csv(out/'example_events.csv',index=False)
    save(fig,out,'03_event_moveout_examples')

    shallow=int((e.depth_km<.5).sum());deep=int((e.depth_km>24.5).sum())
    fraction=100*assigned.mean()
    text=f'''# Initial GaMMA catalog diagnostics

Generated by `04_comparison/03_plot_association.py` from the completed association CSVs. No catalog, phase assignments or raw observations are changed. These figures evaluate internal consistency and geometry; no reference catalog or independent waveform validation is used.

## Coverage and interpretation

- `01_catalog_distribution.png/pdf`: all {len(e):,} events, with no event subsampling. Panel a uses depth colors; the dashed rectangle is the planned core region. Triangles show only stations inside the displayed map; the full association uses all 37 stations. Panels b/c are whole-region longitude/depth and latitude/depth projections, not narrow fault cross sections. Orange marks depth-bound events. All depth axes use the adopted 0.7-km-above-sea-level reference surface, not sea level or local ground level.
- `02_association_diagnostics.png/pdf`: all events and all {len(p):,} picks. Counts use one-hour UTC bins. Residual distributions contain associated picks only and are conditioned on the association residual cutoff of 1.5 s; positive residual means observed arrival is later than the model. Dashed lines mark median event RMS and the 180-degree gap threshold. Association fraction is not detection completeness or precision.
- `03_event_moveout_examples.png/pdf`: three selected illustrations, not the full catalog. Within interior / shallow-bound / wide-gap groups, choose the event nearest its group's median RMS, breaking ties by event ID; the first two groups require at least 15 stations. Circles show observed picks and crosses the model predictions reconstructed as observed minus stored residual. Thus these are fit diagnostics, not independent validation. Station maps show all 37 stations (open triangles), contributing stations (blue) and the event (star). Exact selections and metrics are in `example_events.csv`.

## Main findings

Associated: {assigned.sum():,}/{len(p):,} picks ({fraction:.1f}%). Median event RMS: {e.rms_residual_s.median():.3f} s. Median contributing stations: {e.n_stations.median():.0f}.

{shallow:,} events ({100*shallow/len(e):.1f}%) lie shallower than 0.5 km below the adopted reference; {deep:,} lie deeper than 24.5 km. A concentration at a search boundary cannot be interpreted directly as a physical shallow layer. Small fitting residuals alone do not establish correct event grouping or accurate depth. {int((e.azimuth_gap_deg>180).sum()):,} events have azimuth gaps above 180 degrees; {int(e.quality_flags.str.contains('outside_core_region').sum()):,} lie outside the core region. Flags can overlap.

Next: absolute-location refinement with explicit velocity/depth conventions, then waveform-level checks and independent catalog comparison. Preserve the existing initial catalog as a separate baseline.
'''
    (out/'README.md').write_text(text)
    print(text.split('## Main findings')[1])
    print(f'Figures: {out}')


if __name__=='__main__':main()
