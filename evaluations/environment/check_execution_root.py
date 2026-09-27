#!/usr/bin/env python3
"""Probe chroot and UID dropping only; no runtime installation or real inputs."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

from manage import STATE, demote, managed, now, owned_processes, pending_journals, root_only, save


# Python and ctypes are loaded BEFORE chroot. A pass does not establish that
# a Python executable, shared libraries or scientific packages work inside it.
CHILD = r'''
import ctypes, json, os, pathlib, sys
libc = ctypes.CDLL(None, use_errno=True)
root, marker, uid, gid = sys.argv[1:]
os.chdir('/')
os.chroot(root)
os.chdir('/')
os.setgroups([])
os.setgid(int(gid))
os.setuid(int(uid))
os.umask(0o077)
if libc.prctl(38, 1, 0, 0, 0) != 0:
    raise OSError(ctypes.get_errno(), 'PR_SET_NO_NEW_PRIVS failed')
checks = {'uid_dropped': os.getresuid() == (int(uid),) * 3,
          'gid_dropped': os.getresgid() == (int(gid),) * 3,
          'supplementary_groups_empty': os.getgroups() == [],
          'no_new_privileges': libc.prctl(39, 0, 0, 0, 0) == 1,
          'root_entries_curated': set(os.listdir('/')) == {'input', 'output'},
          'input_readable': pathlib.Path('/input/sample.txt').read_text() == 'synthetic observation',
          'host_marker_hidden': not os.path.exists(marker)}
try:
    with open('/input/sample.txt', 'a') as stream:
        stream.write('BAD')
except PermissionError:
    checks['input_write_denied'] = True
else:
    checks['input_write_denied'] = False
pathlib.Path('/output/result.txt').write_text('ok')
checks['output_writable'] = pathlib.Path('/output/result.txt').read_text() == 'ok'
try:
    os.setuid(0)
except PermissionError:
    checks['root_uid_restore_denied'] = True
else:
    checks['root_uid_restore_denied'] = False
print(json.dumps(checks), flush=True)
sys.exit(0 if all(checks.values()) else 1)
'''


RUNTIME_CHILD = r'''
import ctypes, json, math, os, pathlib, sqlite3, ssl, sys, zlib
import xml.etree.ElementTree as ET
marker, uid = sys.argv[1:]
checks = {
    'fresh_python_exec': sys.executable == '/usr/bin/python3',
    'uid_dropped': os.getresuid() == (int(uid),) * 3,
    'supplementary_groups_empty': not os.getgroups(),
    'host_marker_hidden': not os.path.exists(marker),
    'input_readable': pathlib.Path('/input/sample.txt').read_text() == 'synthetic observation',
    'xml_parser': ET.fromstring('<sample/>').tag == 'sample',
    'sqlite_extension': sqlite3.connect(':memory:').execute('select 1').fetchone() == (1,),
    'compression_extension': zlib.decompress(zlib.compress(b'probe')) == b'probe',
    'math_extension': math.sqrt(4) == 2,
    'ssl_extension': bool(ssl.OPENSSL_VERSION),
    'no_new_privileges': ctypes.CDLL(None).prctl(39, 0, 0, 0, 0) == 1,
    'runtime_not_writable': not os.access(sys.executable, os.W_OK),
}
try:
    with open('/input/sample.txt', 'a') as f: f.write('BAD')
except PermissionError:
    checks['input_write_denied'] = True
else:
    checks['input_write_denied'] = False
pathlib.Path('/output/result.txt').write_text('ok')
checks['output_writable'] = pathlib.Path('/output/result.txt').read_text() == 'ok'
print(json.dumps(checks), flush=True)
sys.exit(0 if all(checks.values()) else 1)
'''


def stage_python(jail):
    """Copy trusted system Python only; no conda/site packages or host config."""
    info = subprocess.check_output(
        ['/usr/bin/python3', '-I', '-c',
         'import sysconfig; print(sysconfig.get_path("stdlib"))'], text=True).strip()
    stdlib = Path(info)
    if not stdlib.is_relative_to('/usr/lib'):
        raise RuntimeError('Expected a system Python stdlib under /usr/lib')
    destination = jail / stdlib.relative_to('/')
    shutil.copytree(stdlib, destination, symlinks=False,
                    ignore=shutil.ignore_patterns('__pycache__', 'site-packages',
                                                'dist-packages', 'test', 'tests'))
    executable = Path('/usr/bin/python3')
    target = jail / executable.relative_to('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(executable, target)
    target.chmod(0o555)
    sources = [executable, *stdlib.rglob('*.so')]
    libraries = set()
    for source in sources:
        # ldd is used only on trusted system binaries, never submitted agent files.
        result = subprocess.run(['/usr/bin/ldd', str(source)], capture_output=True,
                                text=True, timeout=10, env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C'})
        if result.returncode or 'not found' in result.stdout:
            raise RuntimeError(f'Cannot resolve system dependencies: {source}: {result.stdout} {result.stderr}')
        libraries.update(re.findall(r'(/[^\s()]+)', result.stdout))
    for name in sorted(libraries):
        source = Path(name)
        if not source.is_file() or not str(source).startswith(('/lib/', '/usr/lib/')):
            raise RuntimeError(f'Unexpected system library: {source}')
        target = jail / source.relative_to('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        # copyfile does not preserve mode. In particular, the ELF interpreter
        # (e.g. ld-linux-aarch64.so.1) must remain executable for execve(Python).
        target.chmod(0o555 if source.stat().st_mode & 0o111 else 0o444)
    # Keep executable bits for extensions/libraries; only the output is writable.
    for p in (jail/'usr', jail/'lib'):
        if p.exists():
            for child in p.rglob('*'):
                child.chmod(0o555 if child.is_dir() or child.suffix == '.so' or os.access(child, os.X_OK) else 0o444)
            p.chmod(0o555)
    return dict(stdlib=str(stdlib), library_count=len(libraries),
                copied_bytes=sum(p.stat().st_size for p in jail.rglob('*') if p.is_file()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--account', default='bench-agent01')
    parser.add_argument('--runtime', action='store_true', help='Copy and execute system Python inside the root')
    args = parser.parse_args()
    root_only()
    slot, user = managed(args.account)
    with (STATE/'acl.lock').open('a') as global_lock, (slot/'slot.lock').open('a') as slot_lock:
        for lock in (global_lock, slot_lock):
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if pending_journals() or owned_processes(user.pw_uid):
            raise RuntimeError('Resolve pending recovery or active managed-UID processes first')
        report = dict(checked_at=now(), account=args.account,
                      scope='chroot syscall and privilege-drop feasibility only',
                      formal_evaluation_eligible=False, runtime_exec_tested=False,
                      real_data_used=False, passed=False)
        if args.runtime:
            report['scope'] = 'Fresh system Python execution inside chroot; standard library only'
        report_path = slot / ('execution-root-check-' + uuid.uuid4().hex[:12] + '.json')
        try:
            with tempfile.TemporaryDirectory(prefix='execution-root-check-', dir=slot) as tmp:
                base = Path(tmp)
                marker = base/'host-only.txt'
                marker.write_text('synthetic host marker')
                jail = base/'root'
                jail.mkdir(mode=0o755)
                jail.chmod(0o755)
                (jail/'input').mkdir(mode=0o755)
                (jail/'input').chmod(0o755)
                sample = jail/'input/sample.txt'
                sample.write_text('synthetic observation')
                sample.chmod(0o444)
                output = jail/'output'
                output.mkdir(mode=0o700)
                os.chown(output, user.pw_uid, user.pw_gid)
                command = ['/usr/bin/python3', '-I', '-c', CHILD, str(jail), str(marker),
                           str(user.pw_uid), str(user.pw_gid)]
                enter = None
                if args.runtime:
                    print('Staging system Python and shared libraries; no packages are installed.', flush=True)
                    report['staging'] = stage_python(jail)
                    def enter():
                        os.chroot(jail)
                        os.chdir('/')
                        demote(user, limits=True)
                    command = ['/usr/bin/python3', '-I', '-B', '-c', RUNTIME_CHILD,
                               str(marker), str(user.pw_uid)]
                    report['runtime_exec_tested'] = True
                result = subprocess.run(
                    command, preexec_fn=enter,
                    stdin=subprocess.DEVNULL, capture_output=True, text=True,
                    cwd='/', close_fds=True, timeout=20,
                    env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
                report.update(exit_code=result.returncode, stderr=result.stderr,
                              checks=json.loads(result.stdout) if result.stdout.strip() else {})
                report['input_unchanged'] = sample.read_text() == 'synthetic observation'
                report['passed'] = result.returncode == 0 and report['input_unchanged']
        except Exception as exc:
            report['error'] = str(exc)
        save(report_path, report)
        print(json.dumps(report, indent=2))
        print('Saved report:', report_path)
        raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
