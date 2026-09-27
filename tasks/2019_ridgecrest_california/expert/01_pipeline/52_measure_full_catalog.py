"""Expand fixed scalar-P/vector-S measurements, reusing immutable waveform windows."""
from pathlib import Path
import importlib.util
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / 'export/52_full_catalog'
WORK = OUT / 'cc_processing'

def load(name, path):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m

SC = load('full52_scalar', HERE/'03_experiments/02_relative_location/13_hypodd_cc_pilot.py')
H = load('full52_vector', HERE/'03_experiments/07_joint_location/_cc_measurements.py')
WINDOWS = {}; META = {}; PICKS = {}


def fast_curve(a, b, limit):
    a = np.atleast_2d(np.asarray(a, float)).copy()
    b = np.atleast_2d(np.asarray(b, float)).copy()
    assert a.shape == b.shape
    a -= a.mean(axis=1, keepdims=True); b -= b.mean(axis=1, keepdims=True)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if min(na, nb) < 1e-20: raise ValueError('Zero signal')
    a /= na; b /= nb
    values = sum(np.correlate(y, x, mode='full') for x, y in zip(a, b))
    center = a.shape[1]-1
    return np.arange(-limit, limit+1), values[center-limit:center+limit+1]


def measure(row):
    a, b, phase = row.pick_id_a, row.pick_id_b, row.phase
    out = {'accepted': False, 'reason': 'missing_window', 'lag_s': np.nan, 'cc': np.nan, 'cc_arrival_difference_s': np.nan}
    seeds = sorted(set(PICKS[a]) & set(PICKS[b]))
    seeds = [s for s in seeds if (phase == 'P') == s.endswith('Z')]
    if len(seeds) != (1 if phase == 'P' else 2): return out
    if not all((p,s) in META and META[p,s]['status']=='ok' and p+'|'+s in WINDOWS for p in [a,b] for s in seeds): return out
    try:
        lags=[]; peaks=[]; margins=[]; snrs=[]; boundary=False
        limit = 30 if phase == 'P' else 40
        for band, sn in [(0,'snr_primary'),(1,'snr_check')]:
            av=np.stack([WINDOWS[a+'|'+s][band] for s in seeds]).astype(float)
            bv=np.stack([WINDOWS[b+'|'+s][band] for s in seeds]).astype(float)
            sa=np.array([META[a,s][sn] for s in seeds]); sb=np.array([META[b,s][sn] for s in seeds])
            if phase=='S':
                snrs.extend([np.sqrt(np.mean(sa**2)),np.sqrt(np.mean(sb**2))])
                av=H.whiten(av,sa); bv=H.whiten(bv,sb)
            else: snrs.extend([sa[0],sb[0]])
            ls,curve=fast_curve(av,bv,limit); best=int(np.argmax(abs(curve)))
            lags.append(ls[best]/100); peaks.append(curve[best]); margins.append(curve[best]-np.max(abs(curve[abs(ls-ls[best])>8])))
            boundary |= abs(ls[best])>=limit-1
        reasons=[]
        if min(snrs)<2: reasons.append('low_snr')
        if min(peaks)<.75: reasons.append('low_or_negative_cc')
        if min(margins)<.08: reasons.append('ambiguous_peak')
        if boundary: reasons.append('lag_boundary')
        if abs(lags[0]-lags[1])>.020001: reasons.append('band_instability')
        out['reason']=';'.join(reasons) or 'accepted'
        if not reasons: out.update(accepted=True,lag_s=float(lags[0]),cc=float(peaks[0]),cc_arrival_difference_s=float(row.observed_dt_s-lags[0]))
    except ValueError: out['reason']='invalid_signal_or_noise'
    return out


def extract_job(job):
    return SC.extract_file(job)


def batch(rows):
    return [measure(r) for r in rows]


