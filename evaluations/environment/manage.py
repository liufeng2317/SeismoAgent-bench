#!/usr/bin/env python3
"""DEVELOPMENT ONLY: root-managed account slots, not a formal evaluation sandbox."""
import argparse
import ctypes
import datetime
import errno
import fcntl
import json
import os
from pathlib import Path
import pwd
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import uuid
import time
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from acl_transaction import Transaction, ACL, open_target, identity, durable_save

STATE = Path('/var/lib/seismoagentbench')
NAME = re.compile(r'bench-agent[0-9]{2}\Z')
RUN_ID = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}\Z')


def save(path, obj):
    durable_save(path, obj)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def root_only():
    if os.geteuid() != 0:
        raise RuntimeError('This command requires root; doctor is read-only and unprivileged.')


def doctor(output):
    info = dict(checked_at=now(), uid=os.getuid(), architecture=os.uname().machine,
                commands={c: shutil.which(c) for c in ['useradd', 'runuser', 'setfacl', 'getfacl', 'prlimit', 'apptainer', 'bwrap']},
                root_setup_validated=False, formal_evaluation_eligible=False,
                execution_profile='development-account',
                boundary='Unix account permissions only; network and kernel are shared.')
    print(json.dumps(info, indent=2))
    if output:
        save(Path(output), info)


def managed(account):
    if not NAME.fullmatch(account):
        raise ValueError('Account must be bench-agentNN, e.g. bench-agent01')
    path = STATE / 'slots' / account
    meta = json.loads((path / 'account.json').read_text())
    user = pwd.getpwnam(account)
    if user.pw_uid != meta['uid'] or user.pw_gid != meta['gid'] or user.pw_uid == 0:
        raise RuntimeError('Managed account identity changed')
    if os.getgrouplist(account, user.pw_gid) != [user.pw_gid]:
        raise RuntimeError('Managed account must have no supplementary groups')
    return path, user


def initialize(account):
    root_only()
    if not NAME.fullmatch(account):
        raise ValueError('Use a new bench-agentNN account')
    try:
        pwd.getpwnam(account)
    except KeyError:
        pass
    else:
        raise RuntimeError('Account already exists; refusing to adopt or modify an existing user')
    if STATE.exists() and (STATE.is_symlink() or STATE.stat().st_uid != 0 or STATE.stat().st_mode & 0o022):
        raise RuntimeError('State root must be root-owned, not a symlink, and not group/world writable')
    STATE.mkdir(mode=0o711, exist_ok=True)
    (STATE / 'slots').mkdir(mode=0o711, exist_ok=True)
    subprocess.run(['useradd', '--user-group', '--no-create-home', '--home-dir', '/nonexistent',
                    '--shell', '/usr/sbin/nologin', account], check=True)
    user = pwd.getpwnam(account)
    path = STATE / 'slots' / account
    path.mkdir(mode=0o711)
    (path / 'runs').mkdir(mode=0o711)
    save(path / 'account.json', dict(account=account, uid=user.pw_uid, gid=user.pw_gid, created_at=now()))
    print(f'Created dedicated slot {account}; no sudo privileges were granted. Audit sudo/site policies separately.')


def check_bundle(bundle):
    """No links/special files or obvious private material in a public input bundle."""
    if bundle.is_symlink() or not bundle.is_dir():
        raise ValueError('Bundle must be a real directory')
    forbidden = {'.git', '.ssh', 'expert', 'references', 'solution', 'solutions', 'grader', 'grading'}
    for p in [bundle, *bundle.rglob('*')]:
        mode = p.lstat().st_mode
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f'Links and special files are forbidden: {p}')
        if p.name in forbidden or p.name == '.env' or p.name.startswith('.env.'):
            raise ValueError(f'Private/ambiguous bundle content: {p}')


def owned_processes(uid):
    result = []
    for p in Path('/proc').iterdir():
        if p.name.isdigit():
            try:
                lines = (p / 'status').read_text().splitlines()
                if any(x.startswith('State:') and x.split()[1] == 'Z' for x in lines):
                    continue
                ids = next(x for x in lines if x.startswith('Uid:')).split()[1:]
                if str(uid) in ids:
                    result.append(int(p.name))
            except (FileNotFoundError, PermissionError, ProcessLookupError, StopIteration):
                pass
    return result


