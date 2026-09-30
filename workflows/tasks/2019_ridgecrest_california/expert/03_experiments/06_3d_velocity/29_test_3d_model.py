#!/usr/bin/env python3
"""Fixed transfer comparison of the SCEDC-supported hybrid model, CPU only."""
import argparse, json, importlib.util, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
G=load('regional_grid',Path(__file__).with_name('29_build_3d_grids.py'))
S=load('regional_native',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
OUT=HERE/'export/29_3d_velocity/transfer'
XYZ=S.XYZ

def prepare():
    OUT.mkdir(exist_ok=True);(OUT/'tables').mkdir(exist_ok=True);G.configure(.25)
    e=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False);p=p[p.event_id.isin(e.event_id)].copy();p['residual_s']=p.residual_s_gamma
    st=pd.read_csv(G.BASE/'stations.csv').set_index('id')
    held=json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations']
    assert len(e)==147 and len(p)==5413 and p.pick_id.is_unique
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text())
    paths=[Path(__file__),Path(G.__file__),Path(S.__file__),HERE/'00_config/nonlinloc.yaml',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'export/10_validate_catalog/phases.csv',HERE/'export/10_validate_catalog/reference_matches.csv',HERE/'export/05_review_catalog/reference_events.csv',HERE/'export/12_relative_location_pilot/run.json',G.BASE/'stations.csv',G.OUT/'grid_design.json',HERE/'export/20_velocity_model_qualification/tables/events.csv',HERE/'export/20_velocity_model_qualification/tables/fit_phases.csv']
    paths += [HERE/'01_pipeline/04_locate_nonlinloc.py', HERE/'02_diagnostics/16_diagnose_systematics.py', Path(cfg['binary_directory'])/'NLLoc', Path(cfg['binary_directory'])/'NLLocLib.c']
    for eid in e.event_id:
        paths += [G.BASE/'events_raw'/eid/'input.obs',G.BASE/'events_raw'/eid/'control.in']
    design=dict(intervention='Fixed 3D hybrid velocities; zero corrections; original observations/errors, receiver coordinates and search.',cohort='All 147 previously examined transfer events; not fresh confirmation. Pilot gamma_0001110 was examined during numerical implementation.',gates=dict(numerical='For each phase at baseline event coordinates: median |T3Dbackground-T2Doriginal|<=0.05s and p95<=0.10s, across ALL observed stations.',execution='All 588 new fits parsed and identity/timing checked; all original picks retained.',comparison='Candidate must pass against BOTH matched 3D background and archived original fine 2D baseline.',heldout='Same six stations, no origin adjustment: overall RMS <=0.95 baseline, P and S each <=1.05.',reference='Fixed identities, all horizontal and nominal Shelly absolute-depth medians <=1.10 baseline, at least one <=0.95.',depth='Near-bound count <=baseline+3; p90 conditional depth sigma <=1.10 baseline.',omission='Same held-out stations: horizontal/depth median and p90 displacement <=1.10 baseline.',retention='LOCATED count >=baseline in full and omitted fits.'),decision='All pass permits separately frozen confirmation only; no full adoption.',source_sha256={str(q):G.sha(q) for q in paths})
    d=OUT/'design.json'
    if d.exists():assert json.loads(d.read_text())==design
    else:G.write_json(d,design)
    return cfg,e,p,st,held

def tt(branch,p,st):
    if 'original' in branch:return S.DIAG.predict(G.BASE/'grids',p,st)[0]
    return G.predict(G.OUT/('regional' if 'regional' in branch else 'baseline'),p,st)

