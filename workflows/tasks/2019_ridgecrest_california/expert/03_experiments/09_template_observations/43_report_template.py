#!/usr/bin/env python3
"""Report the frozen hidden-pick experiment without changing its decision."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/43_template_p_observations'
def main():
 r=pd.read_csv(OUT/'qualification_results.csv');q=pd.read_csv(OUT/'qualification_inputs.csv');a=r[r.kind.eq('query')&r.accepted].merge(q,on=['id','instrument_id','query_event']);a['abs_error_s']=a.difference_from_hidden_P_s.abs();a['hidden_inside_search']=a.center_difference_s.abs().le(.75);a.to_csv(OUT/'accepted_timing_audit.csv',index=False)
 chosen=pd.concat([a.nlargest(4,'abs_error_s').assign(example='largest_timing_disagreement'),a.iloc[(a.abs_error_s-a.abs_error_s.median()).abs().argsort()[:2]].assign(example='near_median_timing_disagreement')]);chosen.to_csv(OUT/'plotted_examples.csv',index=False)
 data=np.load(OUT/'qualification_windows.npz');t=np.arange(-500,301)/100;plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42});fig,axes=plt.subplots(3,2,figsize=(10,7),layout='constrained')
 for ax,(_,row) in zip(axes.ravel(),chosen.iterrows()):
  ta=data[row.template_pick_id][0];qb=data[row.id+'|query'][0];tq=t+row.center_difference_s
  ta=ta/max(np.max(abs(ta[(t>=-1)&(t<=2)])),1e-20);qb=qb/max(np.max(abs(qb[(tq>=-1)&(tq<=2)])),1e-20)
  ax.plot(t,ta+2,color='black',lw=.7,label='Template');ax.plot(tq,qb,color='#0072B2',lw=.7,label='Query');ax.axvline(0,color='#009E73',lw=1,label='Existing P');ax.axvline(row.difference_from_hidden_P_s,color='#D55E00',lw=1,label='Transferred P');ax.set(xlim=(-1,2),ylim=(-1.2,3.2),yticks=[0,2],yticklabels=['Query','Template'],title=row.instrument_id+' / '+row.query_event,xlabel='Time relative to existing P (s)')
 handles,labels=axes.ravel()[0].get_legend_handles_labels();fig.legend(handles,labels,frameon=False,fontsize=9,loc='upper center',bbox_to_anchor=(.5,1.03),ncol=4)
 for suffix in ['png','pdf']:fig.savefig(OUT/('template_timing_examples.'+suffix),dpi=220,bbox_inches='tight')
 plt.close(fig);data.close();result=json.loads((OUT/'qualification.json').read_text());outliers=a[a.abs_error_s>.2]
 (OUT/'RESULTS.md').write_text('# Template P qualification\n\nDecision: **'+result['decision']+'**. No target observations or locations were changed.\n\n```json\n'+json.dumps(result,indent=2)+'\n```\n\nThere are '+str(len(outliers))+' accepted examples with >0.2 s disagreement, of which '+str((~outliers.hidden_inside_search).sum())+' have the hidden existing pick outside the search interval. Existing picks are automated labels, not ground truth; the disagreement may reflect wrong waveform correspondence, an incorrect existing pick or association. High CC alone cannot resolve that ambiguity. Off-time acceptance is measured without a prediction-time veto and may contain real earthquakes.\n\n`template_timing_examples` shows four largest disagreements and two near-median examples selected deterministically in `plotted_examples.csv`. Each filtered trace is normalized independently for display. These examples are not manual truth labels and do not replace the full qualification table.\n')
 print('Reported',len(a),'accepted cases;',len(outliers),'timing disagreements >0.2 s; decision unchanged.',flush=True)
if __name__=='__main__':main()
