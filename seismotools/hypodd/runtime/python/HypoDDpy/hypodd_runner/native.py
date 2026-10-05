"""Helpers for executing native ph2dt/HypoDD binaries with clear errors."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from typing import Optional, Sequence

try:
    from .errors import NativeProgramError
except ImportError:  # pragma: no cover - legacy direct-script execution
    from errors import NativeProgramError


def read_log_tail(path: str, max_lines: int = 80) -> str:
    """Return the last lines from a native log file.

    Parameters
    ----------
    path
        Log file path.
    max_lines
        Maximum number of trailing lines to return.

    Returns
    -------
    str
        Joined log tail, or an empty string if the log does not exist.
    """
    if not path or not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    return "".join(lines[-max_lines:]).strip()


def run_native_program(
    command: Sequence[str],
    *,
    cwd: str,
    log_path: str,
    program: str,
    timeout: Optional[float] = None,
) -> subprocess.CompletedProcess:
    """Run a native binary and preserve failure evidence.

    Parameters
    ----------
    command
        Command argv for :func:`subprocess.run`.
    cwd
        Working directory for the native executable.
    log_path
        File where combined stdout/stderr are written.
    program
        Human-readable program/stage name used in error messages.
    timeout
        Optional wall-clock timeout in seconds for this native process.

    Returns
    -------
    subprocess.CompletedProcess
        Completed process object when the return code is zero.

    Raises
    ------
    NativeProgramError
        If the process cannot start or exits with a nonzero return code.
    """
    command = [str(x) for x in command]
    cwd = os.path.abspath(cwd)
    log_path = os.path.abspath(log_path)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    proc: Optional[subprocess.Popen] = None

    def _terminate_native_group(reason: str) -> None:
        if proc is None or proc.poll() is not None:
            return
        try:
            pgid = os.getpgid(proc.pid)
        except Exception:
            pgid = None
        try:
            if pgid is not None:
                os.killpg(pgid, signal.SIGTERM)
            else:
                proc.terminate()
        except ProcessLookupError:
            return
        except Exception:
            pass
        deadline = time.monotonic() + 5.0
        while proc.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        if proc.poll() is None:
            try:
                if pgid is not None:
                    os.killpg(pgid, signal.SIGKILL)
                else:
                    proc.kill()
            except ProcessLookupError:
                return
            except Exception:
                pass

    def _preexec() -> None:
        os.setsid()
        # On Linux, ask the kernel to signal native ph2dt/HypoDD if the Python
        # worker that launched it disappears before it can reap the child.
        if sys.platform.startswith("linux"):
            try:
                import ctypes

                libc = ctypes.CDLL(None)
                PR_SET_PDEATHSIG = 1
                libc.prctl(PR_SET_PDEATHSIG, signal.SIGTERM)
                if os.getppid() == 1:
                    os.kill(os.getpid(), signal.SIGTERM)
            except Exception:
                pass

    old_handlers = {}
    interrupted_by_signal: Optional[int] = None

    def _signal_handler(signum, frame):
        nonlocal interrupted_by_signal
        interrupted_by_signal = int(signum)
        _terminate_native_group(f"signal={signum}")
        raise KeyboardInterrupt

    try:
        with open(log_path, "w", encoding="utf-8", errors="replace") as log:
            proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=log,
                stderr=subprocess.STDOUT,
                preexec_fn=_preexec if os.name == "posix" else None,
            )
            for sig in (signal.SIGTERM, signal.SIGINT):
                try:
                    old_handlers[sig] = signal.getsignal(sig)
                    signal.signal(sig, _signal_handler)
                except Exception:
                    pass
            try:
                returncode = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                _terminate_native_group("timeout")
                raise NativeProgramError(
                    program=program,
                    command=command,
                    cwd=cwd,
                    returncode="timeout",
                    log_path=log_path,
                    log_tail=(
                        f"Native process timed out after {timeout} seconds.\n"
                        f"{read_log_tail(log_path)}"
                    ),
                ) from exc
            result = subprocess.CompletedProcess(command, returncode)
    except KeyboardInterrupt as exc:
        if interrupted_by_signal is not None:
            raise NativeProgramError(
                program=program,
                command=command,
                cwd=cwd,
                returncode=f"interrupted-by-signal-{interrupted_by_signal}",
                log_path=log_path,
                log_tail=read_log_tail(log_path),
            ) from exc
        raise
    except OSError as exc:
        raise NativeProgramError(
            program=program,
            command=command,
            cwd=cwd,
            returncode="not-started",
            log_path=log_path,
            log_tail=f"Could not start executable {command[0]!r}: {exc}",
        ) from exc
    finally:
        for sig, handler in old_handlers.items():
            try:
                signal.signal(sig, handler)
            except Exception:
                pass

    if result.returncode != 0:
        _terminate_native_group(f"returncode={result.returncode}")
        raise NativeProgramError(
            program=program,
            command=command,
            cwd=cwd,
            returncode=result.returncode,
            log_path=log_path,
            log_tail=read_log_tail(log_path),
        )
    return result
