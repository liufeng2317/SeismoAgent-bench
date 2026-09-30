"""Case-local reusable CC window loading and frozen vector-S measurement."""
from pathlib import Path
import importlib.util
import numpy as np
import pandas as pd
_spec=importlib.util.spec_from_file_location('vector_core_shared',Path(__file__).with_name('38_vector_s.py'))
_V=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_V)
curve=_V.curve
whiten=_V.whiten

def load_windows(path):
    # Direct zip lookup avoids repeated linear membership searches in NpzFile.
    with np.load(path,allow_pickle=False) as archive:
        result={}
        for entry in archive.zip.infolist():
            assert entry.filename.endswith('.npy')
            with archive.zip.open(entry) as stream:
                result[entry.filename[:-4]]=np.lib.format.read_array(stream,allow_pickle=False)
        for key in [archive.files[0],archive.files[-1]]:
            assert np.array_equal(result[key],archive[key])
    return result

def measure_vector_s(source,picks,meta,windows):
 result=source.copy();audits=[]
 for count,(idx,row) in enumerate(source[source.phase.eq('S')].iterrows(),1):
  a,b=picks.loc[row.pick_id_a],picks.loc[row.pick_id_b];seeds=sorted((set(a.source_channels.split(';'))&set(b.source_channels.split(';')))-{v for v in a.source_channels.split(';') if v.endswith('Z')});record={'edge_index':idx,'accepted':False,'reason':'missing_horizontal_windows'}
  valid=len(seeds)==2 and all((pid,seed) in meta.index and meta.loc[(pid,seed),'status']=='ok' and pid+'|'+seed in windows for pid in [row.pick_id_a,row.pick_id_b] for seed in seeds)
  if valid:
   try:
    lag=[];peak=[];margin=[];snrs=[];boundary=False
    for band,snrname in [(0,'snr_primary'),(1,'snr_check')]:
     av=np.stack([windows[row.pick_id_a+'|'+seed][band] for seed in seeds]).astype(float);bv=np.stack([windows[row.pick_id_b+'|'+seed][band] for seed in seeds]).astype(float);sa=np.array([meta.loc[(row.pick_id_a,seed),snrname] for seed in seeds]);sb=np.array([meta.loc[(row.pick_id_b,seed),snrname] for seed in seeds]);snrs.extend([float(np.sqrt(np.mean(sa**2))),float(np.sqrt(np.mean(sb**2)))])
     ls,c=curve(whiten(av,sa),whiten(bv,sb));best=int(np.argmax(abs(c)));lag.append(float(ls[best]/100));peak.append(float(c[best]));margin.append(float(c[best]-np.max(abs(c[abs(ls-ls[best])>8]))));boundary |= abs(ls[best])>=39
    reasons=[]
    if min(snrs)<2:reasons.append('low_vector_snr')
    if min(peak)<.75:reasons.append('low_or_negative_vector_cc')
    if min(margin)<.08:reasons.append('ambiguous_peak')
    if boundary:reasons.append('lag_boundary')
    if abs(lag[0]-lag[1])>.020001:reasons.append('band_instability')
    record.update(accepted=not reasons,reason=';'.join(reasons) or 'accepted',lag_s=lag[0],cc=peak[0],cc_check=peak[1],lag_check_s=lag[1],min_vector_snr=min(snrs),peak_margin=min(margin))
   except ValueError as exc:record['reason']='invalid_noise_estimate'
  for col,value in [('accepted',record['accepted']),('reason',record['reason']),('lag_s',record.get('lag_s',np.nan) if record['accepted'] else np.nan),('cc',record.get('cc',np.nan) if record['accepted'] else np.nan)]:result.loc[idx,col]=value
  result.loc[idx,'cc_arrival_difference_s']=row.observed_dt_s-record['lag_s'] if record['accepted'] else np.nan;audits.append(record)
  if count%3000==0:print('Vector S',count,'of',int(source.phase.eq('S').sum()),flush=True)
 assert result[source.phase.eq('P')].equals(source[source.phase.eq('P')])
 return result,pd.DataFrame(audits)
