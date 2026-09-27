#!/usr/bin/env python3
"""Disjoint-event P static corrections in the fixed regional 3D model."""
from pathlib import Path
import importlib.util,json,hashlib,types,argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
DIR=Path(__file__).resolve().parent

def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
C=load('physical41',DIR/'40_joint_3d.py');M=C.M;HERE=M.HERE;SRC=HERE/'export/40_joint_3d_model';OUT=HERE/'export/41_regional_p_statics';CAL=HERE/'export/29_3d_velocity/transfer/tables'
C.OUT=OUT;C.R.C.OUT=OUT;C.R.C.INPUT=OUT/'inputs'

def estimate(q,support):
 g=q[q.instrument_id.isin(support)].groupby('instrument_id').centered_s.agg(['size','median']).reindex(support);assert g.notna().all().all()
 g['correction_s']=g['median']-np.average(g['median'],weights=g['size']);assert abs(np.average(g.correction_s,weights=g['size']))<1e-12
 return g

def calibration():
 events=pd.read_csv(CAL/'events.csv');events=events[events.branch.eq('regional')].set_index('event_id');assert len(events)==147 and events.status.eq('LOCATED').all()
 phases=pd.read_csv(CAL/'fit_phases.csv');phases=phases[phases.branch.eq('regional')&phases.phase.eq('P')].reset_index(drop=True)
 full=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv');phases=phases.merge(full[['pick_id','time_utc']],on='pick_id',validate='one_to_one');assert len(phases)==2563
 targets=pd.read_csv(SRC/'inputs/events.csv');assert not set(events.index)&set(targets.event_id)
 phases[M.XYZ]=events.loc[phases.event_id,M.XYZ].to_numpy();stations=pd.read_csv(M.BASE/'stations.csv').set_index('id')
 predicted=C.G.predict(C.REGIONAL,phases,stations);t0=pd.to_datetime(events.loc[phases.event_id,'origin_time'],utc=True,format='ISO8601').astype('int64').to_numpy()/1e9;t=pd.to_datetime(phases.time_utc,utc=True,format='ISO8601').astype('int64').to_numpy()/1e9
 phases['independent_residual_s']=t-t0-predicted;native_error=float(np.max(abs(phases.independent_residual_s-phases.residual_s)));assert native_error<.00035
 phases['centered_s']=phases.independent_residual_s-phases.groupby('event_id').independent_residual_s.transform('median');phases['fold']=phases.event_id.map(lambda s:int(hashlib.sha256(s.encode()).hexdigest(),16)%2)
 table=phases.groupby(['instrument_id','fold']).centered_s.agg(['size','median']).unstack();supported=table[(table['size'][0]>=20)&(table['size'][1]>=20)].index.sort_values();assert len(supported)>0
 correction=estimate(phases,supported);a=estimate(phases[phases.fold.eq(0)],supported);b=estimate(phases[phases.fold.eq(1)],supported)
 correction['fold0_n']=a['size'];correction['fold1_n']=b['size'];correction['fold0_correction_s']=a.correction_s;correction['fold1_correction_s']=b.correction_s;correction.index.name='instrument_id';correction.to_csv(OUT/'p_corrections.csv')
 q=phases[phases.instrument_id.isin(supported)].copy();q['crossfit_correction_s']=[(b if fold==0 else a).loc[sid,'correction_s'] for sid,fold in zip(q.instrument_id,q.fold)];before=q.centered_s.to_numpy();after=q.centered_s-q.crossfit_correction_s;after=after-after.groupby(q.event_id).transform('median')
 # Compare centered residuals on the identical supported rows, centering both sides identically.
 before=q.centered_s-q.groupby('event_id').centered_s.transform('median')
 summary={'calibration_events':len(events),'calibration_picks':len(phases),'disjoint_from_all_target_and_support_events':True,'supported_instruments':len(supported),'split_correction_correlation':float(a.correction_s.corr(b.correction_s)),'crossfit_centered_before_rms_s':float(np.sqrt(np.mean(before**2))),'crossfit_centered_after_rms_s':float(np.sqrt(np.mean(after**2))),'native_residual_equation_max_s':native_error,'weighted_P_mean_s':float(np.average(correction.correction_s,weights=correction['size'])),'min_correction_s':float(correction.correction_s.min()),'max_correction_s':float(correction.correction_s.max()),'limitations':'Fixed-location split diagnostics; calibration locations used their own picks. Not independent calibration-location truth or evidence of physical clock errors. Coefficients transferred to disjoint target/support events; no target residual or reference was used.'}
 phases.to_csv(OUT/'calibration_picks.csv',index=False);M.save(OUT/'calibration_checks.json',summary);print(json.dumps(summary,indent=2),flush=True)

def problem(template,auxiliary):
 p=C.problem(template,auxiliary);correction=pd.read_csv(OUT/'p_corrections.csv').set_index('instrument_id').correction_s
 delay=p.p.instrument_id.map(correction).fillna(0).to_numpy();delay=np.where(p.p.phase.eq('P'),delay,0.);assert np.array_equal(delay[p.a],delay[p.b]);original=p.prediction
 def prediction(self,x):
  t,g=original(x);return t+delay,g
 p.raw_prediction=original;p.delay=delay;p.prediction=types.MethodType(prediction,p);return p