def main():
    global WINDOWS,META,PICKS
    WORK.mkdir(exist_ok=True)
    rng=np.random.default_rng(52)
    for channels in [1,2]:
        for _ in range(10):
            a=rng.normal(size=(channels,181));b=rng.normal(size=a.shape)
            ls,v=fast_curve(a,b,40); l0,v0=H.curve(a,b,40)
            assert np.array_equal(ls,l0) and np.allclose(v,v0,rtol=0,atol=1e-14)
    t=np.arange(181)/100; a=np.exp(-((t-.6)/.06)**2)*np.cos(2*np.pi*6*(t-.6));b=np.exp(-((t-.67)/.06)**2)*np.cos(2*np.pi*6*(t-.67))
    ls,v=fast_curve(a,b,40); assert ls[np.argmax(v)]==7
    picks=pd.read_csv(OUT/'inputs/picks.csv',low_memory=False)
    PICKS={r.pick_id:r.source_channels.split(';') for r in picks.itertuples()}
    wanted=set(PICKS)
    stages=['35_cc_observation_selection','39_support_aware_pairs','42_vertical_p_observations','44_missing_p_observations','45_added_station','47_missing_s_observations','48_differential_augmentation/refreshed','50_uncertain_depth_pairs','51_confirmation']
    reused=[]
    for stage in stages:
        root=HERE/'export'/stage/'cc_processing'
        if not (root/'cc_windows.npz').exists(): continue
        meta=pd.read_csv(root/'waveform_windows.csv');meta=meta[meta.pick_id.isin(wanted)]
        cache=H.load_windows(root/'cc_windows.npz')
        for key,value in cache.items():
            if key.split('|')[0] not in wanted: continue
            if key in WINDOWS: assert np.array_equal(WINDOWS[key],value),key
            else: WINDOWS[key]=value
        for r in meta.to_dict('records'):
            key=(r['pick_id'],r['seed_id'])
            if key not in META or r['status']=='ok':META[key]=r
        reused.append(str(root)); print('Loaded windows:',stage,len(WINDOWS),flush=True)
    if (WORK/'new_windows.npz').exists():
        WINDOWS.update(H.load_windows(WORK/'new_windows.npz'))
        for r in pd.read_csv(WORK/'new_windows.csv').to_dict('records'): META[r['pick_id'],r['seed_id']]=r
    manifest=pd.read_csv(HERE/'export/45_added_station/waveform_inputs.csv')
    files={(r.seed_id,Path(r.path).name.split('__')[1][:8]):r.path for r in manifest.itertuples()}
    jobs={}; early=[]
    for r in picks.itertuples():
        t=pd.Timestamp(r.time_utc)
        for seed in PICKS[r.pick_id]:
            if (r.phase=='P') != seed.endswith('Z') or (r.pick_id,seed) in META: continue
            path=files.get((seed,t.strftime('%Y%m%d')))
            if not (pd.Timestamp('2019-07-04T00:00:10Z')<=t<pd.Timestamp('2019-07-06T23:59:50Z')) or path is None:
                early.append(dict(pick_id=r.pick_id,seed_id=seed,status='outside_window_or_missing_file')); continue
            jobs.setdefault(path,[]).append((r.pick_id,seed,r.phase,r.time_utc))
    new={}; audit=list(early)
    print('Extract new waveform windows:',sum(map(len,jobs.values())),'from',len(jobs),'files',flush=True)
    with ProcessPoolExecutor(max_workers=12,mp_context=mp.get_context('fork')) as pool:
        futures=[pool.submit(extract_job,j) for j in jobs.items()]
        for n,f in enumerate(as_completed(futures),1):
            data,rows=f.result();new.update(data);audit.extend(rows)
            if n%20==0 or n==len(futures):print('Waveform files',n,'/',len(futures),flush=True)
    if audit:
        oldmeta=pd.read_csv(WORK/'new_windows.csv').to_dict('records') if (WORK/'new_windows.csv').exists() else []
        oldwin=H.load_windows(WORK/'new_windows.npz') if (WORK/'new_windows.npz').exists() else {}
        oldwin.update(new); np.savez_compressed(WORK/'new_windows.npz',**oldwin)
        pd.DataFrame(oldmeta+audit).drop_duplicates(['pick_id','seed_id'],keep='last').to_csv(WORK/'new_windows.csv',index=False)
    WINDOWS.update(new)
    for r in audit:META[r['pick_id'],r['seed_id']]=r
    edges=pd.read_csv(OUT/'inputs/differential_times.csv')
    # Named tuples are not reliably picklable across dynamically loaded frames.
    from types import SimpleNamespace
    results=[]; chunk=3000
    with ProcessPoolExecutor(max_workers=12,mp_context=mp.get_context('fork')) as pool:
        def batches():
            for start in range(0,len(edges),chunk):
                yield [SimpleNamespace(**r) for r in edges.iloc[start:start+chunk].to_dict('records')]
        for i,rows in enumerate(pool.map(batch,batches(),chunksize=1),1):
            results.extend(rows)
            if i%10==0:print('Measured',len(results),'/',len(edges),flush=True)
    result=pd.concat([edges.reset_index(drop=True),pd.DataFrame(results)],axis=1)
    # Reproduce old acceptance and accepted lag on all overlapping identities.
    checks=[]
    for stage in ['50_uncertain_depth_pairs','51_confirmation']:
        old=pd.read_csv(HERE/'export'/stage/'cc_measurements.csv')
        q=old.merge(result,on=['pick_id_a','pick_id_b'],suffixes=('_old','_new'),validate='one_to_one')
        assert (q.accepted_old==q.accepted_new).all(),(stage,q[q.accepted_old!=q.accepted_new].head())
        good=q[q.accepted_old]
        assert np.allclose(good.lag_s_old,good.lag_s_new,atol=1e-12,rtol=0)
        checks.append({'stage':stage,'overlapping_edges':len(q),'accepted':len(good),'identical_acceptance_and_lag':True})
    result.to_csv(OUT/'cc_measurements.csv',index=False)
    (WORK/'checks.json').write_text(json.dumps({'fast_curve_equivalence':True,'known_delay_s':.07,'historical_reproduction':checks,'window_cache_sources':reused,'candidate_edges':len(result),'accepted':int(result.accepted.sum())},indent=2)+'\n')
    print('CC complete',len(result),'accepted',int(result.accepted.sum()),flush=True)

if __name__=='__main__':main()
