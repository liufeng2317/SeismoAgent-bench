#!/usr/bin/env python3
"""Fixed-pick depth profiles and one controlled velocity-interpolation experiment."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse
import hashlib
import json
import subprocess
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import yaml
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]  # Expert root; independent of working directory.
OUT=HERE/'export/06_diagnose_depth'
NLL=HERE/'export/04_locate_nonlinloc'
GAMMA=HERE/'export/03_associate_gamma/full'
GRIDS={}


def initialize(directory, config, bounds):
    global GRIDS, CFG, BOUNDS, SHAPE, STEP, TOP
    CFG=config;BOUNDS=bounds;GRIDS={}
    for path in Path(directory).glob('time.*.time.hdr'):
        fields=path.read_text().splitlines()[0].split()
        ny,nz=int(fields[1]),int(fields[2]);STEP=float(fields[7]);TOP=float(fields[5]);SHAPE=(ny,nz)
        GRIDS['.'.join(path.name.split('.')[1:3])]=np.fromfile(path.with_suffix('.buf'),dtype=np.float32,count=ny*nz).reshape(ny,nz).astype(float)


class Problem:
    def __init__(self, job):
        self.job=job
        self.arrays=np.stack([GRIDS[k] for k in job['keys']])
        self.station=np.array(job['stations']);self.observed=np.array(job['observed'])
        self.w=np.array([1/(CFG['model_error_s']**2+CFG['pick_error_s'][p]**2) for p in job['phases']])
        self.index=np.arange(len(self.w))

    def travel(self, xyz):
        delta=xyz[:2]-self.station[:,:2];r=np.linalg.norm(delta,axis=1)
        ur=r/STEP;uz=(xyz[2]-TOP)/STEP
        ir=np.floor(ur).astype(int);iz=int(np.floor(uz))
        if np.any(ir<0) or np.any(ir>=SHAPE[0]-1) or iz<0 or iz>=SHAPE[1]-1:
            raise ValueError('Location outside a travel-time grid')
        a=ur-ir;b=uz-iz
        t00=self.arrays[self.index,ir,iz];t10=self.arrays[self.index,ir+1,iz]
        t01=self.arrays[self.index,ir,iz+1];t11=self.arrays[self.index,ir+1,iz+1]
        tt=(1-a)*((1-b)*t00+b*t01)+a*((1-b)*t10+b*t11)
        dr=((1-b)*(t10-t00)+b*(t11-t01))/STEP
        dz=((1-a)*(t01-t00)+a*(t11-t10))/STEP
        grad=np.column_stack([dr[:,None]*delta/np.maximum(r[:,None],1e-12),dz])
        return tt,grad

    def evaluate(self, xyz):
        tt,grad=self.travel(np.asarray(xyz))
        origin=np.average(self.observed-tt,weights=self.w)
        residual=self.observed-origin-tt
        loss=float(np.dot(self.w,residual**2))
        gradient=-2*(self.w*residual)@grad
        return loss,gradient,origin,residual,tt

    def optimize(self, starts, depth=None):
        best=None;successful=0
        for start in starts:
            start=np.asarray(start,dtype=float)
            def fun(v):
                xyz=v if depth is None else np.r_[v,depth]
                loss,gradient,*_=self.evaluate(xyz)
                return loss,gradient if depth is None else gradient[:2]
            initial=start if depth is None else start[:2]
            result=minimize(fun,initial,jac=True,bounds=BOUNDS if depth is None else BOUNDS[:2],
                            method='L-BFGS-B',options={'maxiter':250,'ftol':1e-11,'gtol':1e-6,'maxls':40})
            successful+=int(result.success)
            # Always retain a better seed even if an optimizer terminates poorly.
            for candidate in [initial,result.x]:
                xyz=candidate if depth is None else np.r_[candidate,depth]
                loss=self.evaluate(xyz)[0]
                if best is None or loss<best[0]:best=(loss,xyz.copy())
        return best[1],successful


def solve(job):
    p=Problem(job);g=np.array(job['gamma_xyz']);n=np.array(job['nll_xyz'])
    seeds=[g,n]+[np.r_[xy,z] for xy in [g[:2],n[:2]] for z in [0.,2.,5.,10.,15.,20.,25.]]
    xyz,success=p.optimize(seeds)
    profiles=[]
    if job['role']=='diagnostic':
        previous=xyz
        for depth in np.arange(0,25+CFG['profile_step_km']/2,CFG['profile_step_km']):
            point,ok=p.optimize([g,n,xyz,previous],depth)
            loss,_,origin,residual,_=p.evaluate(point)
            profiles.append(dict(event_id=job['event_id'],depth_km=depth,chi2=loss,
                                 x_km=point[0],y_km=point[1],origin_offset_s=origin,
                                 rms_s=float(np.sqrt(np.mean(residual**2))),successful_starts=ok))
            previous=point
        best_profile=min(profiles,key=lambda r:r['chi2'])
        candidate,ok=p.optimize([xyz,[best_profile['x_km'],best_profile['y_km'],best_profile['depth_km']]])
        if p.evaluate(candidate)[0]<p.evaluate(xyz)[0]:xyz=candidate
        success+=ok
    loss,_,origin,residual,tt=p.evaluate(xyz)
    gl,_,go,gr,_=p.evaluate(g);nl,_,no,nr,nt=p.evaluate(n)
    row=dict(event_id=job['event_id'],role=job['role'],stratum=job['stratum'],n_picks=len(residual),
             gamma_common_chi2=gl,nll_common_chi2=nl,refined_chi2=loss,
             gamma_common_rms_s=float(np.sqrt(np.mean(gr**2))),nll_common_rms_s=float(np.sqrt(np.mean(nr**2))),
             refined_rms_s=float(np.sqrt(np.mean(residual**2))),
             x_km=xyz[0],y_km=xyz[1],depth_km=xyz[2],origin_anchor=job['anchor'],origin_offset_s=origin,
             gamma_origin_refit_s=go-job['gamma_origin_offset'],nll_origin_refit_s=no-job['nll_origin_offset'],
             gamma_depth_km=g[2],nll_depth_km=n[2],nll_to_refined_horizontal_km=float(np.linalg.norm(xyz[:2]-n[:2])),
             nll_to_refined_depth_km=float(xyz[2]-n[2]),nll_chi2_improvement=nl-loss,
             native_tt_max_difference_s=float(np.max(np.abs(nt-np.array(job['native_tt'])))),successful_starts=success)
    if profiles:
        support=[r['depth_km'] for r in profiles if r['chi2']-loss<=CFG['profile_support_delta_chi2']]
        row.update(profile_support_min_km=min(support) if support else np.nan,
                   profile_support_max_km=max(support) if support else np.nan)
    phase_rows=[]
    for i,r in enumerate(residual):
        phase_rows.append(dict(event_id=job['event_id'],pick_id=job['pick_ids'][i],instrument_id=job['instruments'][i],phase=job['phases'][i],
                               distance_km=float(np.linalg.norm(xyz[:2]-p.station[i,:2])),residual_s=r,
                               predicted_travel_time_s=tt[i],weight=p.w[i]))
    return row,profiles,phase_rows


def setup():
    OUT.mkdir(exist_ok=True)
    cfg=yaml.safe_load((HERE/'00_config/depth_diagnostic.yaml').read_text())
    e=pd.read_csv(NLL/'full/events.csv');g=pd.read_csv(GAMMA/'events.csv').set_index('event_id')
    review=pd.read_csv(HERE/'export/05_review_catalog/event_quality.csv',keep_default_na=False)
    examples=pd.read_csv(HERE/'export/05_review_catalog/examples.csv')
    selection_path=OUT/'selection.csv'
    if not selection_path.exists():
        selected=[dict(event_id=r.event_id,role='diagnostic',stratum=r.reason) for r in examples.itertuples()]
        candidates=review[~review.event_id.isin(examples.event_id)].copy()
        candidates['stratum']=np.select([
            candidates.provisional_quality.eq('association_review'),
            candidates.depth_km.lt(.5),
            candidates.provisional_quality.eq('location_review')],['association_review','shallow','other_location_review'],default='provisionally_usable')
        rng=np.random.default_rng(cfg['validation_seed'])
        for name,group in candidates.groupby('stratum',sort=True):
            ids=group.sort_values('event_id').event_id.to_numpy()
            for eid in sorted(rng.choice(ids,cfg['validation_per_stratum'],replace=False)):
                selected.append(dict(event_id=eid,role='validation',stratum=name))
        pd.DataFrame(selected).to_csv(selection_path,index=False)
    selection=pd.read_csv(selection_path)
    assert len(selection)==108 and selection.event_id.is_unique
    picks=pd.read_csv(GAMMA/'picks.csv',keep_default_na=False)
    picks=picks[picks.event_id.isin(selection.event_id)]
    native=pd.read_csv(NLL/'full/picks.csv').set_index('pick_id')
    stations=pd.read_csv(NLL/'stations.csv').set_index('id')
    old=json.loads((NLL/'inputs.json').read_text());bounds=old['association_inputs']['gamma_config']['bfgs_bounds'][:3]
    jobs=[]
    for sample in selection.itertuples():
        n=e[e.event_id.eq(sample.event_id)].iloc[0];gg=g.loc[sample.event_id]
        pp=picks[picks.event_id.eq(sample.event_id)].sort_values('pick_id')
        times=pd.to_datetime(pp.time_utc,utc=True,format='ISO8601')
        anchor=times.min();ns=times.astype('int64').to_numpy()-anchor.value
        jobs.append(dict(event_id=sample.event_id,role=sample.role,stratum=sample.stratum,
                         gamma_xyz=gg[['x_km','y_km','depth_km']].tolist(),nll_xyz=n[['x_km','y_km','depth_km']].tolist(),
                         gamma_origin_offset=(pd.Timestamp(gg.origin_time)-anchor).total_seconds(),
                         nll_origin_offset=(pd.Timestamp(n.origin_time)-anchor).total_seconds(),
                         anchor=anchor.isoformat(),observed=(ns/1e9).tolist(),pick_ids=pp.pick_id.tolist(),
                         phases=pp.phase.tolist(),instruments=pp.instrument_id.tolist(),
                         keys=[r.phase+'.'+stations.loc[r.instrument_id,'nll_station'] for r in pp.itertuples()],
                         stations=stations.loc[pp.instrument_id,['x(km)','y(km)','z(km)']].to_numpy().tolist(),
                         native_tt=native.loc[pp.pick_id,'predicted_travel_time_s'].tolist()))
    sources=[HERE/'00_config/depth_diagnostic.yaml',Path(__file__),selection_path,NLL/'inputs.json',NLL/'full/events.csv',NLL/'full/picks.csv',GAMMA/'events.csv',GAMMA/'picks.csv',NLL/'stations.csv']
    record={'settings':cfg,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}}
    marker=OUT/'inputs.json';text=json.dumps(record,indent=2,sort_keys=True)
    if marker.exists() and marker.read_text()!=text:raise ValueError('Experiment inputs/code changed; preserve previous results before rerunning')
    marker.write_text(text)
    return cfg,bounds,jobs


def run(jobs,directory,cfg,bounds,label):
    out=OUT/label;out.mkdir(exist_ok=True)
    results=[];profiles=[];picks=[]
    with ProcessPoolExecutor(max_workers=cfg['workers'],initializer=initialize,initargs=(str(directory),cfg,bounds)) as pool:
        futures=[pool.submit(solve,j) for j in jobs]
        for i,f in enumerate(as_completed(futures),1):
            r,pp,ph=f.result();results.append(r);profiles+=pp;picks+=ph
            if i%10==0 or i==len(jobs):print(label,i,'/',len(jobs),flush=True)
    result=pd.DataFrame(results).sort_values('event_id')
    assert np.isfinite(result[['refined_chi2','x_km','y_km','depth_km']]).all().all()
    assert (result.refined_chi2<=result[['gamma_common_chi2','nll_common_chi2']].min(axis=1)+1e-7).all()
    assert result.successful_starts.gt(0).all()
    if label=='linear':assert result.native_tt_max_difference_s.max()<.0003
    result.to_csv(out/'events.csv',index=False)
    pd.DataFrame(profiles).to_csv(out/'depth_profiles.csv',index=False)
    phases=pd.DataFrame(picks).sort_values('pick_id');assert phases.pick_id.is_unique
    phases.to_csv(out/'picks.csv',index=False)
    return result


def layered_grids():
    directory=OUT/'layered_grids';directory.mkdir(exist_ok=True)
    for phase in ['P','S']:
        lines=[]
        for line in (NLL/'grids'/f'{phase}.in').read_text().splitlines():
            if line.startswith('LAYER '):
                fields=line.split();fields[3]='0';fields[5]='0';line=' '.join(fields)
            lines.append(line)
        control=directory/f'{phase}.in';control.write_text('\n'.join(lines)+'\n')
        for binary in ['Vel2Grid','Grid2Time']:
            with (directory/f'{phase}_{binary}.log').open('w') as log:
                subprocess.run(['/liufeng1afs/software/NLLoc/NLL7.00_src/src/'+binary,control.name],cwd=directory,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
        print('Layered grids ready:',phase,flush=True)
    assert len(list(directory.glob('time.*.time.buf')))==74
    return directory


def plot_and_compare():
    a=pd.read_csv(OUT/'linear/events.csv');b=pd.read_csv(OUT/'layered/events.csv')
    c=a.merge(b,on=['event_id','role','stratum'],suffixes=('_linear','_layered'),validate='one_to_one')
    c['chi2_change']=c.refined_chi2_layered-c.refined_chi2_linear
    c['rms_change_s']=c.refined_rms_s_layered-c.refined_rms_s_linear
    c['horizontal_change_km']=np.hypot(c.x_km_layered-c.x_km_linear,c.y_km_layered-c.y_km_linear)
    c['depth_change_km']=c.depth_km_layered-c.depth_km_linear
    c.to_csv(OUT/'comparison.csv',index=False)
    profiles={name:pd.read_csv(OUT/name/'depth_profiles.csv') for name in ['linear','layered']}
    examples=pd.read_csv(HERE/'export/05_review_catalog/examples.csv')
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,4,figsize=(12,6),layout='constrained')
    for ax,r in zip(axes.flat,examples.itertuples()):
        minimum=min(c.loc[c.event_id.eq(r.event_id),'refined_chi2_linear'].iloc[0],c.loc[c.event_id.eq(r.event_id),'refined_chi2_layered'].iloc[0])
        for name,color in [('linear','#0072B2'),('layered','#D55E00')]:
            p=profiles[name];p=p[p.event_id.eq(r.event_id)].sort_values('depth_km')
            ax.plot(p.depth_km,p.chi2-minimum,c=color,label=name.capitalize())
        ax.set(title=r.event_id,xlabel='Depth (km)',ylabel='Δχ² (common minimum)',xlim=(0,25))
        ax.set_yscale('symlog',linthresh=1)
        ax.set_ylim(bottom=0)
    axes.flat[0].legend(frameon=False)
    for ext in ['png','pdf']:fig.savefig(OUT/f'depth_profiles.{ext}',dpi=220)
    plt.close(fig)
    rows=[]
    for (role,stratum),part in c.groupby(['role','stratum']):
        rows.append(dict(role=role,stratum=stratum,n=len(part),median_rms_linear_s=part.refined_rms_s_linear.median(),
                         median_rms_layered_s=part.refined_rms_s_layered.median(),
                         chi2_improved=int(part.chi2_change.lt(-1e-6).sum()),
                         shallow_linear=int(part.depth_km_linear.lt(.5).sum()),shallow_layered=int(part.depth_km_layered.lt(.5).sum()),
                         median_horizontal_change_km=part.horizontal_change_km.median()))
    pd.DataFrame(rows).to_csv(OUT/'summary.csv',index=False)
    print(pd.DataFrame(rows).to_string(index=False),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',choices=['diagnose','control','validate','report'],required=True)
    args=ap.parse_args();cfg,bounds,jobs=setup()
    if args.stage=='diagnose':run([j for j in jobs if j['role']=='diagnostic'],NLL/'grids',cfg,bounds,'linear')
    elif args.stage=='control':run([j for j in jobs if j['role']=='diagnostic'],layered_grids(),cfg,bounds,'layered')
    elif args.stage=='validate':
        for label,directory in [('linear',NLL/'grids'),('layered',OUT/'layered_grids')]:
            run(jobs,directory,cfg,bounds,label)
    else:plot_and_compare()


if __name__=='__main__':main()
