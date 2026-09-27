#!/usr/bin/env python3
"""Root-only Bubblewrap synthetic boundary probe; no real data or agent."""
import argparse, json, os, pwd, subprocess, tempfile, time
from pathlib import Path
from manage import STATE, now, save, root_only

CHILD = r'''import json, os, pathlib, sys
uid = int(sys.argv[1])
sample = pathlib.Path('/input/sample.txt')
checks = {'uid_dropped': os.getuid() == uid and os.geteuid() == uid,
          'input_readable': sample.read_text() == 'synthetic observation',
          'host_marker_hidden': not pathlib.Path('/host-marker.txt').exists(),
          'work_visible': pathlib.Path('/work').is_dir()}
try:
    with sample.open('a') as stream: stream.write('BAD')
except PermissionError: checks['input_write_denied'] = True
else: checks['input_write_denied'] = False
pathlib.Path('/output/result.txt').write_text('ok')
checks['output_writable'] = pathlib.Path('/output/result.txt').read_text() == 'ok'
print(json.dumps(checks), flush=True)
sys.exit(0 if all(checks.values()) else 1)
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account', default='bench-agent01')
    args = parser.parse_args(); root_only(); user = pwd.getpwnam(args.account)
    report = dict(checked_at=now(), account=args.account, bwrap_version=None,
                  scope='synthetic Bubblewrap boundary only', real_data_used=False,
                  agent_started=False, passed=False)
    try:
        report['bwrap_version'] = subprocess.check_output(['/usr/bin/bwrap', '--version'], text=True).strip()
        with tempfile.TemporaryDirectory(prefix='bwrap-check-', dir='/tmp') as tmp:
            base = Path(tmp); input_dir = base/'input'; input_dir.mkdir(mode=0o755)
            (input_dir/'sample.txt').write_text('synthetic observation'); (input_dir/'sample.txt').chmod(0o444)
            output_dir = base/'output'; output_dir.mkdir(mode=0o700); os.chown(output_dir, user.pw_uid, user.pw_gid)
            marker = base/'host-marker.txt'; marker.write_text('must stay hidden')
            command = ['/usr/bin/bwrap','--die-with-parent','--new-session','--unshare-user','--unshare-pid','--unshare-ipc','--unshare-uts','--clearenv','--ro-bind','/usr','/usr','--ro-bind','/lib','/lib']
            if Path('/lib64').exists():
                command += ['--ro-bind', '/lib64', '/lib64']
            command += ['--proc','/proc','--dev','/dev','--tmpfs','/tmp','--ro-bind',str(input_dir),'/input','--bind',str(output_dir),'/output','--dir','/work','--chdir','/work','--uid',str(user.pw_uid),'--gid',str(user.pw_gid),'/usr/bin/python3','-I','-c',CHILD,str(user.pw_uid)]
            result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30, env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'})
            report.update(exit_code=result.returncode, stderr=result.stderr, checks=json.loads(result.stdout) if result.stdout.strip() else {})
            report['output_created'] = (output_dir/'result.txt').read_text() == 'ok' if (output_dir/'result.txt').exists() else False
            report['input_unchanged'] = input_dir.joinpath('sample.txt').read_text() == 'synthetic observation'; report['host_marker_outside_sandbox'] = marker.exists()
            report['passed'] = result.returncode == 0 and report['output_created'] and report['input_unchanged'] and marker.exists()
    except Exception as exc: report['error'] = str(exc)
    report_path = STATE/'slots'/args.account/('bwrap-check-'+str(int(time.time()))+'.json'); save(report_path, report)
    print(json.dumps(report, indent=2)); print('Saved report:', report_path); raise SystemExit(0 if report['passed'] else 1)
if __name__ == '__main__': main()