def prepare():
 OUT.mkdir(exist_ok=True)
 for name in ['inputs','cc_measurements.csv','native_controls']:C.R.ENGINE.link(SRC/name,OUT/name)
 files=[Path(__file__),DIR/'41_evaluate_p.py',Path(C.__file__),Path(C.R.__file__),Path(C.R.C.__file__),Path(M.__file__),DIR/'_joint_validation.py',CAL/'events.csv',CAL/'fit_phases.csv',HERE/'export/10_validate_catalog/phases.csv',SRC/'design.json',SRC/'verified_fields.json',SRC/'inputs/events.csv',SRC/'inputs/all_phases.csv',SRC/'cc_measurements.csv']
 design={'round':20,'cohort_role':'Same exposed 300 targets and 2581 supports; separate 147-event calibration cohort excluded from both.','intervention':'P-only empirical receiver terms in fixed regional 3D mean model. Recompute observed-minus-predicted residuals at archived native regional-model calibration locations; subtract each calibration event P median, estimate station medians, then remove calibration-count-weighted mean across supported P stations. S and unsupported P exactly zero. No depth/coordinate offsets or correction-strength scan.','support':'Deterministic SHA256(event_id) parity split; >=20 calibration P observations in each half. Apply all supported cells, without selecting by sign, reference outcome or target residual. Split correlation/crossfit are diagnostics, not location-accuracy validation.','gauge':'Calibration-weighted P correction mean is zero. This avoids fitting a free common P-S offset in calibration; it does NOT guarantee zero mean correction or zero depth shift on target geometries.','cc_semantics':'Identical station/phase static term cancels exactly in same-station CC differences. Add delay to absolute predictions; retain every absolute and CC observation, weight, 3D field, Huber rule, bound and solver setting. Corrections for omitted target stations are learned solely from disjoint calibration events.','gates':'All stage34 gates plus identical old-575 and fixed-1408 CC RMS <=1.05 uncorrected stage40 joint, held absolute <=1.05 uncorrected stage40 joint, all reference medians <=1.10 uncorrected stage40 joint AND both stage39 joint and matched-background 3D joint; fixed-1408 CC must also remain <=1.05 these two earlier joint controls. Keep original-NLL/reference gates and known failing 206/300 coverage. No promotion without fresh confirmation.','limitations':'Model-specific empirical receiver terms may contain picker, path and source-location errors; not established physical clock delays. Calibration events were examined in earlier development. Static cancellation applies only to matched station/phase pairs.','source_sha256':{str(f):M.sha(f) for f in files}}
 dest=OUT/'design.json'
 if dest.exists():assert json.loads(dest.read_text())==design
 else:M.save(dest,design)
 calibration();template=M.Problem();primary=problem(template,False);aux=problem(template,True)
 previous=json.loads((SRC/'verified_fields.json').read_text());verified={}
 for (_,_,_),(v,o,d,path) in C.FIELDS.items():
  info=previous[str(path)];assert C.sha_stream(path)==info['sha256'];assert M.sha(path.with_suffix('.hdr'))==info['header_sha256'];verified[str(path)]=info
 M.save(OUT/'verified_fields.json',verified)
 x=aux.start.copy();x[:,:3]+=.013;x=x.ravel();raw,rawg=aux.raw_prediction(x);t,g=aux.prediction(x);assert np.array_equal(g,rawg);cc_error=float(np.max(abs((t[aux.a]-t[aux.b])-(raw[aux.a]-raw[aux.b]))));assert cc_error<1e-12
 rng=np.random.default_rng(41);direction=rng.normal(size=len(x));direction/=np.linalg.norm(direction);fun,jac=aux.system(True,True);h=1e-4;error=float(np.max(abs((fun(x+h*direction)-fun(x-h*direction))/(2*h)-jac(x)@direction)));assert error<1e-5
 M.save(OUT/'numerical_checks.json',{'static_cc_cancellation_max_s':cc_error,'prediction_sign_max_error_s':float(np.max(abs(t-raw-aux.delay))),'unchanged_prediction_derivatives':True,'sparse_derivative_error':error,'primary_events':len(primary.e),'auxiliary_events':len(aux.e),'verified_regional_fields':len(verified)})
 return primary,aux

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['prepare','run'],default='run');parser.add_argument('--workers',type=int,default=4);args=parser.parse_args();primary,aux=prepare()
 if args.stage=='prepare':return
 jobs=[]
 for p,withheld in [(primary,False),(aux,True)]:
  for joint in [False,True]:
   branch=('joint' if joint else 'absolute')+('_withheld' if withheld else '_all')
   for label,shift in (M.SHIFTS.items() if withheld else [('control',(0,0,0))]):jobs.append((p,'regional',branch,label,shift))
 states=[]
 with ThreadPoolExecutor(max_workers=args.workers) as pool:
  for f in as_completed([pool.submit(C.solve,j) for j in jobs]):states.append(f.result());pd.DataFrame(states).to_csv(OUT/'solver_status.csv',index=False)
 assert len(states)==16
 for f,h in json.loads((OUT/'design.json').read_text())['source_sha256'].items():assert M.sha(Path(f))==h
 for path,info in json.loads((OUT/'verified_fields.json').read_text()).items():
  st=Path(path).stat();assert st.st_size==info['bytes'] and st.st_mtime_ns==info['mtime_ns']
if __name__=='__main__':main()