def outside_files(uid):
    found = []
    for base in ['/tmp', '/var/tmp', '/dev/shm']:
        def error(exc):
            raise RuntimeError(f'Cannot audit shared temporary storage: {exc}')
        for directory, dirs, files in os.walk(base, followlinks=False, onerror=error):
            for name in dirs + files:
                p = Path(directory) / name
                try:
                    if p.lstat().st_uid == uid:
                        found.append(str(p))
                except FileNotFoundError:
                    pass
    return found


def demote(user, limits=False):
    os.setgroups([])
    os.setgid(user.pw_gid)
    os.setuid(user.pw_uid)
    os.umask(0o077)
    if ctypes.CDLL(None, use_errno=True).prctl(38, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), 'PR_SET_NO_NEW_PRIVS failed')
    if limits:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))


def probe(user, policy, public=None):
    # Run the actual access checks under the slot UID, never infer access from mode bits alone.
    code = '''import json,os,sys
p=json.load(sys.stdin); result=[]
for kind in ('allow_read','deny_read'):
 for name in p[kind]:
  readable=os.access(name,os.R_OK)
  writable=os.access(name,os.W_OK)
  ok=(readable and not writable) if kind=='allow_read' else not readable
  result.append(dict(kind=kind,path=name,readable=readable,writable=writable,ok=ok))
print(json.dumps(result))
'''
    checks = {k: list(policy[k]) for k in ('allow_read', 'deny_read')}
    if public:
        checks['allow_read'] += [str(p) for p in public.rglob('*') if p.is_file()]
    res = subprocess.run(['/usr/bin/python3', '-I', '-c', code], input=json.dumps(checks),
                         text=True, capture_output=True, check=True,
                         env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'},
                         preexec_fn=lambda: demote(user), cwd='/')
    results = json.loads(res.stdout)
    return results


def read_policy(path):
    policy = json.loads(Path(path).read_text())
    if set(policy) != {'allow_read', 'deny_read'}:
        raise ValueError('run accepts only an audit policy (allow_read/deny_read); use run-access with an access config for transactional grants.')
    for key in ('allow_read', 'deny_read'):
        if not isinstance(policy.get(key), list) or not policy[key]:
            raise ValueError(f'{key} must be a nonempty list of existing absolute paths')
        for name in policy[key]:
            p = Path(name)
            if not p.is_absolute() or not p.exists():
                raise ValueError(f'Missing/non-absolute policy path: {name}')
    # Directories alone cannot prove that known answer files are inaccessible.
    if not any(Path(p).is_file() for p in policy['deny_read']):
        raise ValueError('deny_read must include actual private answer files, not only directories')
    return policy


