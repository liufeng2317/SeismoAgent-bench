#!/usr/bin/env python3
"""Display calibration transfer to location; no extra fits or selections."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/49_velocity_ratio/location';OLD=HERE/'export/48_differential_augmentation/refreshed'
def main():
 e=pd.read_csv(OUT/'target_changes.csv');a=pd.read_csv(OLD/'metrics.csv').set_index(['branch','kind']);b=pd.read_csv(OUT/'metrics.csv').set_index(['branch','kind']);r=pd.read_csv(OUT/'reference_summary.csv').set_index(['branch','catalog']);old=pd.read_csv(OLD/'reference_summary.csv').set_index(['branch','catalog'])
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42});fig,axes=plt.subplots(1,3,figsize=(10,3.2),layout='constrained')
 axes[0].scatter(e.previous_depth_km,e.depth_km,s=12,alpha=.6,color='#0072B2');axes[0].plot([0,25],[0,25],color='black',lw=.8);axes[0].set(xlim=(0,25),ylim=(0,25),xlabel='Stage48 depth (km)',ylabel='Calibrated Vp/Vs depth (km)')
 x=np.arange(2);axes[1].bar(x-.18,[a.loc[('joint_withheld',k),'rms_s'] for k in ['absolute','cc']],.36,color='#666666',label='Stage48');axes[1].bar(x+.18,[b.loc[('joint_withheld',k),'rms_s'] for k in ['absolute','cc']],.36,color='#0072B2',label='Calibrated');axes[1].set(xticks=x,xticklabels=['Arrivals','CC 1524'],ylabel='Held-out RMS (s)');axes[1].legend(frameon=False)
 x=np.arange(3);cats=['Liu','Official','Shelly'];axes[2].bar(x-.18,[old.loc[('joint_all',c),'median_horizontal_km'] for c in cats],.36,color='#666666');axes[2].bar(x+.18,[r.loc[('joint_all',c),'median_horizontal_km'] for c in cats],.36,color='#0072B2');axes[2].set(xticks=x,xticklabels=cats,ylabel='Median horizontal difference (km)')
 for ax,letter in zip(axes,'abc'):ax.text(0,1.04,letter,transform=ax.transAxes,fontweight='bold')
 for ext in ['png','pdf']:fig.savefig(OUT/('location_comparison.'+ext),dpi=220)
 plt.close(fig)
if __name__=='__main__':main()
