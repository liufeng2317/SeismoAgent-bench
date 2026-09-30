"""Readable delivery comparisons from frozen tables; no fitting or rematching."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]/'export/06_full_catalog/52_full_catalog'
OUT=ROOT/'figures'
COLORS=['#777777','#0072B2']

def save(fig,name):
    for ext in ['png','pdf']:fig.savefig(OUT/f'{name}.{ext}',dpi=240,bbox_inches='tight')
    plt.close(fig)

def main():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    s=pd.read_csv(ROOT/'reference_summary.csv').set_index(['branch','catalog'])
    fig,axes=plt.subplots(1,3,figsize=(14,3.8),layout='constrained')
    cats=['Liu','Official','Shelly']
    definitions=[('Horizontal difference','Median distance (km)',cats,[(c,'median_horizontal_km') for c in cats]),('Depth difference to Shelly','Absolute depth difference (km)',['Median','P90'],[('Shelly','median_abs_depth_km'),('Shelly','p90_abs_depth_km')]),('Origin-time difference','Median absolute difference (s)',cats,[(c,'median_abs_origin_s') for c in cats])]
    for ax,(title,label,names,fields),letter in zip(axes,definitions,'abc'):
        values=[]
        for i,(cat,field) in enumerate(fields):
            a=float(s.loc[('original_nll',cat),field]);b=float(s.loc[('joint_all',cat),field]);values.extend([a,b])
            ax.plot([a,b],[i,i],color='#888888',lw=1.5)
            for val,col,dy in [(a,COLORS[0],-.15),(b,COLORS[1],.20)]:
                ax.scatter(val,i,s=45,c=col,zorder=3)
                ax.text(val,i+dy,f'{val:.3f}',ha='center',va='center',fontsize=9,color=col)
        ax.set(yticks=range(len(names)),yticklabels=[('Reference: '+n) if n in cats else n for n in names],xlim=(0,max(values)*1.22),ylim=(len(names)-.5,-.65),xlabel=label)
        ax.set_title(f'{letter}  {title}',loc='left',fontsize=11)
        ax.spines['left'].set_visible(False);ax.tick_params(axis='y',length=0)
    handles=[plt.Line2D([],[],marker='o',ls='',color=c,label=t) for c,t in zip(COLORS,['NLL baseline (ours)','Joint DD candidate (ours)'])]
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,1.10),ncol=2,frameon=False,fontsize=10)
    save(fig,'05_delivery_metric_changes')
    # Fixed map-coordinate windows, selected on original coordinates only, not improvements.
    d=pd.read_csv(ROOT/'reference_comparison.csv')
    d=d[d.catalog.eq('Shelly')]
    b=d[d.branch.eq('original_nll')].set_index('event_id');j=d[d.branch.eq('joint_all')].set_index('event_id')
    assert b.index.is_unique and j.index.is_unique and set(b.index)==set(j.index)
    j=j.loc[b.index];assert b.reference_id.equals(j.reference_id)
    windows=[('North',-15.,20.),('Central',0.,0.)]
    fig,axes=plt.subplots(2,3,figsize=(12,7.3),layout='constrained');records=[]
    for row,(region,cx,cy) in enumerate(windows):
        ids=b.index[b.x_km.between(cx-5,cx+5)&b.y_km.between(cy-5,cy+5)]
        frames=[b.loc[ids,['x_km','y_km']].to_numpy(),b.loc[ids,['rx','ry']].to_numpy(),j.loc[ids,['x_km','y_km']].to_numpy()]
        allxy=np.concatenate(frames);lo=allxy.min(axis=0)-.5;hi=allxy.max(axis=0)+.5
        side=max(hi-lo);center=(hi+lo)/2;lo=center-side/2;hi=center+side/2
        for col,(xy,title) in enumerate(zip(frames,['NLL baseline (ours)','Reference: Shelly','Joint DD candidate (ours)'])):
            ax=axes[row,col];ax.scatter(xy[:,0],xy[:,1],s=5,c='#222222',alpha=.55,linewidths=0,rasterized=True)
            ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),xlabel='East (km)',ylabel='North (km)');ax.set_aspect('equal')
            ax.set_title(f'{"abcdef"[row*3+col]}  {title}',loc='left',fontsize=11)
        axes[row,0].text(.03,.97,f'{region} · n = {len(ids)}',transform=axes[row,0].transAxes,ha='left',va='top',fontsize=9)
        for eid in ids:records.append({'region':region,'event_id':eid,'reference_id':b.loc[eid,'reference_id'],'selection_center_x_km':cx,'selection_center_y_km':cy,'selection_half_width_km':5.})
    pd.DataFrame(records).to_csv(OUT/'06_local_comparison_events.csv',index=False)
    save(fig,'06_local_reference_comparison')
    print('Metric comparison and fixed-window maps complete; region counts:',pd.DataFrame(records).groupby('region').size().to_dict())

if __name__=='__main__':main()
