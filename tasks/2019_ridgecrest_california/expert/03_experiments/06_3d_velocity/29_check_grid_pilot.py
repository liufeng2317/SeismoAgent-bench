#!/usr/bin/env python3
"""Check matched 3D grids and locate a frozen pilot; never promote a catalog."""
import argparse, importlib.util, json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
HERE=Path(__file__).resolve().parents[2]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
G=load('grid29',Path(__file__).with_name('29_build_3d_grids.py'))
S=load('station29',HERE/'03_experiments/03_station_corrections/17_test_station_corrections.py')
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--spacing',type=float,default=1.);args=ap.parse_args();G.configure(args.spacing)
    out=G.OUT/'pilot';out.mkdir(exist_ok=True)
    design={'scope':'Fixed single-event numerical and location pilot, not a catalog qualification', 'numerical_gate':'At original transfer locations, each phase median absolute 3D baseline minus original 2D travel time <=0.05 s and p95 <=0.10 s; only stations selected by the fixed pilot are available.', 'sources':{str(p):G.sha(p) for p in [Path(__file__),Path(G.__file__)]}}
    f=out/'design.json'
    if f.exists():assert json.loads(f.read_text())==design
    else:G.write_json(f,design)
    e=pd.read_csv(HERE/'export/15_validate_transfer/inputs/events.csv')
    p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv',keep_default_na=False);p['residual_s']=p.residual_s_gamma
    eid=json.loads((G.OUT/'grid_run.json').read_text())['pilot_event']
    stations=pd.read_csv(G.BASE/'stations.csv').set_index('id')
    used=p.loc[p.event_id.eq(eid),'instrument_id'].unique()
    q=p[p.event_id.isin(e.event_id)&p.instrument_id.isin(used)].merge(e[['event_id','x_km','y_km','depth_km']],on='event_id',validate='many_to_one').reset_index(drop=True)
    q['baseline_2d_s']=S.DIAG.predict(G.BASE/'grids',q,stations)[0]
    q['baseline_3d_s']=G.predict(G.OUT/'baseline',q,stations)
    q['difference_s']=q.baseline_3d_s-q.baseline_2d_s
    q.to_csv(out/'travel_time_checks.csv',index=False)
    metrics=[]
    for phase,t in q.groupby('phase'):
        d=t.difference_s.abs();metrics.append({'phase':phase,'count':len(t),'median_abs_s':float(d.median()),'p95_abs_s':float(d.quantile(.95)),'pass':bool(d.median()<=.05 and d.quantile(.95)<=.1)})
    print('Numerical checks:',metrics,flush=True)
    # Original native controls and observation identities; only travel-time prefix changes.
    event=e[e.event_id.eq(eid)].iloc[0].to_dict();obs=p[p.event_id.eq(eid)].to_dict('records')
    cfg=yaml.safe_load((HERE/'00_config/nonlinloc.yaml').read_text());aliases=stations.nll_station.to_dict()
    rows=[];links=[]
    for label in ['baseline','regional']:
        proxy=out/('input_'+label);proxy.mkdir(exist_ok=True)
        for name,target in [('events_raw',G.BASE/'events_raw'),('grids',G.OUT/label)]:
            dest=proxy/name
            if not dest.exists():dest.symlink_to(target,target_is_directory=True)
            assert dest.resolve()==target.resolve()
        S.BASE=proxy;S.OUT=out
        row,ph=S.solve(event,obs,label,{},aliases,cfg);rows.append(row);links.extend(ph)
        print(label,row['status'],row['depth_km'],row['rms_unweighted_s'],flush=True)
    r=pd.DataFrame(rows);l=pd.DataFrame(links)
    errors=[]
    for label in ['baseline','regional']:
        t=l[l.branch.eq(label)].merge(r[r.branch.eq(label)][['event_id','origin_time','x_km','y_km','depth_km']],on='event_id').merge(p[['pick_id','time_utc']],on='pick_id').reset_index(drop=True)
        tt=G.predict(G.OUT/label,t,stations)
        elapsed=(pd.to_datetime(t.time_utc,utc=True)-pd.to_datetime(t.origin_time,utc=True)).dt.total_seconds().to_numpy()
        err=float(np.max(np.abs(tt-t.predicted_travel_time_s)));res=float(np.max(np.abs(elapsed-tt-t.residual_s)))
        assert max(err,res)<.00035,(label,err,res)
        errors.append({'model':label,'max_tt_error_s':err,'max_residual_equation_error_s':res})
    r.to_csv(out/'events.csv',index=False);l.to_csv(out/'phases.csv',index=False)
    result={'numerical_checks':metrics,'numerical_gate_pass':all(m['pass'] for m in metrics),'native_interpolation_checks':errors,'pilot_event':eid,'status':'pilot_only_not_catalog_improvement'}
    G.write_json(out/'run.json',result)
    (out/'README.md').write_text('# Matched 3D grid pilot\n\nTwo actual NonLinLoc fits with identical observations and controls, using matched baseline and regional hybrid grids. No station delays.\n\nNumerical gate: '+str(result['numerical_gate_pass'])+'. The original fine 2D baseline is checked separately at transfer-event locations for the pilot stations. See travel_time_checks.csv and run.json. A single event cannot establish improved location accuracy. Do not adopt this as a catalog.\n')
    print(json.dumps(result),flush=True)
if __name__=='__main__':main()
