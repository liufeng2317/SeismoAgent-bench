#!/usr/bin/env python3
"""Report the fixed P/S qualification without changing its failed joint decision."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/46_alternative_picker'
def main():
 result=json.loads((OUT/'qualification.json').read_text());q=pd.read_csv(OUT/'qualification_results.csv');assert not result['qualification_gates']['P_coverage'] and result['new_target_picks_added']==0
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 fig,axes=plt.subplots(1,2,figsize=(7.1,2.8),layout='constrained')
 for i,(phase,color) in enumerate([('P','#0072B2'),('S','#D55E00')]):
  g=q[q.phase.eq(phase)];a=g[g.accepted];axes[0].bar(i,len(a)/len(g),color=color,width=.55);v=np.sort(a.difference_from_existing_pick_s.abs());axes[1].plot(v,np.arange(1,len(v)+1)/len(v),label=phase,color=color)
 axes[0].axhline(.5,color='black',lw=.8,ls='--');axes[0].set(xticks=[0,1],xticklabels=['P','S'],ylim=(0,1),ylabel='Accepted fraction')
 axes[1].set(xlabel='Absolute pick-time difference (s)',ylabel='Cumulative fraction',xlim=(0,max(.5,float(q[q.accepted].difference_from_existing_pick_s.abs().max())*1.03)),ylim=(0,1));axes[1].legend(frameon=False)
 for a,l in zip(axes,'ab'):a.text(0,1.04,l,transform=a.transAxes,fontweight='bold')
 for suffix in ['png','pdf']:fig.savefig(OUT/('qualification_comparison.'+suffix),dpi=220)
 plt.close(fig)
 (OUT/'README.md').write_text('''# EQTransformer P/S qualification — round 25

**Completed; joint P/S candidate rejected.** No target observations or locations are changed. Do not lower the P acceptance gate or call the S-only result a pass for this round.

Test the local original non-conservative EQTransformer weights on 1,186 preselected phase examples from the old transfer cohort, disjoint from all current target/support events and confirmation reserve 3. Use the published model's preprocessing, two shifted 90-second contexts and unchanged predefined phase/detection, prediction-distance and time-stability rules. Qualification labels are automated original picks, not manual truth; original locations used those labels, and training overlap has not been established.

| Phase | Examples | Instruments | Accepted | Accepted fraction | Median absolute difference | P90 absolute difference | Signed median |
|---|---:|---:|---:|---:|---:|---:|---:|
| P | 640 | 37 | 238 | 37.19% | 0.040 s | 0.110 s | -0.020 s |
| S | 546 | 34 | 492 | 90.11% | 0.050 s | 0.090 s | -0.040 s |

P fails the fixed >=50% coverage criterion: 156 cases fail detection-at-pick, 141 lack an admitted peak and 105 are unstable across contexts. Its accepted timings pass, but that does not repair the missing coverage. All S criteria pass. This is method compatibility, not proof of higher location accuracy or independent S truth.

Close the joint candidate without changing weights or thresholds. The separately demonstrated S compatibility motivates a distinct, explicitly counted S-only missing-observation trial; it must pass the complete original catalog-level gates before adoption. That future trial cannot retroactively convert this failed round to a success.

Run `python 03_experiments/11_alternative_picker/46_qualify_eqtransformer.py --workers 8`, then `python 03_experiments/11_alternative_picker/46_report_qualification.py` from the expert root. `qualification_results.csv` preserves every decision, `qualification.json` the frozen gate outcome, and `qualification_comparison.png/pdf` the coverage/timing summary. An initial pre-inference timestamp parser error is archived in `provenance/`; it produced no scientific results and changed no rule.

Sources: [Mousavi et al. (2020)](https://www.nature.com/articles/s41467-020-17591-w), [SeisBench model documentation](https://seisbench.readthedocs.io/en/latest/pages/documentation/models/waveform_models.html#eqtransformer). Exact local implementation, weights, metadata and input identities are frozen in `design.json`.
''')
if __name__=='__main__':main()
