"""Case-specific adapters for the frozen stage50 recipe; no fitted parameters."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parents[2]
OUT=HERE/'export/51_confirmation';SELECTED=HERE/'export/50_uncertain_depth_pairs'
BASE=HERE/'export/45_added_station/base';ORIGINAL=HERE/'export/10_validate_catalog'
XYZ=['x_km','y_km','depth_km']
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def freeze(path,value):
 if path.exists():assert json.loads(path.read_text())==value,f'Frozen file changed: {path}'
 else:save(path,value)
def verify_candidate():
 r=json.loads((SELECTED/'run.json').read_text());assert r['all_gates_passed'] and not r['full_catalog_adopted']
 for path,h in json.loads((SELECTED/'frozen_candidate.json').read_text())['source_sha256'].items():assert sha(path)==h,path
def held():return set(json.loads((HERE/'export/12_relative_location_pilot/run.json').read_text())['held_out_stations'])
def exclusions(include_reserve3=False):
 paths=[HERE/'export/12_relative_location_pilot/events.csv',HERE/'export/15_validate_transfer/inputs/events.csv',HERE/'docs/optimization_reserved_events.csv']
 if include_reserve3:paths.append(HERE/'docs/optimization_reserved_events_v3.csv')
 return set().union(*(set(pd.read_csv(f).event_id) for f in paths))
def source_data():
 e=pd.read_csv(ORIGINAL/'events.csv');ph=pd.read_csv(ORIGINAL/'phases.csv',low_memory=False);prior=pd.read_csv(SELECTED/'inputs/all_phases.csv',low_memory=False);extra=prior[~prior.pick_id.isin(ph.pick_id)];assert extra.pick_id.str.startswith(('vp42_','mp44_','lb45_','eqs47_')).all()
 allph=pd.concat([ph,extra],ignore_index=True);assert allph.pick_id.is_unique
 return e,ph,allph
def lookup(ph,event_ids):
 ph=ph[ph.event_id.isin(event_ids)].copy();direct=ph.pick_id.str.startswith(('vp42_','mp44_','lb45_','eqs47_'));old=ph[~direct&ph.probability.ge(.5)];old=old[~old.duplicated(['event_id','instrument_id','phase'],keep=False)];good=pd.concat([old,ph[direct]],ignore_index=True);assert not good.duplicated(['event_id','instrument_id','phase']).any();good['key']=good.instrument_id+':'+good.phase
 return {eid:g.set_index('key') for eid,g in good.groupby('event_id')}
def ranked_pairs(targets,pool,ph,envelope=False,nearest=False):
 xyz=pool[XYZ].to_numpy();look=lookup(ph,set(pool.event_id));keys={eid:set(g.index) for eid,g in look.items()};hh=held();train={eid:{k for k in kk if k.split(':')[0] not in hh} for eid,kk in keys.items()};pairs=set();rows=[]
 mean=pool.posterior_mean_depth_km.to_numpy(float);sigma=pool.posterior_sigma_depth_km.to_numpy(float);valid=np.isfinite(mean)&np.isfinite(sigma)&(sigma>=0)&(mean>=0)&(mean<=25);lo=np.where(valid,np.maximum(0,mean-2*sigma),xyz[:,2]);hi=np.where(valid,np.minimum(25,mean+2*sigma),xyz[:,2]);bounds=dict(zip(pool.event_id,zip(lo,hi)))
 for event in targets.itertuples():
  d=np.linalg.norm(xyz-np.array([getattr(event,k) for k in XYZ]),axis=1);horizontal=np.linalg.norm(xyz[:,:2]-np.array([event.x_km,event.y_km]),axis=1);low,high=bounds[event.event_id];gap=np.maximum(np.maximum(lo-high,low-hi),0);screen=np.hypot(horizontal,gap) if envelope else d
  indices=np.flatnonzero((screen<=3)&pool.event_id.ne(event.event_id).to_numpy());rank=[]
  for i in indices:
   eid=pool.event_id.iloc[i]
   if nearest:rank.append((0,0,float(d[i]),eid));continue
   common=keys.get(event.event_id,set())&keys.get(eid,set());ct=train.get(event.event_id,set())&train.get(eid,set());ns=len({k.split(':')[0] for k in ct})
   if len(common)>=6 and len({k.split(':')[0] for k in common})>=4 and ct:rank.append((-ns,-len(ct),float(d[i]),eid))
  for ns,nph,distance,eid in sorted(rank)[:12]:pairs.add(tuple(sorted([event.event_id,eid])));rows.append({'target_event_id':event.event_id,'neighbor_event_id':eid,'distance_km':distance,'shared_training_stations':-ns,'shared_training_phases':-nph})
 return pairs,pd.DataFrame(rows)
def cohort(pool,targets,pairs,original):
 ids=set(targets)|{v for pair in pairs for v in pair};e=pool[pool.event_id.isin(ids)].copy();e['role']=np.where(e.event_id.isin(targets),'reserve','support');ph=original[original.event_id.isin(ids)&~original.instrument_id.isin(held())];counts=ph.assign(is_s=ph.phase.eq('S')).groupby('event_id').agg(n=('pick_id','size'),n_s=('is_s','sum')).reindex(e.event_id,fill_value=0);e['auxiliary_eligible']=(counts.n.ge(10)&counts.n_s.ge(3)).to_numpy();return e
def edges_for(pairs,ph,poolids):
 look=lookup(ph,poolids);rows=[];status=[];hh=held()
 for a,b in sorted(pairs):
  common=sorted(set(look.get(a,pd.DataFrame()).index)&set(look.get(b,pd.DataFrame()).index));ok=len(common)>=6 and len({k.split(':')[0] for k in common})>=4;status.append({'event_id_a':a,'event_id_b':b,'eligible':ok,'n_common':len(common)})
  if not ok:continue
  for key in common:
   x,y=look[a].loc[key],look[b].loc[key];rows.append({'event_id_a':a,'event_id_b':b,'pick_id_a':x.pick_id,'pick_id_b':y.pick_id,'instrument_id':x.instrument_id,'phase':x.phase,'observed_dt_s':(pd.Timestamp(x.time_utc)-pd.Timestamp(y.time_utc)).total_seconds(),'training':x.instrument_id not in hh})
 return pd.DataFrame(rows),pd.DataFrame(status)
def prediction(e,station,phase):
 hdr=BASE/'grids'/f'time.{phase}.{station.nll_station}.time.hdr';p=hdr.read_text().splitlines()[0].split();ny,nz=int(p[1]),int(p[2]);h=float(p[7]);top=float(p[5]);v=np.fromfile(hdr.with_suffix('.buf'),np.float32,count=ny*nz).reshape(ny,nz).astype(float);ur=np.hypot(e.x_km-station['x(km)'],e.y_km-station['y(km)']).to_numpy()/h;uz=(e.depth_km.to_numpy()-top)/h;i=np.floor(ur).astype(int);j=np.floor(uz).astype(int);a=ur-i;b=uz-j;assert np.all((i>=0)&(i<ny-1)&(j>=0)&(j<nz-1));return (1-a)*((1-b)*v[i,j]+b*v[i,j+1])+a*((1-b)*v[i+1,j]+b*v[i+1,j+1])
