"""Fixed joint/absolute full-catalog fits and matched held-instrument controls."""
from pathlib import Path
import importlib.util
import json
from concurrent.futures import ProcessPoolExecutor,as_completed
import multiprocessing as mp
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parents[1]
OUT=HERE/'export/52_full_catalog'
spec=importlib.util.spec_from_file_location('full52_engine',HERE/'03_experiments/12_differential_augmentation/48_run.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
M=C.M
C.OUT=OUT;C.R.C.OUT=OUT;C.R.C.INPUT=OUT/'inputs'
PRIMARY=None
AUXILIARY=None

def execute_branch(branch):
    problem=AUXILIARY if branch.endswith('_withheld') else PRIMARY
    return C.solve((problem,branch,'control',(0,0,0)))


def main():
    global PRIMARY,AUXILIARY
    design=json.loads((OUT/'design.json').read_text())
    cc_checks=json.loads((OUT/'cc_processing/checks.json').read_text())
    assert cc_checks['fast_curve_equivalence'] and len(cc_checks['historical_reproduction'])==2
    assert all(r['identical_acceptance_and_lag'] for r in cc_checks['historical_reproduction'])
    for path,h in design['source_sha256'].items():assert M.sha(Path(path))==h,path
    paths=[Path(__file__),HERE/'01_pipeline/52_measure_full_catalog.py',HERE/'04_comparison/52_compare_full_catalog.py',Path(C.__file__),Path(C.R.C.__file__),Path(C.R.__file__),Path(M.__file__),OUT/'inputs/events.csv',OUT/'inputs/all_phases.csv',OUT/'cc_measurements.csv',M.BASE/'stations.csv']+sorted((M.BASE/'grids').glob('time.*.time.*'))
    frozen={'source_sha256':{str(f):M.sha(f) for f in paths},'fits':'Matched absolute/joint, primary and eligible six-instrument withholding. Fixed existing objective and solver. No new model selection, no multi-start revalidation in this full-scale application.'}
    path=OUT/'execution.json'
    if path.exists():assert json.loads(path.read_text())==frozen
    else:M.save(path,frozen)
    template=M.Problem();primary=C.problem(template,False);aux=C.problem(template,True)
    PRIMARY=primary;AUXILIARY=aux
    usage=primary.p[['pick_id','event_id','instrument_id','phase']].copy();usage['absolute_used']=primary.absolute_used
    usage.to_csv(OUT/'observation_usage.csv',index=False)
    x=aux.start.copy();x[:,:3]+=.013;x=x.ravel();d=np.random.default_rng(52).normal(size=len(x));d/=np.linalg.norm(d)
    for joint in [False,True]:
        f,j=aux.system(joint,True);h=1e-4;err=float(np.max(abs((f(x+h*d)-f(x-h*d))/(2*h)-j(x)@d)))
        assert err<1e-5; print('Jacobian error',joint,err,flush=True)
    jobs=[(p,b,'control',(0,0,0)) for p,bs in [(primary,['absolute_all','joint_all']),(aux,['absolute_withheld','joint_withheld'])] for b in bs]
    rows=[]
    print('Start four full-scale fits:',len(primary.e),'primary;',len(aux.e),'withheld-eligible; CC',len(primary.c),flush=True)
    with ProcessPoolExecutor(max_workers=4,mp_context=mp.get_context('fork')) as pool:
        for future in as_completed([pool.submit(execute_branch,job[1]) for job in jobs]):
            rows.append(future.result());pd.DataFrame(rows).to_csv(OUT/'solver_status.csv',index=False)
    assert len(rows)==4
    metrics=[];locations=[]
    for p,bs in [(primary,['absolute_all','joint_all']),(aux,['absolute_withheld','joint_withheld'])]:
        for branch in bs:
            with np.load(OUT/(branch+'_control.npz')) as z:
                assert np.array_equal(z['event_id'],p.e.event_id.to_numpy());x=z['x']
            assert np.isfinite(x).all()
            tt,_=p.prediction(x.ravel());ar=tt-p.obs;cr=tt[p.a]-tt[p.b]-p.dt
            for kind,values,mask in [('absolute',ar,~p.train&p.absolute_used),('cc',cr,~p.c.training.to_numpy())]:
                metrics.append(dict(branch=branch,kind=kind,heldout=branch.endswith('_withheld'),n=int(mask.sum()),rms_s=float(np.sqrt(np.mean(values[mask]**2)))))
            e=p.e[['event_id']].copy();e[M.XYZ]=x[:,:3];e['origin_time']=pd.to_datetime(p.t0+x[:,3],unit='s',utc=True).astype(str);e['branch']=branch
            locations.append(e)
            if branch=='joint_all':
                phase=p.p[['pick_id','event_id','instrument_id','phase','time_utc','source_channels']].copy()
                phase['absolute_used']=p.absolute_used;phase['candidate_residual_s']=ar
                phase.to_csv(OUT/'phases.csv',index=False)
    pd.DataFrame(metrics).to_csv(OUT/'metrics.csv',index=False)
    pd.concat(locations,ignore_index=True).to_csv(OUT/'branch_locations.csv',index=False)
    for path,h in frozen['source_sha256'].items():assert M.sha(Path(path))==h,path
    print(pd.DataFrame(metrics).to_string(index=False),flush=True)

if __name__=='__main__':main()
