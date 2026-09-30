"""Fixed 147-event transfer metrics; extracted from the verified stage29 report.

Case-specific shared code; does not modify historical stage29 outputs.
"""
import json
import numpy as np
import pandas as pd

def report(data, *, out, here, native, predict, write_json, round_id, title):
    OUT, HERE, S, tt, XYZ = out, here, native, predict, native.XYZ
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
    result=dict(round=round_id,decision='eligible_for_separate_confirmation' if all(all(v['gates'].values()) for v in decisions.values()) else 'do_not_promote',comparisons=decisions)
    for name,df in dict(metrics=metrics,heldout_metrics=hm,heldout_predictions=hp,reference_pairs=pd.concat(vectors,ignore_index=True),reference_summary=rs,omission_summary=om,timing_checks=pd.DataFrame(timing)).items():df.to_csv(OUT/f'tables/{name}.csv',index=False)
    write_json(OUT/'run.json',result)
    table=lambda df:df.to_string(index=False,float_format=lambda v:f'{v:.5f}')
    (OUT/'README.md').write_text('# '+title+'\n\nDecision: **'+result['decision']+'**. The same 147 examined transfer events and all original observations are retained. New regional and matched 3D background fits are compared with each other and the archived fine 2D baseline. No corrections, reference fitting, repicking or rematching. Mainshock uncertainty remains outside this ordinary-event pilot.\n\nLocations:\n```text\n'+table(metrics)+'\n```\n\nSame six-station held-out arrivals, no origin recentering:\n```text\n'+table(hm)+'\n```\n\nFixed reference comparisons (only Shelly depth nominally comparable):\n```text\n'+table(rs)+'\n```\n\nConditional posterior widths do not include model error. Full numerical checks, input hashes, native fits and residual equations are retained. See run.json for every fixed decision gate. A successful transfer comparison permits a new confirmation experiment, not full catalog adoption.\n')
    print(json.dumps(result,indent=2),flush=True)