def plan_access(config_path):
    """Expand explicit access scope without changing ACLs or creating accounts."""
    config = json.loads(Path(config_path).read_text())
    if set(config) - {'restrict_roots'} != {'account', 'run_id', 'data_read', 'tools_read_execute', 'deny_read'}:
        raise ValueError('Expected account, run_id, data_read, tools_read_execute, deny_read')
    if not NAME.fullmatch(config['account']) or not RUN_ID.fullmatch(config['run_id']):
        raise ValueError('Invalid account or run_id')
    denied = config['deny_read']
    if not isinstance(denied, list) or not denied:
        raise ValueError('deny_read must list existing private paths')
    for item in denied:
        if not isinstance(item, str) or not Path(item).is_absolute() or not Path(item).exists():
            raise ValueError(f'Missing/non-absolute private path: {item}')
    if not any(Path(item).is_file() for item in denied):
        raise ValueError('Include an actual private answer file, not only a directory')
    private = [Path(item).resolve() for item in denied]
    grants = {}
    ancestors = set()
    def overlaps(a, b):
        return a == b or a in b.parents or b in a.parents
    for kind in ('data_read', 'tools_read_execute'):
        entries = config[kind]
        if not isinstance(entries, list):
            raise ValueError(f'{kind} must be a list')
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {'path', 'recursive'} or type(entry['recursive']) is not bool:
                raise ValueError('Each access entry requires path and boolean recursive')
            path = Path(entry['path'])
            if not path.is_absolute() or not path.exists() or path != path.resolve():
                raise ValueError(f'Use an existing canonical physical path without symlink components: {path}')
            if path == Path('/') or (entry['recursive'] and path.parent == Path('/')):
                raise ValueError('Refusing broad filesystem-root access scope')
            if any(overlaps(path, q) for q in private):
                raise ValueError(f'Granted scope overlaps private material: {path}')
            if entry['recursive'] and not path.is_dir():
                raise ValueError('recursive is only valid for directories')
            candidates = [path]
            if entry['recursive']:
                def onerror(exc):
                    raise exc
                for parent, dirs, files in os.walk(path, followlinks=False, onerror=onerror):
                    candidates.extend(Path(parent) / name for name in sorted(dirs + files))
            for target in candidates:
                mode = target.lstat().st_mode
                if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)) or target.is_symlink():
                    raise ValueError(f'Link/special file inside granted scope: {target}')
                if any(overlaps(target, q) for q in private):
                    raise ValueError(f'Granted path overlaps private material: {target}')
                # Tool files get execute permission only if they already have an execute bit.
                perms = 'r-x' if target.is_dir() or (kind == 'tools_read_execute' and mode & 0o111) else 'r--'
                name = str(target)
                previous = grants.get(name)
                if previous and previous['permissions'] != perms:
                    raise ValueError(f'Conflicting data/tool access: {target}')
                grants[name] = {'path': name, 'permissions': perms, 'kind': kind,
                                'device': target.stat().st_dev, 'inode': target.stat().st_ino}
                ancestors.update(target.parents)
    if not grants:
        raise ValueError('At least one data/tool path is required')
    workspace = STATE / 'slots' / config['account'] / 'runs' / config['run_id']
    restrictions = []
    roots = config.get('restrict_roots', [])
    if not isinstance(roots, list):
        raise ValueError('restrict_roots must be a list of canonical directories')
    for name in roots:
        path = Path(name)
        if not path.is_absolute() or path != path.resolve() or not path.is_dir() or len(path.parts) < 3:
            raise ValueError('Restriction requires an existing canonical directory below a filesystem root')
        if overlaps(path, STATE) or any(overlaps(path, Path(p)) for p in grants):
            raise ValueError('Restriction overlaps managed state or public grants')
        if any(overlaps(path, Path(t['path'])) for t in restrictions):
            raise ValueError('Restriction roots must not overlap')
        if not any(path == p or path in p.parents for p in private):
            raise ValueError('Restriction must contain an explicit private check')
        restrictions.append(dict(path=str(path), permissions='---',
                                 device=path.stat().st_dev, inode=path.stat().st_ino))
    if any(overlaps(workspace, Path(p)) for p in grants) or any(overlaps(workspace, p) for p in private):
        raise ValueError('Workspace must be separate from allowed and private inputs')
    return {'schema_version': 1, 'checked_at': now(), 'account': config['account'],
            'run_id': config['run_id'], 'execution_profile': 'development-account',
            'formal_evaluation_eligible': False, 'permissions_modified': False,
            'acl_application_implemented': True, 'plan_kind': 'scope-only',
            'grants': sorted(grants.values(), key=lambda item: item['path']),
            'restrictions': restrictions,
            'ancestor_traversal_candidates': [str(p) for p in sorted(ancestors) if str(p) not in grants],
            'ancestor_rule': 'Check effective --x; only propose missing traverse access; never recursively grant parents.',
            'deny_read': denied, 'workspace_root': str(workspace),
            'writable_subdirectories': ['work', 'output', 'home', 'tmp'],
            'pending_checks': ['Target-UID access and ownership', 'Filesystem ACL support',
                               'ACL mask impact on other users', 'Snapshot and recoverable rollback']}


def pending_journals():
    pending = [p for p in (STATE/'slots').glob('*/runs/*/acl_journal.json')
               if json.loads(p.read_text()).get('state') != 'restored']
    for p in (STATE/'slots').glob('*/runs/*/result.json'):
        record = json.loads(p.read_text())
        if record.get('state') == 'recovery_required' and not record.get('recovery_resolved'):
            pending.append(p)
    return pending


def user_access(user, paths):
    code = "import os,json,sys; print(json.dumps({p:[os.access(p,m) for m in [os.R_OK,os.W_OK,os.X_OK]] for p in json.load(sys.stdin)}))"
    result = subprocess.run(['/usr/bin/python3', '-I', '-c', code], input=json.dumps(paths),
                            text=True, capture_output=True, check=True, cwd='/',
                            env={'PATH': '/usr/bin:/bin'}, preexec_fn=lambda: demote(user))
    return json.loads(result.stdout)


