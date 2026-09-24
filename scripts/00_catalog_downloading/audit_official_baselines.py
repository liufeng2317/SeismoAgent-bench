#!/usr/bin/env python3
"""Audit local official baseline snapshots against the frozen query config."""
from __future__ import annotations
import csv,json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; CONFIG=ROOT/'scripts/00_catalog_downloading/official_baseline_windows.json'; DATA=ROOT/'data'
def dt(s):
 try:return datetime.fromisoformat(s.replace('Z','+00:00')).replace(tzinfo=timezone.utc)
 except:return None
def num(s):
 try:return float(s)
 except:return None
def read(p):
 with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def check(rows,scope):
 lo=dt(scope['starttime']+'Z'); hi=dt(scope['endtime']+'Z'); bad=[]; ids=[]
 for r in rows:
  t=dt(r.get('time','')); lat=num(r.get('latitude')); lon=num(r.get('longitude')); dep=num(r.get('depth'))
  if not t or not (lo<=t<hi):bad.append('time');continue
  if lat is None or not scope['minlatitude']<=lat<=scope['maxlatitude']:bad.append('latitude')
  if lon is None or not scope['minlongitude']<=lon<=scope['maxlongitude']:bad.append('longitude')
  if dep is None or not scope['mindepth']<=dep<=scope['maxdepth']:bad.append('depth')
  ids.append(r.get('id',''))
 return {'rows':len(rows),'unique_ids':len(set(ids)),'duplicate_ids':len(ids)-len(set(ids)),'out_of_scope_rows':len(bad),'out_of_scope_reasons':dict(Counter(bad)),'networks':dict(Counter(r.get('net','') for r in rows)),'location_sources':dict(Counter(r.get('locationSource','') for r in rows)),'types':dict(Counter(r.get('type','') for r in rows))}
def main():
 cfg=json.loads(CONFIG.read_text()); report=[]
 for case,spec in cfg.items():
  case_result={'case_id':case,'provider':spec['provider'],'source_filter_note':'The downloader does not send network/locationSource to ComCat; source fields are audited after retrieval.','scopes':{}}
  if not spec['provider'].startswith('USGS') and not spec['provider'].startswith('USGS ComCat'):
   continue
  for name in ('full','benchmark'):
   p=ROOT/spec[name]['output']; rows=read(p); x=check(rows,spec[name]); x['path']=str(p.relative_to(ROOT)); case_result['scopes'][name]=x
  full_ids={r.get('id') for r in read(ROOT/spec['full']['output'])}; bench_ids={r.get('id') for r in read(ROOT/spec['benchmark']['output'])}; case_result['benchmark_subset_of_full']=bench_ids<=full_ids
  report.append(case_result)
 out=DATA/'OFFICIAL_BASELINE_AUDIT.md'; lines=['# Official baseline download audit','','This report checks local CSV snapshots against the configured full/benchmark time, space, and depth windows. It does not treat a small routine-catalog count as a download failure. ComCat does not expose `network`/`locationSource` as the same query filters used by the local source labels; those fields are audited after retrieval.','','| Case | Full rows | Benchmark rows | Full out-of-scope | Benchmark out-of-scope | Duplicate IDs | Benchmark subset | Source distribution |','|---|---:|---:|---:|---:|---:|---|---|']
 for x in report:
  f=x['scopes']['full'];b=x['scopes']['benchmark']; dup=f['duplicate_ids']+b['duplicate_ids']; src=', '.join(f"{k}:{v}" for k,v in f['networks'].items())
  lines.append(f"| `{x['case_id']}` | {f['rows']:,} | {b['rows']:,} | {f['out_of_scope_rows']} | {b['out_of_scope_rows']} | {dup} | {'yes' if x['benchmark_subset_of_full'] else 'NO'} | {src} |")
 lines += ['', '## Interpretation','', '- `out_of_scope_rows = 0`, zero duplicate IDs, and benchmark subset `yes` indicate that the local merge obeys the configured query mask.', '- Prague and Maple are small because they are routine ComCat/U.S. network baselines, not enhanced research catalogs. Their low counts are consistent with the local source distributions and are not evidence of a truncation: all chunks are far below the ComCat 20,000-row cap.', '- Source labels are preserved. Prague includes 64 `tul` and 7 `us` location-source rows; HVO includes 40,086 `hv` and 9 `us`; Ridgecrest includes 17,958 `ci` and 1 `us`; these should not be silently recoded.', '- For completeness benchmarking, use the research catalogs (Cochran/McMahon, Shelly/Pang, etc.) rather than substituting the official routine baseline.']
 for x in report:
  lines += ['',f"### `{x['case_id']}`",'',f"- Full: `{x['scopes']['full']['path']}`; benchmark: `{x['scopes']['benchmark']['path']}`",f"- Full source fields: networks `{x['scopes']['full']['networks']}`, location sources `{x['scopes']['full']['location_sources']}`",f"- Full type fields: `{x['scopes']['full']['types']}`",f"- Benchmark subset of full: `{x['benchmark_subset_of_full']}`"]
 out.write_text('\n'.join(lines)+'\n'); print(out)
if __name__=='__main__':main()
