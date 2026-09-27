#!/usr/bin/env python3
"""Plot fixed transfer comparisons without selecting favorable events."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2]
OUT=HERE/'export/29_3d_velocity/transfer'
LABELS={'original':'Original 1D','baseline':'Matched 1D','regional':'Regional 3D'}
COLORS={'original':'#333333','baseline':'#0072B2','regional':'#D55E00'}

def cdf(ax,values,branch):
    q=np.sort(np.asarray(values,float));assert np.isfinite(q).all() and len(q)
    ax.plot(q,np.arange(1,len(q)+1)/len(q),color=COLORS[branch],label=LABELS[branch],lw=1.3)

def main(*, out, expected_round, regional_label):
    global OUT
    OUT=Path(out)
    LABELS['regional']=regional_label
    status=json.loads((OUT/'run.json').read_text())
    assert status['round']==expected_round
    hp=pd.read_csv(OUT/'tables/heldout_predictions.csv')
    ref=pd.read_csv(OUT/'tables/reference_pairs.csv')
    new=pd.read_csv(OUT/'tables/events.csv')
    old=pd.read_csv(HERE/'export/20_velocity_model_qualification/tables/events.csv')
    old=old[old.branch.eq('control')].copy();old['branch']='original'
    e=pd.concat([new[new.branch.isin(['baseline','regional'])],old],ignore_index=True)
    assert len(e)==441 and not e.duplicated(['branch','event_id']).any()
    assert all(set(g.event_id)==set(old.event_id) for _,g in e.groupby('branch'))
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.linewidth':.7,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'ps.fonttype':42})
    fig,axs=plt.subplots(2,3,figsize=(10,5.8),layout='constrained')
    for branch in LABELS:
        held=hp[hp.branch.eq('withheld_'+branch)]
        cdf(axs[0,0],held.residual_s.abs(),branch)
        for ax,cat in zip(axs[0,1:],['Liu','Official']):
            cdf(ax,ref[ref.branch.eq(branch)&ref.catalog.eq(cat)].horizontal_km,branch)
        cdf(axs[1,0],ref[ref.branch.eq(branch)&ref.catalog.eq('Shelly')].horizontal_km,branch)
        cdf(axs[1,1],ref[ref.branch.eq(branch)&ref.catalog.eq('Shelly')].depth_difference_km.abs(),branch)
        cdf(axs[1,2],e[e.branch.eq(branch)].depth_km,branch)
    labels=['Held-out absolute residual (s)','Horizontal distance to Liu (km)','Horizontal distance to Official (km)','Horizontal distance to Shelly (km)','Absolute depth difference to Shelly (km)','Depth below benchmark datum (km)']
    for i,(ax,label) in enumerate(zip(axs.flat,labels)):
        ax.set(xlabel=label,ylabel='Cumulative fraction',ylim=(0,1.02),xlim=(0,None))
        ax.text(0,1.04,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=11)
    axs[0,0].legend(frameon=False)
    for ext in ['png','pdf']:fig.savefig(OUT/f'comparison.{ext}',dpi=240)
    plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(10,3.4),layout='constrained',sharex=True,sharey=True)
    for i,(ax,branch) in enumerate(zip(axs,LABELS)):
        g=e[e.branch.eq(branch)];sc=ax.scatter(g.x_km,g.y_km,c=g.depth_km,cmap='viridis_r',vmin=0,vmax=25,s=9,linewidths=0)
        ax.set(title=LABELS[branch],xlabel='East (km)',aspect='equal');ax.text(0,1.07,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=11)
    axs[0].set_ylabel('North (km)');fig.colorbar(sc,ax=axs,label='Depth below benchmark datum (km)',shrink=.8)
    for ext in ['png','pdf']:fig.savefig(OUT/f'locations.{ext}',dpi=240)
    plt.close(fig)
    (OUT/'README.md').write_text((OUT/'README.md').read_text().split('\n## Figures\n')[0]+'\n## Figures\n\ncomparison.png/pdf shows full empirical distributions without truncation or event filtering. Reference comparisons use the same fixed unambiguous identities in all branches; reference catalog differences are not errors against known truth. Only Shelly depth is treated as nominally datum-compatible. All held-out residuals use the fitted origin without recentering.\n\nlocations.png/pdf shows all 147 transfer events per model in the same benchmark coordinates, with identical spatial axes and depth colors. The regional model is the explicitly documented hybrid. These are validation-cohort figures, not the full catalog.\n')
    print('Saved comparison and locations figures for all fixed transfer events.')