def stop_user(uid):
    deadline = time.monotonic() + 3
    while True:
        pids = owned_processes(uid)
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if time.monotonic() >= deadline:
            raise RuntimeError(f'Live processes remain for managed UID: {pids}')
        time.sleep(.05)


def check_acl_filesystems(targets, roots, uid):
    """Only disposable explicitly chosen probe directories are touched here."""
    required = {Path(t['path']).stat().st_dev for t in targets}
    passed = set()
    for name in roots:
        root = Path(name)
        if not root.is_absolute() or root != root.resolve() or not root.is_dir():
            raise ValueError('ACL probe root must be an existing canonical directory')
        if root.stat().st_dev not in required:
            continue
        with tempfile.TemporaryDirectory(prefix='bench-acl-probe-', dir=root) as folder:
            p = Path(folder)/'sample'
            p.write_text('disposable ACL support probe')
            p.chmod(0o600)
            t = Transaction(Path(folder)/'probe.json')
            try:
                t.prepare([{'path': str(p), 'permissions': 'r--'}], uid)
                t.apply()
                t.restore()
            except OSError as exc:
                if exc.errno in (errno.ENOTSUP, errno.EOPNOTSUPP):
                    raise RuntimeError(
                        f'POSIX ACLs are unsupported at probe root {root} '
                        f'(device {root.stat().st_dev}). Shared-path ACL changes have not started. '
                        'Use a different isolation/storage strategy; no chmod fallback is performed.'
                    ) from exc
                raise
            assert stat.S_IMODE(p.stat().st_mode) == 0o600
        passed.add(root.stat().st_dev)
    if required - passed:
        raise RuntimeError(f'Provide --acl-probe-root for every affected filesystem; untested device IDs: {required-passed}')


def prepare_access(plan, user, run, probe_roots):
    targets = list(plan['grants'])
    restrictions = plan.get('restrictions', [])
    baseline_paths = sorted(set([t['path'] for t in targets + restrictions] + plan['ancestor_traversal_candidates'] + plan['deny_read']))
    baseline = user_access(user, baseline_paths)
    save(run/'access_before.json', baseline)
    for path in plan['ancestor_traversal_candidates']:
        if not baseline[path][2]:
            targets.append({'path': path, 'permissions': '--x'})
    # Aliased hardlinks to known private files must not receive a public grant.
    private_ids = {(Path(p).stat().st_dev, Path(p).stat().st_ino) for p in plan['deny_read']}
    if any((Path(t['path']).stat().st_dev, Path(t['path']).stat().st_ino) in private_ids for t in targets):
        raise ValueError('A grant aliases a private inode')
    targets.extend(restrictions)
    targets.sort(key=lambda t: (len(Path(t['path']).parts), t['path']))
    check_acl_filesystems(targets, probe_roots, user.pw_uid)
    transaction = Transaction(run/'acl_journal.json')
    transaction.prepare(targets, user.pw_uid)
    transaction.apply()
    return transaction, baseline


