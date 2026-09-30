"""Render current catalog figures/report labels; read-only scientific tables.

The original comparison/export script remains frozen. This presentation entry
point writes figures and report display labels, using the same saved populations and plotting rules.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'export/06_full_catalog/52_full_catalog'
FIG=OUT/'figures'
COLORS={'original_nll':'#777777','absolute_all':'#E69F00','joint_all':'#0072B2'}
LABELS={'original_nll':'NLL baseline (ours)','absolute_all':'Absolute-only control (ours)','joint_all':'Joint DD candidate (ours)'}
def save(fig,name):
    for ext in ['png','pdf']:fig.savefig(FIG/(name+'.'+ext),dpi=240,bbox_inches='tight')
    plt.close(fig)
def plot_matched_reference_maps(work, joint, detail):
    """Overlay fixed reference pairs without rematching, thinning or hiding outliers."""
    fig, axes = plt.subplots(3, 2, figsize=(10, 13), layout='constrained')
    for row, cat in enumerate(['Liu', 'Official', 'Shelly']):
        q = detail[(detail.catalog == cat) & (detail.branch == 'joint_all')]
        ids = q.event_id
        assert ids.is_unique
        frames = [('original_nll', work.loc[ids]), ('joint_all', joint.loc[ids])]
        xx = np.concatenate([q.rx.to_numpy()] + [f.x_km.to_numpy() for _, f in frames])
        yy = np.concatenate([q.ry.to_numpy()] + [f.y_km.to_numpy() for _, f in frames])
        for col, (branch, frame) in enumerate(frames):
            ax = axes[row, col]
            ax.scatter(q.rx, q.ry, s=9, marker='+', c='#D55E00',
                       alpha=.55, linewidths=.5, rasterized=True, label='Reference: ' + cat)
            ax.scatter(frame.x_km, frame.y_km, s=2, c='#0072B2',
                       alpha=.45, linewidths=0, rasterized=True, label=LABELS[branch])
            ax.set(xlim=(xx.min()-1, xx.max()+1), ylim=(yy.min()-1, yy.max()+1),
                   xlabel='East (km)', ylabel='North (km)')
            ax.set_aspect('equal', adjustable='box')
            ax.set_title(f'{"abcdef"[row*2+col]}  {LABELS[branch]} vs {cat}',
                         loc='left', fontsize=10)
            matched = detail[(detail.catalog == cat) & (detail.branch == branch)].set_index('event_id').loc[ids]
            assert np.allclose(matched.rx, q.rx) and np.allclose(matched.ry, q.ry)
            median = matched.horizontal_km.median()
            ax.text(.97, .03, f'N = {len(ids):,}\nMedian ΔH = {median:.2f} km',
                    ha='right', va='bottom', transform=ax.transAxes, fontsize=9)
            ax.legend(loc='upper right', frameon=False, fontsize=8, markerscale=2)
    save(fig, '04_matched_reference_maps')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--matched-only', action='store_true', help='Render only the paired reference overlay figure.')
    args = parser.parse_args()
    base=pd.read_csv(HERE/'export/01_baseline/10_validate_catalog/events.csv',low_memory=False).set_index('event_id')
    work=base[base.in_v1_working_catalog].copy()
    candidate=pd.read_csv(OUT/'working_catalog.csv').set_index('event_id').loc[work.index]
    joint=candidate
    coverage=pd.read_csv(OUT/'event_quality.csv').set_index('event_id').loc[work.index]
    detail=pd.read_csv(OUT/'reference_comparison.csv')
    refs=pd.read_csv(HERE/'export/01_baseline/05_review_catalog/reference_events.csv')
    assert len(candidate)==6520 and candidate.index.is_unique
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    if args.matched_only:
        plot_matched_reference_maps(work, joint, detail)
        return
    # Native-population reference maps: identical scope and symbols, not paired subsets.
    mapframes=[('NLL baseline (ours)',work.reset_index().assign(time=work.origin_time.to_numpy())),('Joint DD candidate (ours)',candidate.reset_index().assign(time=candidate.origin_time.to_numpy()))]
    for name in ['Official','Liu','Shelly']:mapframes.append(('Reference: '+name,refs[refs.catalog.eq(name)].copy()))
    oldmaps=pd.read_csv(HERE/'export/11_plot_catalog_maps/plotted_events.csv')
    ross=oldmaps[(oldmaps.figure=='working_subset')&(oldmaps.catalog=='Ross_relocated')].copy()
    mapframes.append(('Reference: Ross relocated',ross))
    fig,axes=plt.subplots(2,3,figsize=(12,8),sharex=True,sharey=True,layout='constrained');pop=[]
    for i,((label,d),ax) in enumerate(zip(mapframes,axes.ravel())):
        t=pd.to_datetime(d.time,utc=True,format='ISO8601');mask=t.ge(pd.Timestamp('2019-07-04T15:35:29.4Z'))&t.lt(pd.Timestamp('2019-07-07T00:00:00Z'))&d.longitude.between(-117.9,-117.2)&d.latitude.between(35.45,36.05);d=d[mask]
        ax.scatter(d.longitude,d.latitude,s=.8,c='#252525',alpha=.35,linewidths=0,rasterized=True)
        ax.set(xlim=(-117.9,-117.2),ylim=(35.45,36.05));ax.set_aspect(1/np.cos(np.deg2rad(35.75)))
        ax.set_title(f'{"abcdef"[i]}  {label}',loc='left');ax.text(.97,.97,f'N = {len(d):,}',ha='right',va='top',transform=ax.transAxes)
        if i>=3:ax.set_xlabel('Longitude (°)')
        if i%3==0:ax.set_ylabel('Latitude (°N)')
        pop.append({'catalog':label,'plotted_events':len(d)})
    save(fig,'01_catalog_maps')
    # Same IDs and complete coordinate ranges for the depth sections.
    fig,axes=plt.subplots(2,3,figsize=(12,8),layout='constrained');norm=Normalize(0,25)
    ranges={k:(min(work[k].min(),joint[k].min())-1,max(work[k].max(),joint[k].max())+1) for k in ['x_km','y_km']}
    flags=coverage.candidate_depth_boundary
    for row,(frame,name) in enumerate([(work,'NLL baseline (ours)'),(joint,'Joint DD candidate (ours)')]):
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
        ax.set_title('Reference: '+cat,loc='left');ax.set_xlabel('Horizontal discrepancy (km)');ax.set_ylabel('Cumulative fraction')
    ax=axes[1,1]
    for branch in COLORS:
        values=np.sort(detail[(detail.branch==branch)&(detail.catalog=='Shelly')].absolute_depth_km.dropna().to_numpy());ax.plot(values,np.arange(1,len(values)+1)/len(values),color=COLORS[branch],label=LABELS[branch],lw=1.3)
    ax.set_title('Reference: Shelly (depth)',loc='left');ax.set_xlabel('Absolute depth discrepancy (km)');ax.set_ylabel('Cumulative fraction');axes[0,0].legend(frameon=False,fontsize=8);save(fig,'03_reference_discrepancies')
    plot_matched_reference_maps(work, joint, detail)
    report=OUT/'README.md'
    if report.exists():
        text=report.read_text()
        for old,new in [('Original NLL',LABELS['original_nll']),('Joint candidate',LABELS['joint_all']),('Absolute only',LABELS['absolute_all'])]:
            text=text.replace(old,new)
        report.write_text(text)

if __name__=='__main__':main()
