#!/usr/bin/env python3
"""Resume the already launched confirmation jobs; fail closed on missing products."""
import json,os,subprocess,time,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;LOG=HERE/'logs';OUT=HERE.parents[1]/'export/51_confirmation';PYTHON='/liufeng1afs/software/miniconda3/envs/seismoagent/bin/python'
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
# Register the observation module in parent and spawned children. Normalize only
# JSON container types when validating an existing cache (tuples serialize as lists).
import _confirmation as C
OBS=C.load('confirmation_observations',HERE/'51_observations.py')
_original_freeze=C.freeze
def canonical_freeze(path,value):
 return _original_freeze(path,json.loads(json.dumps(value,allow_nan=False)))
C.freeze=canonical_freeze
def wait(name):
 pid=int((LOG/(name+'.pid')).read_text())
 while True:
  p=Path('/proc')/str(pid)/'stat'
  if not p.exists():break
  fields=p.read_text().split()
  if fields[2]=='Z':
   assert int(fields[51])==0,(name,'nonzero process exit',fields[51]);break
  time.sleep(10)
 assert 'Traceback (most recent call last)' not in (LOG/(name+'.log')).read_text(),name

def main():
 wait('51_observations');assert (OUT/'observations/summary.json').exists()
 for name in ['51_graph','51_measure','51_run','51_evaluate']:
  if name=='51_run':
   wait('51_native_controls');assert (OUT/'native_controls/events.csv').exists();assert 'All native controls and pick identities verified.' in (LOG/'51_native_controls.log').read_text()
  print('Starting',name,flush=True)
  with (LOG/(name+'.log')).open('w') as log:
   process=subprocess.Popen([PYTHON,'-u',str(HERE/(name+'.py'))],stdout=log,stderr=subprocess.STDOUT);(LOG/(name+'.pid')).write_text(str(process.pid)+'\n');code=process.wait()
  (LOG/(name+'.exitcode')).write_text(str(code)+'\n');assert code==0,(name,code)
 print('Confirmation complete',flush=True)
if __name__=='__main__':
 if '--observations' in sys.argv:
  sys.argv.remove('--observations')
  for kind in ['dpp','eqt']:
   env=os.environ.copy();env['SEISBENCH_CACHE_ROOT']=str(OUT/'observations'/kind/'cache')
   subprocess.run([PYTHON,'-c','import seisbench'],env=env,check=True)
  OBS.main();sys.exit(0)
 try:main()
 except BaseException:
  (LOG/'51_continue.exitcode').write_text('1\n');raise
 else:(LOG/'51_continue.exitcode').write_text('0\n')
