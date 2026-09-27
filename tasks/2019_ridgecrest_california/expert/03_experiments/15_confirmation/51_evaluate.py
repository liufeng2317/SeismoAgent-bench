#!/usr/bin/env python3
"""Open confirmation outcomes only after all frozen fits and native controls finish."""
import json
import pandas as pd
import _confirmation as F
C=F.load('confirmation51_solver',F.OUT.parents[1]/'03_experiments/15_confirmation/51_run.py')
V=F.load('confirmation51_validation',F.HERE/'03_experiments/07_joint_location/_joint_validation.py')

def main():
 F.verify_candidate()
 for name in ['design.json','graph_design.json','cc_processing/design.json','location_design.json','observations/design.json','observations/model_identity.json','native_controls/design.json']:
  for f,h in json.loads((F.OUT/name).read_text())['source_sha256'].items():assert F.sha(f)==h,f
 status=pd.read_csv(F.OUT/'solver_status.csv');assert len(status)==16
 r=V.evaluate(C,F.OUT,round_id=30,cohort_role='confirmation');r['reserve_v2_used']=False;r['reserve_v3_used']=True;r['cohort_role']='unused_outcome_confirmation';r['all_gates_passed']=all(r['gates'].values());r['development_candidate']='stage50';r['optimization_rounds_remaining']=0;r['independence_limit']='Targets had no previous development outcomes; upstream original catalog, shared support events and receiver selection are not independent ground truth.';F.save(F.OUT/'run.json',r)
 report=F.OUT/'RESULTS.md';text=report.read_text();start=text.index('```json\n')+8;end=text.index('\n```',start);report.write_text(text[:start]+json.dumps(r,indent=2)+text[end:])
 readme='''# Frozen candidate confirmation (round 30)

This is the final confirmation round of the 30-round campaign. The stage50 candidate is applied without tuning to all 300 third-reserve targets. Support events remain latent unknowns, not known-location anchors. No reference outcomes were read during observation extraction or graph construction.

The original elevated linear 1D model, observation errors, scalar P/vector S correlation, relative-only EQTransformer S observations, Huber CC objective and 16 matched fits are unchanged. Original PhaseNet counts determine auxiliary eligibility before augmentation. Previously admitted support observations are preserved. The six held instruments remain excluded from auxiliary fitting. Reference identities are the original frozen matches, never rematched to favor the result.

`inputs/` contains the final cohort and observations; `observations/` records real waveform queries and admissions; `native_controls/` holds original-model station-omission controls; `events.csv` contains experimental branch locations, not an adopted full catalog. `RESULTS.md` records all gates. Shared supports and prior catalog exposure limit independence.

'''
 readme+='Decision: **'+r['decision']+'**.\n\n'
 readme+=('All confirmation gates passed. Full-production generation and whole-product verification are still required before catalog adoption.\n' if r['all_gates_passed'] else 'Confirmation did not pass every frozen gate. Do not promote this candidate or start another adaptive round under the exhausted 30-round budget. Retain v1 as the current product and report the failed gates without relaxing them.\n')
 (F.OUT/'README.md').write_text(readme);print(json.dumps(r,indent=2),flush=True)
if __name__=='__main__':main()