def recover_access(account, run_id):
    root_only()
    if not RUN_ID.fullmatch(run_id):
        raise ValueError('Invalid run ID')
    slot, user = managed(account)
    with (STATE/'acl.lock').open('a') as global_lock, (slot/'slot.lock').open('a') as lock:
        fcntl.flock(global_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = slot/'runs'/run_id
        tx = Transaction(run/'acl_journal.json')
        if tx.record is None or tx.record['uid'] != user.pw_uid:
            raise RuntimeError('Missing or mismatched recovery journal')
        stop_user(user.pw_uid)
        run.chmod(0o700)
        tx.restore()
        after = user_access(user, list(json.loads((run/'access_before.json').read_text())))
        save(run/'access_restored.json', after)
        before = json.loads((run/'access_before.json').read_text())
        result = json.loads((run/'result.json').read_text())
        result.update(acl_state=tx.record['state'], recovered_at=now(), baseline_access_restored=after==before, recovery_resolved=after==before)
        save(run/'result.json', result)
        if after != before:
            raise RuntimeError('ACL restored, but baseline effective access differs; inspect external permissions')
        print('ACL restored and baseline access verified; original execution status retained.')


def trial(account, run_id, bundle, policy_path, seconds, command, access_plan=None, probe_roots=()):
    root_only()
    if not RUN_ID.fullmatch(run_id) or seconds <= 0:
        raise ValueError('Invalid run ID or timeout')
    slot, user = managed(account)
    with (STATE/'acl.lock').open('a') as global_lock, (slot / 'slot.lock').open('a') as lock:
        fcntl.flock(global_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if pending_journals():
            raise RuntimeError('Unfinished ACL journals exist; use recover-access before another run')
        processes = owned_processes(user.pw_uid)
        leftovers = outside_files(user.pw_uid)
        if processes or leftovers:
            raise RuntimeError(f'Slot is dirty; inspect processes={processes}, temporary files={leftovers[:20]}. Nothing deleted automatically.')
        policy = ({'allow_read': [t['path'] for t in access_plan['grants']], 'deny_read': access_plan['deny_read']}
                  if access_plan else read_policy(policy_path))
        bundle = Path(bundle).absolute()
        check_bundle(bundle)
        run = slot / 'runs' / run_id
        run.mkdir(mode=0o700)  # unique IDs; old runs are never overwritten
        result = dict(started_at=now(), account=account, run_id=run_id, command=command,
                      timeout_s=seconds, state='preparing', isolation='account-permissions',
                      execution_profile='development-account', formal_evaluation_eligible=False)
        save(run / 'policy.json', policy)
        save(run / 'result.json', result)
        try:
            public = run / 'input'
            shutil.copytree(bundle, public, symlinks=False)
            for p in [public, *public.rglob('*')]:
                os.chown(p, 0, user.pw_gid)
                p.chmod(0o550 if p.is_dir() else 0o440)
            for name in ['work', 'output', 'home', 'tmp']:
                p = run / name
                p.mkdir(mode=0o700)
                os.chown(p, user.pw_uid, user.pw_gid)
            os.chown(run, 0, user.pw_gid)
            run.chmod(0o750)
            if access_plan:
                save(run/'access_plan.json', access_plan)
                prepare_access(access_plan, user, run, probe_roots)
            checks = probe(user, policy, public)
            save(run / 'access_check.json', checks)
            if access_plan:
                effective = user_access(user, [t['path'] for t in access_plan['grants']])
                for t in access_plan['grants']:
                    if 'x' in t['permissions']:
                        checks.append(dict(kind='execute', path=t['path'], ok=effective[t['path']][2]))
                restricted = user_access(user, [t['path'] for t in access_plan.get('restrictions', [])])
                for path, access in restricted.items():
                    checks.append(dict(kind='restricted_root', path=path, ok=not any(access)))
                save(run/'access_check.json', checks)
            if not all(c['ok'] for c in checks):
                raise RuntimeError('Access audit failed. No agent launched; inspect access_check.json as root.')
            env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'HOME': str(run/'home'),
                   'TMPDIR': str(run/'tmp'), 'XDG_CACHE_HOME': str(run/'home/cache'),
                   'PYTHONNOUSERSITE': '1', 'BENCH_INPUT': str(public),
                   'BENCH_OUTPUT': str(run/'output'), 'BENCH_WORK': str(run/'work'),
                   'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
            result['state'] = 'running'
            save(run/'result.json', result)
            with (run/'execution.log').open('wb') as log:
                process = subprocess.Popen(command, cwd=run/'work', env=env,
                                           stdout=log, stderr=subprocess.STDOUT,
                                           start_new_session=True,
                                           preexec_fn=lambda: demote(user, limits=True))
                try:
                    result['exit_code'] = process.wait(timeout=seconds)
                    result['state'] = 'completed' if process.returncode == 0 else 'command_failed'
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    result['state'] = 'timeout'
        except BaseException as exc:
            result['state'] = 'blocked_or_failed'
            result['error'] = str(exc)
            raise
        finally:
            cleanup_error = None
            try:
                stop_user(user.pw_uid)
                run.chmod(0o700)
                journal = run/'acl_journal.json'
                if journal.exists():
                    tx = Transaction(journal)
                    tx.restore()
                    result['acl_state'] = tx.record['state']
                    before = json.loads((run/'access_before.json').read_text())
                    after = user_access(user, list(before))
                    save(run/'access_restored.json', after)
                    result['baseline_access_restored'] = before == after
                    if before != after:
                        raise RuntimeError('Baseline access differs after ACL restoration')
                elif access_plan and (run/'access_before.json').exists():
                    result['acl_state'] = 'not_applied'
                    before = json.loads((run/'access_before.json').read_text())
                    after = user_access(user, list(before))
                    save(run/'access_restored.json', after)
                    result['baseline_access_restored'] = before == after
                    if before != after:
                        raise RuntimeError('No shared ACL transaction started, but baseline access changed')
            except Exception as exc:
                cleanup_error = str(exc)
                result['cleanup_error'] = cleanup_error
                result['state'] = 'recovery_required'
            finally:
                run.chmod(0o700)
                result['finished_at'] = now()
                try:
                    result['shared_temp_residue'] = outside_files(user.pw_uid)
                except Exception as exc:
                    result['state'] = 'recovery_required'
                    result['cleanup_error'] = str(exc)
                save(run/'result.json', result)
            if cleanup_error:
                raise RuntimeError(cleanup_error)
        print(json.dumps(result, indent=2))
        if result['state'] != 'completed' or result['shared_temp_residue']:
            raise SystemExit(1)


def smoke(account):
    """Two synthetic root-only trials; never touch project or real scientific data."""
    root_only()
    slot, _ = managed(account)
    tag = uuid.uuid4().hex[:12]
    fixture = slot / ('smoke-' + tag)
    fixture.mkdir(mode=0o700)
    bundle = fixture / 'bundle'
    bundle.mkdir()
    (bundle / 'sample.txt').write_text('synthetic observation\n')
    secret = fixture / 'private_answer.txt'
    secret.write_text('synthetic hidden answer\n')
    secret.chmod(0o600)
    policy = fixture / 'policy.json'
    save(policy, {'allow_read': ['/usr/bin/python3'], 'deny_read': [str(secret)]})
    code = "import os,pathlib; p=pathlib.Path(os.environ['BENCH_INPUT'])/'sample.txt'; assert p.read_text()=='synthetic observation\\n'; assert not os.access(p,os.W_OK); pathlib.Path(os.environ['BENCH_OUTPUT'],'result.txt').write_text('ok')"
    first = 'smoke-' + tag + '-1'
    trial(account, first, bundle, policy, 30, ['/usr/bin/python3', '-I', '-c', code])
    previous = slot / 'runs' / first / 'output/result.txt'
    save(policy, {'allow_read': ['/usr/bin/python3'], 'deny_read': [str(secret), str(previous)]})
    trial(account, 'smoke-' + tag + '-2', bundle, policy, 30, ['/usr/bin/python3', '-I', '-c', code])
    print('Synthetic smoke passed: read-only input, private answer denied, previous output denied. Real project ACLs still require their own policy audit.')


def smoke_access(account):
    """Root acceptance: disposable ACL grants, real UID access, failure and timeout."""
    root_only()
    slot, user = managed(account)
    tag = uuid.uuid4().hex[:12]
    fixture = slot / ('acl-smoke-' + tag)
    fixture.mkdir(mode=0o700)
    data = fixture/'observation.txt'
    data.write_text('synthetic observation')
    data.chmod(0o600)
    secret = fixture/'answer.txt'
    secret.write_text('private answer')
    secret.chmod(0o600)
    tool = fixture/'tool.sh'
    tool.write_text('#!/bin/sh\nprintf "tool-ok\\n"\n')
    tool.chmod(0o700)
    bundle = fixture/'bundle'
    bundle.mkdir()
    (bundle/'instruction.txt').write_text('Synthetic permission check only.')
    config = fixture/'access.json'
    code = """import os,pathlib,subprocess,sys,time
p=pathlib.Path(sys.argv[1]); secret=pathlib.Path(sys.argv[2])
assert p.read_text()=='synthetic observation'
try:
 with p.open('a') as f: f.write('BAD')
except PermissionError: pass
else: raise AssertionError('Input is writable')
try: secret.read_text()
except PermissionError: pass
else: raise AssertionError('Private answer is readable')
assert subprocess.check_output([sys.argv[3]],text=True).strip()=='tool-ok'
pathlib.Path(os.environ['BENCH_OUTPUT'],'result.txt').write_text('ok')
if sys.argv[4]=='timeout': time.sleep(30)
if sys.argv[4]=='failure': sys.exit(7)
"""
    private = [str(secret)]
    reports = []
    for mode, expected in [('normal', 'completed'), ('failure', 'command_failed'), ('timeout', 'timeout')]:
        run_id = 'acl-smoke-' + tag + '-' + mode
        save(config, {'account': account, 'run_id': run_id,
                      'data_read': [{'path': str(data), 'recursive': False}],
                      'tools_read_execute': [{'path': str(tool), 'recursive': False}],
                      'deny_read': private})
        plan = plan_access(config)
        try:
            trial(account, run_id, bundle, None, 1 if mode=='timeout' else 30,
                  ['/usr/bin/python3','-I','-c',code,str(data),str(secret),str(tool),mode], plan, [str(fixture)])
        except SystemExit as exc:
            if expected == 'completed' or exc.code != 1:
                raise
        run = slot/'runs'/run_id
        report = json.loads((run/'result.json').read_text())
        assert report['state'] == expected, report
        assert report['acl_state'] == 'restored' and report['baseline_access_restored'], report
        assert data.read_text() == 'synthetic observation'
        private.append(str(run/'output/result.txt'))
        reports.append({'run_id': run_id, 'state': report['state'], 'acl_restored': True})
    save(fixture/'acceptance.json', reports)
    print('Root ACL smoke passed: normal/failure/timeout restoration, tool execution, immutable input and old-output denial. Real data-filesystem validation is separate.')


def preflight_access(config_path, output=None):
    """Audit current real-path access; do not grant, revoke or read file contents."""
    root_only()
    plan = plan_access(config_path)
    _, user = managed(plan['account'])
    checks = probe(user, {'allow_read': [p['path'] for p in plan['grants']],
                          'deny_read': plan['deny_read']})
    result = dict(checked_at=now(), account=plan['account'], checks=checks,
                  permissions_modified=False, execution_profile='development-account',
                  formal_evaluation_eligible=False,
                  current_policy_passed=all(c['ok'] for c in checks),
                  private_paths_denied=all(c['ok'] for c in checks if c['kind']=='deny_read'),
                  scope='Current access only; no ACL support or scientific runtime validation.')
    if output:
        save(Path(output), result)
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    d = sub.add_parser('doctor'); d.add_argument('--output')
    pa = sub.add_parser('plan-access'); pa.add_argument('--config', required=True); pa.add_argument('--output')
    pf = sub.add_parser('preflight-access'); pf.add_argument('--config', required=True); pf.add_argument('--output')
    i = sub.add_parser('init'); i.add_argument('--account', default='bench-agent01')
    sm = sub.add_parser('smoke'); sm.add_argument('--account', default='bench-agent01')
    sa = sub.add_parser('smoke-access'); sa.add_argument('--account', default='bench-agent01')
    rec = sub.add_parser('recover-access'); rec.add_argument('--account', default='bench-agent01'); rec.add_argument('--id', required=True)
    ra = sub.add_parser('run-access'); ra.add_argument('--config', required=True); ra.add_argument('--bundle', required=True)
    ra.add_argument('--acl-probe-root', action='append', required=True); ra.add_argument('--timeout', type=int, default=600)
    ra.add_argument('command', nargs=argparse.REMAINDER)
    t = sub.add_parser('run'); t.add_argument('--account', default='bench-agent01')
    t.add_argument('--id', required=True); t.add_argument('--bundle', required=True)
    t.add_argument('--policy', required=True); t.add_argument('--timeout', type=int, default=600)
    t.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.action == 'doctor':
        doctor(args.output)
    elif args.action == 'preflight-access':
        if not preflight_access(args.config, args.output)['current_policy_passed']:
            raise SystemExit(1)
    elif args.action == 'plan-access':
        result = plan_access(args.config)
        if args.output:
            save(Path(args.output), result)
        print(json.dumps(result, indent=2))
    elif args.action == 'init':
        initialize(args.account)
    elif args.action == 'recover-access':
        recover_access(args.account, args.id)
    elif args.action == 'run-access':
        root_only()
        plan = plan_access(args.config)
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command or not Path(command[0]).is_absolute():
            parser.error('Supply an absolute executable after --')
        trial(plan['account'], plan['run_id'], args.bundle, None, args.timeout, command, plan, args.acl_probe_root)
    elif args.action == 'smoke-access':
        smoke_access(args.account)
    elif args.action == 'smoke':
        smoke(args.account)
    else:
        command = args.command[1:] if args.command[:1] == ['--'] else args.command
        if not command or not Path(command[0]).is_absolute():
            parser.error('Supply an absolute executable after --')
        trial(args.account, args.id, args.bundle, args.policy, args.timeout, command)


if __name__ == '__main__':
    main()
