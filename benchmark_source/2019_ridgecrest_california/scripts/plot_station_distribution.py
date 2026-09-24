#!/usr/bin/env python3
"""Plot verified Ridgecrest station selections and later temporary deployments."""
import json
from pathlib import Path
import hashlib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
import numpy as np

from plot_catalog_comparison import publication_style, save_figure, WIDTH_INCHES

CASE = Path(__file__).resolve().parents[1]
ZOOM = (-118.04, -117.12, 35.36, 36.34)
COLORS = {'shared': '#0072B2', 'liu_only': '#D55E00', 'later': '#8B4C9D'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    epochs_path = CASE/'data/waveforms/stations/channel_epochs.json'
    report_path = CASE/'analysis/station_preparation.json'
    audit_path = CASE/'analysis/reference_audit.json'
    report = json.loads(report_path.read_text())
    assert sha(epochs_path) == report['artifacts'][str(epochs_path.relative_to(CASE))]['sha256']
    epochs = json.loads(epochs_path.read_text())
    anchors = json.loads(audit_path.read_text())['anchors']
    shared = set(report['shelly_auxiliary']['arrival_window_station_ids'])
    active = set(report['liu']['metadata_present_in_candidate'])
    stations = []
    for name in report['liu']['paper_stations']:
        rows = [r for r in epochs if r['network']+'.'+r['station']==name]
        if name in active:
            rows = [r for r in rows if r['candidate_overlap_seconds']>0]
        positions = sorted({(r['longitude'], r['latitude']) for r in rows})
        if not positions:
            raise ValueError(f'No coordinate evidence: {name}')
        xy = np.median(positions, axis=0)
        stations.append(dict(id=name, longitude=float(xy[0]), latitude=float(xy[1]),
                             coordinate_variants=positions,
                             category='shared' if name in shared else ('liu_only' if name in active else 'later')))
    counts = {k: sum(r['category']==k for r in stations) for k in COLORS}
    assert counts == {'shared':24, 'liu_only':17, 'later':4}
    with publication_style():
        fig, axes = plt.subplots(1, 2, figsize=(WIDTH_INCHES, 4.7),
                                 gridspec_kw={'left':.085,'right':.98,'bottom':.22,'top':.92,'wspace':.27})
        for i, ax in enumerate(axes):
            if i == 0:
                ax.set_xlim(-118.95,-116.25); ax.set_ylim(34.65,36.75)
                ax.set_xticks([-118.8,-118,-117.2,-116.4]); ax.set_yticks([35,35.5,36,36.5])
            else:
                ax.set_xlim(ZOOM[:2]); ax.set_ylim(ZOOM[2:])
                ax.set_xticks([-117.9,-117.6,-117.3]); ax.set_yticks([35.5,35.75,36,36.25])
            ax.set_aspect(1/np.cos(np.deg2rad(35.77)))
            ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{abs(x):.1f}'))
            ax.set_xlabel('Longitude (°W)'); ax.set_ylabel('Latitude (°N)')
            ax.grid(color='#e8e8e8', lw=.45, zorder=0)
            for edge in ('top','right'): ax.spines[edge].set_visible(True)
            ax.set_title(('a  Selected stations','b  Sequence area')[i],loc='left',pad=10,fontsize=9)
            for station in stations:
                x,y=station['longitude'],station['latitude'];kind=station['category']
                if not (ax.get_xlim()[0] <= x <= ax.get_xlim()[1] and ax.get_ylim()[0] <= y <= ax.get_ylim()[1]):
                    continue
                ax.scatter(x,y,s=26 if i else 21,marker='D' if kind=='later' else '^',
                           facecolors='white' if kind=='later' else COLORS[kind],edgecolors=COLORS[kind],linewidths=.85,zorder=3)
                inside = ZOOM[0]<=x<=ZOOM[1] and ZOOM[2]<=y<=ZOOM[3]
                if i or not inside:
                    offsets={'CI.JRC2':(4,1),'CI.WVP2':(-3,-8),'CI.WRC2':(-3,-8),
                             'PB.B918':(4,-7),'CI.WOR':(6,1),'CI.WHF':(-5,-10),'CI.WAS2':(4,10),'CI.ISA':(4,-12),
                             'CI.LMR2':(-3,5),'CI.HYS':(4,-6),'CI.APL':(-3,5),
                             'CI.CLC':(4,4),'CI.WRV2':(-3,8)}
                    dx,dy=offsets.get(station['id'],(4,3))
                    ax.annotate(station['id'],(x,y),xytext=(dx,dy),textcoords='offset points',
                                fontsize=5.2 if i else 5.5,ha='right' if dx<0 else 'left',zorder=4)
            for key, a in anchors.items():
                ax.scatter(a['longitude'],a['latitude'],marker='*',s=78,c='#F0C94E',edgecolors='#222222',lw=.7,zorder=5)
                if i:
                    ax.annotate(f'Mw {a["magnitude"]:.1f}',(a['longitude'],a['latitude']),
                                xytext=(7,0) if key=='mw6_4' else (-7,-9),textcoords='offset points',
                                ha='left' if key=='mw6_4' else 'right',fontsize=6,zorder=6)
        axes[0].add_patch(Rectangle((ZOOM[0],ZOOM[2]),ZOOM[1]-ZOOM[0],ZOOM[3]-ZOOM[2],
                                    fill=False,ec='#444444',lw=.8,ls='--'))
        # Local geographical approximation, not a projected basemap.
        for ax,km in zip(axes,[40,10]):
            x0,x1=ax.get_xlim();y0,y1=ax.get_ylim();x=x0+.07*(x1-x0);y=y0+.055*(y1-y0)
            length=km/(111.195*np.cos(np.deg2rad(y)))
            ax.plot([x,x+length],[y,y],color='black',lw=1.5)
            ax.text(x+length/2,y+.025*(y1-y0),f'{km} km',ha='center',fontsize=6)
        handles=[Line2D([],[],marker='^',color=COLORS['shared'],ls='',label='Liu + Shelly auxiliary (24)'),
                 Line2D([],[],marker='^',color=COLORS['liu_only'],ls='',label='Liu only in verified lists (17)'),
                 Line2D([],[],marker='D',mfc='white',mec=COLORS['later'],ls='',label='Later temporary stations (4)'),
                 Line2D([],[],marker='*',mfc='#F0C94E',mec='#222222',ls='',markersize=9,label='Mw 6.4 / Mw 7.1')]
        fig.legend(handles=handles,ncol=2,loc='lower center',bbox_to_anchor=(.52,.025),frameon=False,fontsize=7,
                   columnspacing=2.0,labelspacing=.9)
        out=CASE/'analysis/figures/station_infomation/station_distribution'
        save_figure(fig,out);plt.close(fig)
    manifest=dict(inputs={str(p.relative_to(CASE)):sha(p) for p in [epochs_path,report_path,audit_path]},
                  script_sha256=sha(Path(__file__)),style_script_sha256=sha(Path(__file__).with_name('plot_catalog_comparison.py')),
                  counts=counts,stations=stations,
                  semantics='Metadata selections, not waveform coverage or exact paper channel selection. AWR/Ross station lists unresolved and not plotted. Later stations lie outside the candidate 72 hours.',
                  coordinate_policy='Median of unique channel horizontal coordinates for each station; only candidate-overlapping epochs used for active stations, discovery epochs for later stations. CI.FUR has two latitudes differing by about 18 m.',
                  outputs={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in [out.with_suffix('.png'),out.with_suffix('.pdf')]})
    out.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(counts)


if __name__=='__main__':main()
