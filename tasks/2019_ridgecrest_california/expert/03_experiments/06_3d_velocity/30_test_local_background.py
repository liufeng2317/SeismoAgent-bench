#!/usr/bin/env python3
"""Round10 transfer experiment: fixed local depth background, regional lateral structure."""
from pathlib import Path
import argparse, importlib.util, json, sys
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
B=load('background30',Path(__file__).with_name('30_build_local_background.py'));G=B.G
S=load('native30',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
C=load('comparison30',Path(__file__).with_name('_transfer_comparison.py'))
OUT=B.OUT/'transfer';OLD=HERE/'export/29_3d_velocity/transfer'

def prepare():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'tables').mkdir(exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text());e=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False);p=p[p.event_id.isin(e.event_id)].copy();p['residual_s']=p.residual_s_gamma
    st=pd.read_csv(G.BASE/'stations.csv').set_index('id');held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    assert len(e)==147 and len(p)==5413 and p.pick_id.is_unique
    olddesign=json.loads((OLD/'design.json').read_text())
    files=[Path(__file__),Path(B.__file__),Path(G.__file__),Path(S.__file__),Path(C.__file__),B.OUT/'model_design.json',OLD/'design.json',OLD/'run.json',OLD/'tables/events.csv',OLD/'tables/fit_phases.csv',OLD/'verified_grid_inputs.json']
    files += [Path(__file__).with_name('_model_figures.py')]
    files+=list(map(Path,olddesign['source_sha256']))
    frozen=dict(round=10,intervention='Local 1D depth background with unchanged regional fractional lateral variations; model_design.json fixes ROI/taper/normalization before results. No reference fitting.',gates={**olddesign['gates'],'execution':'All 294 new and 294 reused matched-background fits pass identity/timing checks; all original picks retained.'},execution='294 new regional/withheld_regional fits plus 294 reused matched-background fits; all original picks retained; identities/timing checked. Original fine 2D controls remain a second comparison.',confirmation='Second reserve unused; all gates must pass before opening it.',source_sha256={str(f):G.sha(f) for f in files})
    path=OUT/'design.json'
    if path.exists():assert json.loads(path.read_text())==frozen
    else:G.write_json(path,frozen)
    return cfg,e,p,st,held

def predict(branch,p,st):
    if 'original' in branch:return S.DIAG.predict(G.BASE/'grids',p,st)[0]
    return G.predict(G.OUT/('regional' if 'regional' in branch else 'baseline'),p,st)

def verify_grids():
    assert json.loads((B.OUT/'grid_run.json').read_text())['complete']
    previous=json.loads((OLD/'verified_grid_inputs.json').read_text());records={}
    for label in ['baseline','regional']:
        folder=G.OUT/label
        for marker in sorted(folder.glob('*.complete.json')):
            m=json.loads(marker.read_text());phase,sid=marker.name.removesuffix('.complete.json').split('_');buf=folder/f'time.{phase}.{sid}.time.buf';hdr=buf.with_suffix('.hdr')
            assert G.sha(buf)==m['time_sha256'] and G.sha(hdr)==m['header_sha256']
            if label=='baseline':assert previous[str(buf.resolve())]==dict(time_sha256=m['time_sha256'],header_sha256=m['header_sha256'])
            records[str(buf)]=dict(time_sha256=m['time_sha256'],header_sha256=m['header_sha256'])
    assert len(records)==148
    for d in json.loads((OLD/'numerical_checks.json').read_text()):assert d['passed']
    G.write_json(OUT/'verified_grid_inputs.json',records)
    print('All 148 grid identities verified; unchanged baseline numerical gate retained.',flush=True)

def run(data,workers):
    cfg,e,p,st,held=data;verify_grids()
    rows=[];links=[];failures=[]
    for name in ['events','fit_phases']:
        q=pd.read_csv(OLD/f'tables/{name}.csv');q=q[q.branch.isin(['baseline','withheld_baseline'])]
        if name=='events':rows=q.to_dict('records');assert len(rows)==294
        else:links=q.to_dict('records')
    groups={eid:g.to_dict('records') for eid,g in p.groupby('event_id')}
    proxy=OUT/'input_regional';proxy.mkdir(exist_ok=True)
    for name,target in [('events_raw',G.BASE/'events_raw'),('grids',G.OUT/'regional')]:
        dest=proxy/name
        if not dest.exists():dest.symlink_to(target,target_is_directory=True)
        assert dest.resolve()==target.resolve()
    S.OUT=OUT;S.BASE=proxy;S.write_json=G.write_json;aliases=st.nll_station.to_dict()
    # One fixed implementation check, also reused as a primary result.
    event=e.sort_values('event_id').iloc[0].to_dict();r,l=S.solve(event,groups[event['event_id']],'regional',{},aliases,cfg)
    q=pd.DataFrame(l).reset_index(drop=True)
    for c in S.XYZ:q[c]=r[c]
    pred=predict('regional',q,st);err=float(np.max(np.abs(pred-q.predicted_travel_time_s)));assert err<.00035
    G.write_json(OUT/'pilot_check.json',dict(event_id=event['event_id'],max_native_tt_difference_s=err))
    print('Fixed pilot interpolation verified:',err,flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(S.solve,event,groups[event['event_id']],branch,{},aliases,cfg,held if branch.startswith('withheld_') else ()):(branch,event['event_id']) for branch in ['regional','withheld_regional'] for event in e.to_dict('records')}
        for i,f in enumerate(as_completed(jobs),1):
            try:r,l=f.result();rows.append(r);links.extend(l)
            except Exception as exc:failures.append(dict(branch=jobs[f][0],event_id=jobs[f][1],error=repr(exc)));print('FAILED',failures[-1],flush=True)
            if i%20==0 or i==len(jobs):print(f'[{i}/{len(jobs)}] new fits; failures={len(failures)}',flush=True)
    pd.DataFrame(rows).to_csv(OUT/'tables/events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'tables/fit_phases.csv',index=False);pd.DataFrame(failures,columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv',index=False)
    assert not failures and len(rows)==588

def report(data):
    C.report(data,out=OUT,here=HERE,native=S,predict=predict,write_json=G.write_json,round_id=10,title='Local 1D background with regional lateral variations')
    p=OUT/'README.md';p.write_text(p.read_text()+'\n## Model and control provenance\n\nmodel_design.json in the parent directory fixes the area-weighted local-depth normalization, full-strength fractional lateral variations and the original support taper. No reference coordinates or event residuals determine the velocity field. All 294 matched-background controls are reused from verified stage29 tables; 294 candidate fits are new. The second 300-event reserve remains unused at this stage. See background_profiles.csv and model_checks.json for the exact replaced mean profiles and checks.\n')
    plot=load('plot30',Path(__file__).with_name('_model_figures.py'))
    plot.main(out=OUT,expected_round=10,regional_label='3D + local background')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['prepare','run','report','all'],default='all');ap.add_argument('--workers',type=int,default=8);a=ap.parse_args()
    import fcntl
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);data=prepare()
        if a.stage in ['all','run']:run(data,a.workers)
        if a.stage in ['all','report']:report(data)
if __name__=='__main__':main()
