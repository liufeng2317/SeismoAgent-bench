"""Journaled Linux POSIX access ACL transactions; no chmod fallback or recursive writes."""
import base64
import contextlib
import ctypes
import ctypes.util
import errno
import json
import pwd
import grp
import os
from pathlib import Path
import stat
import tempfile


def durable_save(path, value):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.journal-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


@contextlib.contextmanager
def open_target(path):
    """Walk all components without following links, then pin the target inode."""
    path = Path(path)
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Absolute non-traversing path required')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for i, part in enumerate(path.parts[1:]):
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
            if i < len(path.parts[1:]) - 1:
                flags |= os.O_DIRECTORY
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        if not (stat.S_ISREG(os.fstat(fd).st_mode) or stat.S_ISDIR(os.fstat(fd).st_mode)):
            raise ValueError('Only regular files and directories may receive ACLs')
        yield fd
    finally:
        os.close(fd)


class ACL:
    def __init__(self):
        name = ctypes.util.find_library('acl')
        if not name:
            raise RuntimeError('libacl is required')
        self.lib = ctypes.CDLL(name, use_errno=True)
        for name, args, result in [
            ('acl_get_fd', [ctypes.c_int], ctypes.c_void_p),
            ('acl_from_text', [ctypes.c_char_p], ctypes.c_void_p),
            ('acl_to_text', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ssize_t)], ctypes.c_void_p),
            ('acl_set_fd', [ctypes.c_int, ctypes.c_void_p], ctypes.c_int),
            ('acl_valid', [ctypes.c_void_p], ctypes.c_int),
            ('acl_free', [ctypes.c_void_p], ctypes.c_int),
        ]:
            func = getattr(self.lib, name)
            func.argtypes, func.restype = args, result

    def error(self):
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number))

    def text(self, acl):
        ptr = self.lib.acl_to_text(acl, None)
        if not ptr:
            self.error()
        try:
            lines = []
            for line in ctypes.string_at(ptr).decode().splitlines():
                kind, qualifier, value = line.split(':', 2)
                if qualifier and not qualifier.isdigit():
                    qualifier = str(pwd.getpwnam(qualifier).pw_uid if kind == 'user' else grp.getgrnam(qualifier).gr_gid)
                lines.append(f'{kind}:{qualifier}:{value}')
            return '\n'.join(lines) + '\n' 
        finally:
            self.lib.acl_free(ptr)

    def get(self, fd):
        acl = self.lib.acl_get_fd(fd)
        if not acl:
            self.error()
        try:
            return self.text(acl)
        finally:
            self.lib.acl_free(acl)

    def convert(self, text, fd=None):
        acl = self.lib.acl_from_text(text.encode())
        if not acl:
            self.error()
        try:
            if self.lib.acl_valid(acl) != 0:
                self.error()
            canonical = self.text(acl)
            if fd is not None and self.lib.acl_set_fd(fd, acl) != 0:
                self.error()  # Native ACL error: never falls back to chmod.
            return canonical
        finally:
            self.lib.acl_free(acl)


def fields(text):
    return {':'.join(line.split(':')[:2]): line.split(':')[2].split()[0]
            for line in text.splitlines() if line.strip()}


def bits(perms):
    return sum(b for c, b in zip('rwx', [4, 2, 1]) if c in perms)


def perm(value):
    return ''.join(c if value & b else '-' for c, b in zip('rwx', [4, 2, 1]))


def granted_acl(acl, before, uid, permissions):
    entries = fields(before)
    requested = bits(permissions)
    if requested & 2:
        raise ValueError('Shared access grants cannot contain write permission')
    if 'mask:' in entries:
        if requested & ~bits(entries['mask:']):
            raise ValueError('Existing ACL mask would need widening; prepare a reviewed staging area')
    else:
        # With no extended ACL, widening the new mask does not widen group:: itself.
        entries['mask:'] = perm(bits(entries['group:']) | requested)
    entries[f'user:{uid}'] = permissions
    return acl.convert('\n'.join(f'{k}:{v}' for k, v in entries.items()) + '\n')