def numerical(e,p,st):
    assert json.loads((G.OUT/'pilot/run.json').read_text())['numerical_gate_pass']
    assert json.loads((G.OUT/'grid_run.json').read_text())['all_stations']
    verified={}
    for label in ['baseline','regional']:
        folder=G.OUT/label
        for station in st.nll_station:
            for phase in ['P','S']:
                marker=folder/f'{phase}_{station}.complete.json';m=json.loads(marker.read_text())
                buf=folder/f'time.{phase}.{station}.time.buf';hdr=buf.with_suffix('.hdr')
                assert G.sha(buf)==m['time_sha256'] and G.sha(hdr)==m['header_sha256']
                verified[str(buf)]={'time_sha256':m['time_sha256'],'header_sha256':m['header_sha256']}
    G.write_json(OUT/'verified_grid_inputs.json',verified)
    q=p.merge(e[['event_id']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
    q['difference_s']=tt('baseline',q,st)-tt('original',q,st)
    q.to_csv(OUT/'tables/numerical_checks.csv',index=False)
    checks=[]
    for phase,g in q.groupby('phase'):
        a=g.difference_s.abs();checks.append(dict(phase=phase,n=len(g),median_abs_s=float(a.median()),p95_abs_s=float(a.quantile(.95)),passed=bool(a.median()<=.05 and a.quantile(.95)<=.10)))
    G.write_json(OUT/'numerical_checks.json',checks)
    assert all(c['passed'] for c in checks),'Full-station numerical gate fails; do not locate or relax gate.'

def run(data,workers):
    cfg,e,p,st,held=data;numerical(e,p,st)
    groups={eid:g.to_dict('records') for eid,g in p.groupby('event_id')};rows=[];links=[];failures=[]
    S.OUT=OUT;S.write_json=G.write_json
    for label in ['baseline','regional']:
        proxy=OUT/('input_'+label);proxy.mkdir(exist_ok=True)
        for name,target in [('events_raw',G.BASE/'events_raw'),('grids',G.OUT/label)]:
            dest=proxy/name
            if not dest.exists():dest.symlink_to(target,target_is_directory=True)
            assert dest.resolve()==target.resolve()
        S.BASE=proxy
        with ThreadPoolExecutor(max_workers=workers) as pool:
            jobs={pool.submit(S.solve,event,groups[event['event_id']],branch,{},st.nll_station.to_dict(),cfg,held if branch.startswith('withheld_') else ()):(branch,event['event_id']) for branch in [label,'withheld_'+label] for event in e.to_dict('records')}
            for i,f in enumerate(as_completed(jobs),1):
                try:r,l=f.result();rows.append(r);links.extend(l)
                except Exception as exc:failures.append(dict(branch=jobs[f][0],event_id=jobs[f][1],error=repr(exc)));print('FAILED',failures[-1],flush=True)
                if i%20==0 or i==len(jobs):print(label,i,len(jobs),'failures',len(failures),flush=True)
    pd.DataFrame(rows).to_csv(OUT/'tables/events.csv',index=False);pd.DataFrame(links).to_csv(OUT/'tables/fit_phases.csv',index=False);pd.DataFrame(failures,columns=['branch','event_id','error']).to_csv(OUT/'tables/failures.csv',index=False)
    assert not failures and len(rows)==588


def report(data):
    cfg,cohort,p,st,held=data;e=pd.read_csv(OUT/'tables/events.csv');fp=pd.read_csv(OUT/'tables/fit_phases.csv');assert len(e)==588
    mapping={'control':'original','withheld_control':'withheld_original'}
    for name,target in [('events',e),('fit_phases',fp)]:
        old=pd.read_csv(HERE/f'export/20_velocity_model_qualification/tables/{name}.csv');old=old[old.branch.isin(mapping)].copy();old['branch']=old.branch.map(mapping)
        if name=='events':e=pd.concat([e,old],ignore_index=True)
        else:fp=pd.concat([fp,old],ignore_index=True)
    assert len(e)==882 and not e.duplicated(['branch','event_id']).any()
    hp=[];metrics=[];timing=[];om=[]
    for branch,g in e.groupby('branch'):
        f=fp[fp.branch.eq(branch)]
        expected=p[~p.instrument_id.isin(held)] if branch.startswith('withheld_') else p
        assert set(f.pick_id)==set(expected.pick_id) and f.pick_id.is_unique
        q=f.merge(p[['pick_id','time_utc']],on='pick_id',validate='one_to_one').merge(g[['event_id','origin_time']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
        pred=tt(branch,q,st);elapsed=(pd.to_datetime(q.time_utc,utc=True,format='ISO8601')-pd.to_datetime(q.origin_time,utc=True,format='ISO8601')).dt.total_seconds()
        err=float(np.max(np.abs(elapsed-pred-q.residual_s)));assert err<.00035,(branch,err)
        timing.append(dict(branch=branch,max_residual_equation_error_s=err))
        metrics.append(dict(branch=branch,located=int(g.status.eq('LOCATED').sum()),near_bound=int(((g.depth_km<.5)|(g.depth_km>24.5)).sum()),median_depth_km=g.depth_km.median(),p90_sigma_z_km=g.posterior_sigma_depth_km.quantile(.9),fit_rms_s=S.rms(f.residual_s)))
        if branch.startswith('withheld_'):
            q=p[p.instrument_id.isin(held)].merge(g[['event_id','origin_time']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True);q['branch']=branch;q['predicted_travel_time_s']=tt(branch,q,st);q['residual_s']=(pd.to_datetime(q.time_utc,utc=True,format='ISO8601')-pd.to_datetime(q.origin_time,utc=True,format='ISO8601')).dt.total_seconds()-q.predicted_travel_time_s;hp.append(q)
    hp=pd.concat(hp,ignore_index=True);hm=[]
    for branch,g in hp.groupby('branch'):
        for phase,q in [('all',g),('P',g[g.phase.eq('P')]),('S',g[g.phase.eq('S')])]:hm.append(dict(branch=branch,phase=phase,n=len(q),rms_s=S.rms(q.residual_s)))
    matches=pd.read_csv(HERE/'export/10_validate_catalog/reference_matches.csv');refs=pd.read_csv(HERE/'export/05_review_catalog/reference_events.csv');vectors=[];rs=[]
    common=set.intersection(*(set(e[e.branch.eq(b)&e.status.eq('LOCATED')].event_id) for b in ['original','baseline','regional']))
    m=matches[matches.event_id.isin(common)&matches.matched&~matches.ambiguous].merge(refs[['catalog','reference_id','latitude','longitude']],on=['catalog','reference_id'],validate='many_to_one')
    for branch in ['original','baseline','regional']:
        g=e[e.branch.eq(branch)].set_index('event_id').loc[m.event_id];rx,ry=S.PROJ(m.longitude.to_numpy(),m.latitude.to_numpy());v=m[['event_id','catalog','reference_id','reference_depth_km']].copy();v['branch']=branch;v['horizontal_km']=np.hypot(g.x_km.to_numpy()-rx,g.y_km.to_numpy()-ry);v['depth_difference_km']=np.where(m.catalog.eq('Shelly'),g.depth_km.to_numpy()-m.reference_depth_km,np.nan);vectors.append(v)
        for cat,q in v.groupby('catalog'):rs.append(dict(branch=branch,catalog=cat,n=len(q),median_horizontal_km=q.horizontal_km.median(),median_abs_depth_km=q.depth_difference_km.abs().median()))
        a=e[e.branch.eq(branch)].set_index('event_id');b=e[e.branch.eq('withheld_'+branch)].set_index('event_id').loc[a.index];h=np.hypot(b.x_km-a.x_km,b.y_km-a.y_km);z=(b.depth_km-a.depth_km).abs();om.append(dict(branch=branch,median_horizontal_km=h.median(),p90_horizontal_km=h.quantile(.9),median_depth_km=z.median(),p90_depth_km=z.quantile(.9)))
    metrics=pd.DataFrame(metrics);hm=pd.DataFrame(hm);rs=pd.DataFrame(rs);om=pd.DataFrame(om);decisions={}
    mt=metrics.set_index('branch');hr=hm.pivot(index='phase',columns='branch',values='rms_s');rr=rs.pivot(index='catalog',columns='branch',values='median_horizontal_km');dr=rs[rs.catalog.eq('Shelly')].set_index('branch').median_abs_depth_km;oo=om.set_index('branch')
    for base in ['original','baseline']:
        ratios=(rr.regional/rr[base]).to_dict();ratios['Shelly_depth']=float(dr.regional/dr[base]);oratio=(oo.loc['regional']/oo.loc[base]).to_dict()
        gates=dict(execution=True,retention=bool(all(mt.loc[b,'located']>=mt.loc[a,'located'] for a,b in [(base,'regional'),('withheld_'+base,'withheld_regional')])),heldout=bool(hr.loc['all','withheld_regional']<=.95*hr.loc['all','withheld_'+base] and all(hr.loc[p,'withheld_regional']<=1.05*hr.loc[p,'withheld_'+base] for p in ['P','S'])),reference=bool(all(x<=1.10 for x in ratios.values())),reference_gain=bool(any(x<=.95 for x in ratios.values())),depth_bounds=bool(mt.loc['regional','near_bound']<=mt.loc[base,'near_bound']+3),posterior=bool(mt.loc['regional','p90_sigma_z_km']<=1.10*mt.loc[base,'p90_sigma_z_km']),omission_stability=bool(all(x<=1.10 for x in oratio.values())))
        decisions[base]=dict(gates=gates,reference_ratios=ratios,omission_ratios=oratio,heldout_rms_ratio=float(hr.loc['all','withheld_regional']/hr.loc['all','withheld_'+base]))
    result=dict(round=9,decision='eligible_for_separate_confirmation' if all(all(v['gates'].values()) for v in decisions.values()) else 'do_not_promote',comparisons=decisions)
    for name,df in dict(metrics=metrics,heldout_metrics=hm,heldout_predictions=hp,reference_pairs=pd.concat(vectors,ignore_index=True),reference_summary=rs,omission_summary=om,timing_checks=pd.DataFrame(timing)).items():df.to_csv(OUT/f'tables/{name}.csv',index=False)
    G.write_json(OUT/'run.json',result)
    table=lambda df:df.to_string(index=False,float_format=lambda v:f'{v:.5f}')
    (OUT/'README.md').write_text('# Fixed 3D hybrid velocity comparison\n\nDecision: **'+result['decision']+'**. The same 147 examined transfer events and all original observations are retained. New regional and matched 3D background fits are compared with each other and the archived fine 2D baseline. No corrections, reference fitting, repicking or rematching. Mainshock uncertainty remains outside this ordinary-event pilot.\n\nLocations:\n```text\n'+table(metrics)+'\n```\n\nSame six-station held-out arrivals, no origin recentering:\n```text\n'+table(hm)+'\n```\n\nFixed reference comparisons (only Shelly depth nominally comparable):\n```text\n'+table(rs)+'\n```\n\nConditional posterior widths do not include model error. Full numerical checks, input hashes, native fits and residual equations are retained. See run.json for every fixed decision gate. A successful transfer comparison permits a new confirmation experiment, not full catalog adoption.\n')
    print(json.dumps(result,indent=2),flush=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',choices=['prepare','run','report','all'],default='all');ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    import fcntl
    OUT.mkdir(exist_ok=True)
    with (OUT/'run.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);data=prepare()
        if a.stage in ['run','all']:run(data,a.workers)
        if a.stage in ['report','all']:report(data)
if __name__=='__main__':main()
