#!/usr/bin/env python3
"""Fixed-target location and depth effects of the 3D model intervention."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/40_joint_3d_model'

def main():
 positions=pd.read_csv(OUT/'target_model_comparison.csv');reference=pd.read_csv(OUT/'reference_comparison.csv');reference=reference[reference.branch.eq('joint_all')&reference.catalog.eq('Shelly')][['event_id','reference_depth_km']]
 summary=pd.read_csv(OUT/'joint_control_reference_summary.csv');models=['previous_1d_joint','matched_3d_background_joint','regional_3d_joint'];labels=['1D radial','1D on 3D grid','Regional 3D'];colors=['#777777','#E69F00','#0072B2']
 indexed={model:positions[positions.solution.eq(model)].set_index('event_id') for model in models};base=indexed[models[0]];rows=[]
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.8,'pdf.fonttype':42,'ps.fonttype':42})
 fig,axes=plt.subplots(1,3,figsize=(10.8,3.25),layout='constrained')
 b=indexed[models[2]].loc[base.index];axes[0].scatter(base.depth_km,b.depth_km,s=9,alpha=.55,c=colors[2],linewidths=0,rasterized=True);axes[0].plot([0,25],[0,25],color='black',lw=.8);axes[0].set(xlim=(0,25),ylim=(0,25),xlabel='1D radial depth (km)',ylabel='Regional 3D depth (km)')
 cats=['Liu','Official','Shelly']
 for n,(model,label,color) in enumerate(zip(models,labels,colors)):
  q=summary[summary.solution.eq(model)].set_index('catalog');axes[1].bar(np.arange(3)+(n-1)*.24,q.loc[cats,'median_horizontal_km'],width=.24,color=color,label=label)
  p=indexed[model].loc[base.index];depth_delta=p.depth_km-base.depth_km;horizontal=np.hypot(p.x_km-base.x_km,p.y_km-base.y_km);matched=reference.merge(p.reset_index(),on='event_id',validate='one_to_one');residual=np.sort((matched.depth_km-matched.reference_depth_km).to_numpy());axes[2].plot(residual,np.arange(1,len(residual)+1)/len(residual),color=color,lw=1.4)
  folder={'previous_1d_joint':HERE/'export/39_support_aware_pairs','matched_3d_background_joint':OUT/'matched_background','regional_3d_joint':OUT}[model]
  with np.load(folder/'absolute_all_control.npz') as f:
   ids=pd.Index(f['event_id']).get_indexer(p.index);assert (ids>=0).all();joint_delta=p.depth_km.to_numpy()-f['x'][ids,2]
  rows.append({'solution':model,'n_targets':len(p),'median_signed_joint_minus_absolute_depth_km':float(np.median(joint_delta)),'median_absolute_joint_minus_absolute_depth_km':float(np.median(abs(joint_delta))),'p90_absolute_joint_minus_absolute_depth_km':float(np.quantile(abs(joint_delta),.9)),'median_depth_shift_from_stage39_km':float(depth_delta.median()),'median_horizontal_shift_from_stage39_km':float(np.median(horizontal)),'near_depth_boundary':int(((p.depth_km<.5)|(p.depth_km>24.5)).sum()),'n_Shelly_matches':len(matched),'median_signed_Shelly_depth_difference_km':float(np.median(residual)),'median_absolute_Shelly_depth_difference_km':float(np.median(abs(residual)))})
 axes[1].set(xticks=np.arange(3),xticklabels=cats,ylabel='Median horizontal difference (km)');axes[1].set_ylim(0,1);axes[1].legend(frameon=False,fontsize=8,loc='upper right')
 axes[2].set_xscale('symlog',linthresh=10);axes[2].set_xticks([-60,-10,-5,0,5,10]);axes[2].set_xticklabels(['−60','−10','−5','0','5','10']);axes[2].axvline(0,color='black',lw=.7);axes[2].set(xlabel='Depth − Shelly depth (km; symlog)',ylabel='Cumulative fraction',ylim=(0,1))
 for ax,letter in zip(axes,'abc'):ax.text(0,1.03,letter,transform=ax.transAxes,fontweight='bold',fontsize=12)
 fig.savefig(OUT/'physical_model_comparison.png',dpi=300);fig.savefig(OUT/'physical_model_comparison.pdf');plt.close(fig)
 pd.DataFrame(rows).to_csv(OUT/'model_effects.csv',index=False);print(pd.DataFrame(rows).to_string(index=False),flush=True)
if __name__=='__main__':main()