def identity(fd):
    s = os.fstat(fd)
    try:
        default = base64.b64encode(os.getxattr(fd, 'system.posix_acl_default')).decode()
    except OSError as exc:
        if exc.errno not in (errno.ENODATA, errno.ENOTSUP):
            raise
        default = None
    return dict(device=s.st_dev, inode=s.st_ino, owner=s.st_uid, group=s.st_gid,
                kind=stat.S_IFMT(s.st_mode), default_acl=default,
                special_bits=s.st_mode & 0o7000)


class Transaction:
    def __init__(self, journal):
        self.path = Path(journal)
        self.acl = ACL()
        self.record = json.loads(self.path.read_text()) if self.path.exists() else None

    def save(self):
        durable_save(self.path, self.record)

    def prepare(self, targets, uid):
        if self.record is not None:
            raise RuntimeError('Journal already exists; recover instead of overwriting')
        entries = []
        for target in targets:
            with open_target(target['path']) as fd:
                info = identity(fd)
                if info['owner'] == uid:
                    raise ValueError('Evaluation UID must not own a shared input/tool target')
                if info['special_bits']:
                    raise ValueError('Special mode bits require separate administrator review')
                for key in ('device', 'inode'):
                    if key in target and target[key] != info[key]:
                        raise RuntimeError('Target changed since scope planning')
                before = self.acl.get(fd)
                after = granted_acl(self.acl, before, uid, target['permissions'])
                entries.append(dict(path=target['path'], identity=info, before=before,
                                    after=after, mode_before=stat.S_IMODE(os.fstat(fd).st_mode), status='pending'))
        self.record = dict(schema_version=1, uid=uid, state='prepared', entries=entries)
        self.save()  # All paths and original ACLs durable before the first mutation.

    def apply(self):
        if self.record['state'] != 'prepared':
            raise RuntimeError('Only a prepared transaction can be applied')
        self.record['state'] = 'applying'
        self.save()
        try:
            for entry in self.record['entries']:
                with open_target(entry['path']) as fd:
                    if identity(fd) != entry['identity'] or self.acl.get(fd) != entry['before']:
                        raise RuntimeError('ACL/identity changed before application: ' + entry['path'])
                    entry['status'] = 'intent'
                    self.save()  # Recovery handles a kill between syscall and next journal write.
                    self.acl.convert(entry['after'], fd)
                    if self.acl.get(fd) != entry['after'] or identity(fd) != entry['identity']:
                        raise RuntimeError('Applied ACL verification failed: ' + entry['path'])
                    entry['status'] = 'applied'
                    self.save()
            self.record['state'] = 'active'
            self.save()
        except BaseException:
            self.restore()
            raise

    def restore(self):
        if self.record is None:
            raise RuntimeError('Missing journal')
        if self.record['state'] == 'restored':
            return
        self.record['state'] = 'restoring'
        self.save()
        conflicts = []
        for entry in reversed(self.record['entries']):
            if entry['status'] in ('pending', 'restored'):
                continue
            try:
                with open_target(entry['path']) as fd:
                    if identity(fd) != entry['identity']:
                        raise RuntimeError('Path inode/owner/default ACL changed')
                    current = self.acl.get(fd)
                    if current != entry['before']:
                        if current != entry['after']:
                            raise RuntimeError('ACL changed outside this transaction')
                        self.acl.convert(entry['before'], fd)
                    if self.acl.get(fd) != entry['before'] or stat.S_IMODE(os.fstat(fd).st_mode) != entry['mode_before']:
                        raise RuntimeError('Restoration verification failed')
                    entry['status'] = 'restored'
                    entry.pop('error', None)
            except Exception as exc:
                entry['error'] = str(exc)
                conflicts.append(entry['path'])
            self.save()
        self.record['state'] = 'recovery_required' if conflicts else 'restored'
        self.save()
        if conflicts:
            raise RuntimeError('ACL recovery conflicts; slot must not be reused: ' + ', '.join(conflicts))
