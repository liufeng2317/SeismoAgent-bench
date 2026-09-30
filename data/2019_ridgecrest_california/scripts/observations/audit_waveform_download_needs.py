#!/usr/bin/env python3
"""Assess local candidate waveform gaps; update the existing inventory, without downloading."""
import json
from pathlib import Path
from collections import defaultdict
from obspy import read, UTCDateTime
c=Path(__file__).resolve().parents[2];b=c/'data/waveforms'
d=json.loads((b/'waveform_inventory.json').read_text());meta=json.loads((b/'stations/station_inventory.json').read_text())['channel_epochs'];prep=json.loads((c/'analysis/station_preparation.json').read_text())
a=UTCDateTime(d['candidate']['start_utc']);z=UTCDateTime(d['candidate']['end_utc']);start=float(a);end=float(z)
existing={s['network']+'.'+s['station'] for r in d['files'] for s in r['streams'] if s['candidate_npts']}
sets={}
for cat in ['LIU2020_GL086189','SHELLY2020_0220190309']:
 x=json.loads((b/'stations/station_inventory.json').read_text())['catalogs'][cat];target=set(x['metadata_present_station_ids']);sets[cat]={'target':len(target),'present':len(target&existing),'missing':sorted(target-existing)}
target=set(prep['ross_rule_candidates']['station_ids']);sets['ROSS_rule_candidates']={'target':len(target),'present':len(target&existing),'missing':sorted(target-existing)}
intervals=defaultdict(list);rates=defaultdict(set)
for r in d['files']:
 if not r['in_candidate_window']:continue
 for tr in read(str(b/r['path']),headonly=True,format='MSEED'):
  s=tr.stats;lo=max(start,float(s.starttime));hi=min(end,float(s.starttime)+s.npts/s.sampling_rate)
  if hi>lo:intervals[tr.id].append((lo,hi));rates[tr.id].add(s.sampling_rate)
rows=[]
for nslc,ints in sorted(intervals.items()):
 cursor=start;missing=[]
 for lo,hi in sorted(ints):
  if lo>cursor+1e-6:missing.append((cursor,lo))
  cursor=max(cursor,hi)
 if cursor<end-1e-6:missing.append((cursor,end))
 net,sta,loc,ch=nslc.split('.')
 epochs=[m for m in meta if (m['network'],m['station'],m['location'],m['channel'])==(net,sta,loc,ch) and m['candidate_overlap_seconds']>0]
 usable=[m for m in epochs if m['response_present'] and m['response_stages']>0 and m['sample_rate_hz'] in rates[nslc]]
 def covers(x,y):
  cur=x
  for l,h in sorted((float(UTCDateTime(m['effective_start'])) if m['effective_start'] else float('-inf'),float(UTCDateTime(m['effective_end'])) if m['effective_end'] else float('inf')) for m in usable):
   if l>cur:break
   cur=max(cur,h)
   if cur>=y:return True
  return False
 rows.append({'seed_id':nslc,'missing_seconds':round(sum(y-x for x,y in missing),6),'gaps_over_1s':[{'start_utc':str(UTCDateTime(x)),'end_utc':str(UTCDateTime(y)),'seconds':round(y-x,6)} for x,y in missing if y-x>1],'matching_response_metadata_covers_observed_intervals':all(covers(x,y) for x,y in ints)})
missingstations=sorted(set(sum((x['missing'] for x in sets.values()),[])))
options={sta:sorted({m['location']+'.'+m['channel'] for m in meta if m['network']+'.'+m['station']==sta and m['candidate_overlap_seconds']>0 and m['channel'].startswith(('EH','HH','HN'))}) for sta in missingstations}
# Channel candidates at already present stations are metadata options, not automatic requests.
actual=set(intervals)
partial={sta:sorted({m['location']+'.'+m['channel'] for m in meta if m['network']+'.'+m['station']==sta and m['candidate_overlap_seconds']>0 and m['channel'].startswith(('EH','HH')) and '.'.join((m['network'],m['station'],m['location'],m['channel'])) not in actual}) for sta in sorted(existing)}
partial={k:v for k,v in partial.items() if v}
r={'window':d['candidate'],'station_comparison':sets,'missing_station_channel_options':options,'additional_EH_HH_metadata_options_at_present_stations':partial,'existing_channels':len(rows),'channels_with_gaps_over_1s':[x for x in rows if x['gaps_over_1s']],'response_metadata_unmatched':[x['seed_id'] for x in rows if not x['matching_response_metadata_covers_observed_intervals']],'scope':'Local coverage audit only. Missing means absent locally, not confirmed remotely available. Station sets are reference candidates, not finalized input. Metadata match checks NSLC, response presence, rate and epochs, not response calibration quality.'}
d['download_assessment']=r
output=b/'waveform_inventory.json'
tmp=output.with_suffix('.json.tmp')
tmp.write_text(json.dumps(d,indent=2)+'\n')
tmp.replace(output)
print(json.dumps({k:v for k,v in r.items() if k!='channels_with_gaps_over_1s'},indent=2))
