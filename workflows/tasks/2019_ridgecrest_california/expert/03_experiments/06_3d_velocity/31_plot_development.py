#!/usr/bin/env python3
"""Plot every development S-P prediction; no trimming or reference coordinates."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]/'export/31_background_calibration/development'
def main():
 p=pd.read_csv(ROOT/'SP_predictions.csv');m=pd.read_csv(ROOT/'metrics.csv').set_index('model')
 models=['original','local_background','regional','midpoint'];labels=['Original 1D','Local background','Regional','Midpoint'];colors=['#333333','#0072B2','#D55E00','#009E73']
 assert len(p)==552 and all(len(p[p.model.eq(x)])==138 for x in models)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'pdf.fonttype':42})
 fig,axes=plt.subplots(1,2,figsize=(8,3.2),layout='constrained')
 for model,label,color in zip(models,labels,colors):
  values=np.sort(p[p.model.eq(model)].error_s.abs());assert np.isfinite(values).all()
  axes[0].plot(values,np.arange(1,len(values)+1)/len(values),label=label,color=color,lw=1.3)
 axes[0].set(xlabel='Absolute S–P prediction error (s)',ylabel='Cumulative fraction',xlim=(0,None),ylim=(0,1.02));axes[0].legend(frameon=False)
 axes[1].bar(np.arange(4),m.loc[models,'SP_rms_s'],color=colors,width=.6);axes[1].set(xticks=np.arange(4),xticklabels=labels,ylabel='S–P prediction RMS (s)');axes[1].tick_params(axis='x',rotation=20)
 for i,ax in enumerate(axes):ax.text(0,1.04,chr(97+i),transform=ax.transAxes,fontweight='bold',fontsize=11)
 for ext in ['png','pdf']:fig.savefig(ROOT/f'selection.{ext}',dpi=240)
 plt.close(fig)
 print('Saved untrimmed 138-event selection figure.')
if __name__=='__main__':main()
