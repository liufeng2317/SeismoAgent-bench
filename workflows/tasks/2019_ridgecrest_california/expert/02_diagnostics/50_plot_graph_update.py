#!/usr/bin/env python3
"""Compare stage50 with its fixed stage48 control on unchanged observations."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'export/50_uncertain_depth_pairs';OLD=HERE/'export/48_differential_augmentation/refreshed'
def main():
 e=pd.read_csv(OUT/'target_changes.csv');scores=pd.read_csv(OUT/'fixed_observation_scores.csv').set_index(['observations','solution','phase']).rms_s
 support=[]
 for label,path in [('stage48',OLD),('stage50',OUT)]:
  events=pd.read_csv(path/'inputs/events.csv');aux=set(events.loc[events.auxiliary_eligible,'event_id']);cc=pd.read_csv(path/'cc_measurements.csv');cc=cc[cc.accepted&cc.training&cc.event_id_a.isin(aux)&cc.event_id_b.isin(aux)]
  for eid in e.event_id:
   g=cc[cc.event_id_a.eq(eid)|cc.event_id_b.eq(eid)];support.append({'event_id':eid,'stage':label,'training_edges':len(g),'training_instruments':g.instrument_id.nunique(),'training_S_edges':int(g.phase.eq('S').sum()),'training_neighbors':len((set(g.event_id_a)|set(g.event_id_b))-{eid})})
 counts=pd.DataFrame(support);depth=e.set_index('event_id');counts['depth_km']=[depth.loc[row.event_id,'previous_depth_km' if row.stage=='stage48' else 'depth_km'] for row in counts.itertuples()];counts['near_depth_boundary']=(counts.depth_km<.5)|(counts.depth_km>24.5);counts.to_csv(OUT/'target_support_comparison.csv',index=False)
 boundary=e[(e.previous_depth_km<.5)|(e.previous_depth_km>24.5)];counts[counts.event_id.isin(boundary.event_id)].merge(boundary[['event_id','previous_depth_km','depth_km']],on='event_id',validate='many_to_one').to_csv(OUT/'previous_boundary_support.csv',index=False)
 metric=pd.read_csv(OUT/'metrics.csv').set_index(['branch','kind']);oldmetric=pd.read_csv(OLD/'metrics.csv').set_index(['branch','kind'])
 ref=pd.read_csv(OUT/'reference_summary.csv').set_index(['branch','catalog']);oldref=pd.read_csv(OLD/'reference_summary.csv').set_index(['branch','catalog'])
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 fig,axes=plt.subplots(1,3,figsize=(10.5,3.3),layout='constrained')
 axes[0].scatter(e.previous_depth_km,e.depth_km,s=12,alpha=.6,color='#0072B2');axes[0].plot([0,25],[0,25],color='black',lw=.8);axes[0].set(xlim=(0,25),ylim=(0,25),xlabel='Stage48 depth (km)',ylabel='Stage50 depth (km)')
 x=np.arange(3);sets=['fixed1408','fixed1524'];a=[oldmetric.loc[('joint_withheld','absolute'),'rms_s']]+[scores.loc[(k,'stage48','all')] for k in sets];b=[metric.loc[('joint_withheld','absolute'),'rms_s']]+[scores.loc[(k,'candidate','all')] for k in sets]
 axes[1].bar(x-.18,a,.36,color='#666666',label='Stage48');axes[1].bar(x+.18,b,.36,color='#0072B2',label='Stage50');axes[1].set(xticks=x,xticklabels=['Arrivals','CC 1408','CC 1524'],ylabel='Held-out RMS (s)',yscale='log');axes[1].legend(frameon=False)
 cats=['Liu','Official','Shelly'];axes[2].bar(x-.18,[oldref.loc[('joint_all',c),'median_horizontal_km'] for c in cats],.36,color='#666666');axes[2].bar(x+.18,[ref.loc[('joint_all',c),'median_horizontal_km'] for c in cats],.36,color='#0072B2');axes[2].set(xticks=x,xticklabels=cats,ylabel='Median horizontal difference (km)')
 for ax,letter in zip(axes,'abc'):ax.text(0,1.04,letter,transform=ax.transAxes,fontweight='bold')
 for ext in ['png','pdf']:fig.savefig(OUT/('graph_update_comparison.'+ext),dpi=220)
 plt.close(fig)
if __name__=='__main__':main()
