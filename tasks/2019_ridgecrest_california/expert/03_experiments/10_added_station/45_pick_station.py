#!/usr/bin/env python3
"""Frozen CPU PhaseNet inference for added LB.DAC; preserve the original manifest."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import argparse,csv,fcntl,importlib.util,itertools,json,multiprocessing,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import yaml
from scipy.signal import resample_poly
from obspy import read,read_inventory,Stream,Trace,UTCDateTime
from obspy.signal.rotate import rotate2zne
HERE=Path(__file__).resolve().parents[2];OUT=HERE/'export/45_added_station';WAVE=HERE.parents[2]/'data/2019_ridgecrest_california/data/waveforms'
LIB=HERE.parents[2].parent/'TRACE-1.1/seismoagent/library'
s=importlib.util.spec_from_file_location('baseline_picking45',HERE/'01_pipeline/02_pick_phasenet.py');P=importlib.util.module_from_spec(s);sys.modules[s.name]=P;s.loader.exec_module(P)

def convert(x):
 return resample_poly(x,2,5,window=('kaiser',8.6))[:((len(x)-1)*2)//5+1]

def prepare(rows,root,start,end):
 groups={}
 for r in rows:
  st=read(str(root/r['path']),starttime=start,endtime=end).select(id=r['seed_id'])
  if r['component'] in groups:
   old,stream=groups[r['component']];assert all(old[k]==r[k] for k in ['azimuth_deg','dip_deg','sample_rate_hz']);stream+=st
  else:groups[r['component']]=(r,st)
 assert set(groups)==set('ZNE')
 for _,stream in groups.values():stream.merge(method=-1)
 result=Stream();duration=0.;segments=0
 for traces in itertools.product(*(groups[k][1] for k in 'ZNE')):
  a=max(t.stats.starttime for t in traces);b=min(t.stats.endtime for t in traces)
  if b-a<30.01:continue
  pieces=[t.copy().trim(a,b,nearest_sample=False) for t in traces]
  assert all(t.stats.sampling_rate==250 for t in pieces)
  assert max(t.stats.starttime for t in pieces)-min(t.stats.starttime for t in pieces)<1e-5
  n=min(map(len,pieces));args=[]
  for k,t in zip('ZNE',pieces):
   x=t.data[:n];assert not np.ma.isMaskedArray(x) and np.isfinite(x).all();r=groups[k][0]
   args.extend([convert(x.astype(np.float64)),float(r['azimuth_deg']),float(r['dip_deg'])])
  for k,x in zip('ZNE',rotate2zne(*args)):
   header={key:pieces[0].stats[key] for key in ['network','station','location','starttime']};header.update(channel='HH'+k,sampling_rate=100)
   trace=Trace(x.astype(np.float32),header);assert trace.stats.sampling_rate==100 and trace.stats.delta==.01
   assert trace.stats.starttime==pieces[0].stats.starttime and abs(trace.stats.endtime-(pieces[0].stats.starttime+(n-1)/250))<.010001
   result+=trace
  segments+=1;duration+=min(float(b)+.004,float(end))-max(float(a),float(start))
 assert len(result)>0
 return result,segments,duration

def initialize():
 P.prepare=prepare;P.initialize_worker(str(LIB),'original','2',1)

def work(job,rows,cfg):
 return P.pick_chunk(job,('LB.DAC','','HH'),rows,WAVE,str(UTCDateTime('2019-07-04')+int(job)*21600),str(UTCDateTime('2019-07-04')+(int(job)+1)*21600),cfg,str(OUT/'picking'))

def freeze(path,value):
 if path.exists():assert json.loads(path.read_text())==value,f'Frozen inputs changed: {path}'
 else:path.write_text(json.dumps(value,indent=2)+'\n')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,default=8);ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args()
 OUT.mkdir(exist_ok=True);out=OUT/'picking';(out/'chunks').mkdir(parents=True,exist_ok=True)
 lock=(out/'run.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 old=HERE/'export/01_prepare_inputs/full/waveform_inputs.csv';rows=list(csv.DictReader(old.open()));fields=list(rows[0]);new=[];metadata=[]
 inv=read_inventory(str(WAVE/'stations/earthscope.stationxml'))
 for f in sorted((WAVE/'data/LB.DAC').glob('*.mseed')):
  st=read(str(f),headonly=True);assert len(st)==1;t=st[0]
  assert t.stats.npts==21600000 and t.stats.sampling_rate==250 and t.stats.channel in ['HHE','HHN','HHZ']
  epoch=inv.select(network='LB',station='DAC',location='',channel=t.stats.channel,starttime=t.stats.starttime,endtime=t.stats.endtime)
  assert len(epoch)==1 and len(epoch[0])==1 and len(epoch[0][0])==1;c=epoch[0][0][0]
  assert c.start_date<=t.stats.starttime and c.end_date>=t.stats.endtime and c.sample_rate==250
  response=c.response.get_evalresp_response_for_frequencies([1.,5.,10.,20.],output='VEL');assert np.isfinite(response).all() and (abs(response)>0).all()
  metadata.append(dict(seed_id=t.id,response_stages=len(c.response.response_stages),sensitivity=c.response.instrument_sensitivity.value,units=c.response.instrument_sensitivity.input_units,response_abs_1_5_10_20_hz=abs(response).tolist()))
  new.append(dict(path=str(f.relative_to(WAVE)),bytes=f.stat().st_size,seed_id=t.id,station_id='LB.DAC',location='',family='HH',component=t.stats.channel[-1],sample_rate_hz=250.,latitude=c.latitude,longitude=c.longitude,elevation_m=c.elevation,azimuth_deg=c.azimuth,dip_deg=c.dip,start_utc=str(t.stats.starttime),end_utc=str(t.stats.endtime+.004),pilot_candidate=True))
 assert len(new)==9
 P.table(OUT/'waveform_inputs.csv',rows+new,fields);P.table(OUT/'new_waveform_inputs.csv',new,fields)
 # Numerical anti-alias and timing checks are independent of observed earthquake picks.
 tones=[];t=np.arange(25000)/250;u=np.arange(10000)/100
 for hz in [1,5,10,20,80]:
  y=convert(np.sin(2*np.pi*hz*t));target=np.sin(2*np.pi*hz*u[:len(y)]);error=float(np.sqrt(np.mean((y[200:-200]-target[200:-200])**2)))
  amplitude=float(np.sqrt(2*np.mean(y[200:-200]**2)));tones.append(dict(hz=hz,rms_difference=error,amplitude=amplitude))
  assert amplitude<.001 if hz==80 else error<.001
 impulse=[]
 for r in range(5):
  x=np.zeros(2500);x[1250+r]=1;y=convert(x);err=abs(np.argmax(y)/100-(1250+r)/250);assert err<=.0050001;impulse.append(err)
 sample_start=UTCDateTime('2019-07-04T16:00:00');test_stream,_,_=prepare(new,WAVE,sample_start,sample_start+60)
 assert len(test_stream)==3 and all(t.stats.sampling_rate==100 and t.stats.starttime==sample_start and abs(t.stats.endtime-(sample_start+60))<.010001 for t in test_stream)
 checks=dict(actual_trace_header_100hz_and_60s_verified=True,native_files=9,native_rate_hz=250,inference_rate_hz=100,tones=tones,impulse_timing_error_s=impulse,response_metadata=metadata,old_manifest_unchanged=True)
 freeze(OUT/'input_checks.json',checks)
 cfg=yaml.safe_load((HERE/'00_config/config.yaml').read_text());base=LIB/'ai_module/phase_picking'
 files=[Path(__file__),Path(P.__file__),old,OUT/'waveform_inputs.csv',WAVE/'stations/earthscope.stationxml',base/'pretrained/v3/phasenet/original.pt.v2',base/'pretrained/v3/phasenet/original.json.v2',base/'model/phasenet.py',base/'model/base.py']
 design=dict(round=24,baseline='44_missing_p_observations',intervention='Add LB.DAC real three-component P/S observations. No old observation, event, model or gate changes.',resampling='In-memory polyphase 2/5 Kaiser 8.6 anti-alias; retain start time and native support; no gap fill.',picking=cfg['picking'],association={'probability_min':.7,'P_gate_s':1.,'S_gate_s':1.2,'closest_competitor_margin_s':.2,'onset_collision_s':.100001,'competitors':'all original v1 events','cohort':'unchanged stage44 targets/supports','one_pick_per_event_phase':'highest probability; chronological tie break','noncausal_S':'reject S<=P'},cc='Original stage39 pair graph; existing scalar P and frozen vector S rules. Preserve all old CC rows.',location='Original 1D fields, original errors for new PhaseNet P/S, fixed16 matched solves and all original gates; compare44 and39; reserve3 remains unused.',source_sha256={str(f):P.digest(f) for f in files},raw_identity=[(r['path'],(WAVE/r['path']).stat().st_size,(WAVE/r['path']).stat().st_mtime_ns) for r in new])
 design=json.loads(json.dumps(design));freeze(OUT/'design.json',design)
 print('Input/response/resampling checks passed; original 351-row manifest preserved.',flush=True)
 if args.prepare_only:return
 os.environ['SEISBENCH_CACHE_ROOT']=str(out/'cache');import seisbench
 journal=out/'completed.jsonl';done={}
 if journal.exists():
  for line in journal.read_text().splitlines():
   q=json.loads(line)
   if P.digest(out/'chunks'/f"{q['job_id']}.csv")==q['csv_sha256']:done[q['job_id']]=q
 with journal.open('a') as log,ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('spawn'),initializer=initialize) as pool:
  jobs={pool.submit(work,str(i),new,cfg):i for i in range(12) if str(i) not in done}
  for future in as_completed(jobs):
   q=future.result();done[q['job_id']]=q;log.write(json.dumps(q)+'\n');log.flush();os.fsync(log.fileno());print(f"[{len(done)}/12] block {q['job_id']}: {q['picks']} picks in {q['seconds']} s",flush=True)
 picks=[]
 for i in range(12):picks.extend(csv.DictReader((out/'chunks'/f'{i}.csv').open()))
 picks.sort(key=lambda p:(p['time_utc'],p['phase']));unique=[];seen=set()
 for p in picks:
  key=(p['phase'],p['time_utc'])
  if key in seen:continue
  seen.add(key);p['pick_id']=f'lb45_{len(unique):07d}';unique.append(p)
 P.table(out/'picks.csv',unique,P.PICK_FIELDS)
 for path,h in design['source_sha256'].items():assert P.digest(Path(path))==h
 summary=dict(completed_blocks=len(done),picks=len(unique),P=sum(p['phase']=='P' for p in unique),S=sum(p['phase']=='S' for p in unique),exact_duplicates_removed=len(picks)-len(unique),status='complete',catalog_adopted=False)
 (out/'run.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary,flush=True)
if __name__=='__main__':main()
