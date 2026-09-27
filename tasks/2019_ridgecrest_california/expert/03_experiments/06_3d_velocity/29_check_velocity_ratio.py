#!/usr/bin/env python3
"""Bounded first-order counterfactual; no new locations or reference fitting."""
from pathlib import Path
import importlib.util
import json
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('regional_grid',Path(__file__).with_name('29_build_3d_grids.py'));G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G);G.configure(.25)
OUT=HERE/'export/29_3d_velocity/transfer'
XYZ=['x_km','y_km','depth_km']
def main():
    e=pd.read_csv(OUT/'tables/events.csv');e=e[e.branch.eq('regional')]
    p=pd.read_csv(HERE/'export/10_validate_catalog/phases.csv');p=p[p.event_id.isin(e.event_id)].merge(e[['event_id']+XYZ],on='event_id',validate='many_to_one').reset_index(drop=True)
    st=pd.read_csv(G.BASE/'stations.csv').set_index('id')
    def old(q):return G.predict(G.OUT/'regional',q,st)
    def new(q):
        qp=q.copy();qp['phase']='P';return old(qp)*np.where(q.phase.eq('S'),1.73,1.)
    delta=new(p)-old(p)
    jac=[];step=.05
    for col in XYZ:
        a=p.copy();b=p.copy();a[col]+=step;b[col]-=step
        jac.append((new(a)-new(b))/(2*step))
    J=np.column_stack(jac+[np.ones(len(p))]);w=1/(.3**2+np.where(p.phase.eq('P'),.1,.2)**2)
    rows=[]
    for eid,q in p.groupby('event_id'):
        idx=q.index.to_numpy();A=J[idx]*np.sqrt(w[idx,None]);rhs=-delta[idx]*np.sqrt(w[idx]);dx,_,rank,singular=np.linalg.lstsq(A,rhs,rcond=None)
        assert rank==4
        rows.append(dict(event_id=eid,predicted_dx_km=dx[0],predicted_dy_km=dx[1],predicted_depth_change_km=dx[2],predicted_origin_change_s=dx[3],jacobian_condition_number=singular[0]/singular[-1]))
    r=pd.DataFrame(rows);r.to_csv(OUT/'tables/constant_vpvs_first_order.csv',index=False)
    p[['event_id','pick_id','phase','instrument_id']].assign(candidate_minus_regional_tt_s=delta).to_csv(OUT/'tables/constant_vpvs_time_changes.csv',index=False)
    result=dict(scope='First-order only, at regional locations, fixed Vp and candidate Vs=Vp/1.73. No new inversion and no reference fitting. Source gradients are central differences at 0.05km; original inverse observation-plus-model variances; free origin.',n_events=len(r),median_predicted_depth_change_km=float(r.predicted_depth_change_km.median()),p10_predicted_depth_change_km=float(r.predicted_depth_change_km.quantile(.1)),p90_predicted_depth_change_km=float(r.predicted_depth_change_km.quantile(.9)),median_S_travel_time_change_s=float(np.median(delta[p.phase.eq('S')])),median_horizontal_change_km=float(np.median(np.hypot(r.predicted_dx_km,r.predicted_dy_km))),code_sha256=G.sha(Path(__file__)))
    G.write_json(OUT/'constant_vpvs_first_order.json',result);print(json.dumps(result,indent=2),flush=True)
if __name__=='__main__':main()
