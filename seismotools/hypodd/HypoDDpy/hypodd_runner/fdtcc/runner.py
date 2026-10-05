"""Internal FDTCC binary runner: build argv, execute native binary, collect ``dt.cc``.

Normal relocation scripts should not import this module directly. Configure
FDTCC through the public ``hypodd_runner`` function APIs. This module exists so
the pipeline can isolate the native FDTCC executable in a controlled working
directory.

FDTCC writes ``dt.cc`` in the **current working directory** only. Always pass
``work_dir`` so runs are isolated and Input.* scratch files do not clash.

**Path length:** FDTCC uses ``char[FDTCC_PATH_MAX]`` (1024) path buffers.
:func:`build_fdtcc_argv` still prefers paths relative to ``work_dir`` when
possible to keep argv lines short. If a path exceeds 1023 bytes it is rejected
before invoking the binary.

Command-line flag order matches the upstream demo (``-F -B -C -W -D -G``) so
the ``-C`` / ``-W`` fall-through quirk in the C parser leaves ``-W`` values
correct when ``-C`` is parsed before ``-W``.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

def _argv_path_for_fdtcc(
    target: str,
    *,
    work_dir: Optional[str],
    path_max: int = 1023,
) -> str:
    """
    Emit a path string safe for FDTCC argv.

    When ``work_dir`` is set and ``target`` lies under that directory, use a path
    relative to ``work_dir`` (same idea as ``runFDTCC.sh`` using ``./station.dat``).
    ``path_max`` must stay in sync with ``FDTCC_PATH_MAX`` in ``FDTCC/src/FDTCC.c``.
    """
    ap = os.path.abspath(os.path.normpath(target))
    if work_dir:
        wd = os.path.abspath(os.path.normpath(work_dir))
        try:
            if os.path.commonpath([wd, ap]) == wd:
                rel = os.path.relpath(ap, wd)
                if len(rel) <= path_max:
                    return rel
        except ValueError:
            pass
    out = ap
    if len(out) > path_max:
        raise ValueError(
            f"Path too long for FDTCC (max {path_max} characters; "
            f"see FDTCC_PATH_MAX in FDTCC.c): {out!r}. "
            f"Run with cwd equal to a parent of all inputs (see work_dir in "
            f"run_fdtcc), use shorter symlinks, or place copyable inputs under "
            f"the run directory."
        )
    return out


@dataclass
class FDTCCCliFlags:
    """Native FDTCC option values.

    The field names map to upstream FDTCC command-line flags, but generated
    relocation scripts should set readable flag values through the public
    ``hypodd_runner`` function APIs, not by constructing argv or calling
    :func:`run_fdtcc` directly.
    """

    # -W: window before pick, after pick, max shift (P then S)
    wb: float = 0.2
    wa: float = 1.0
    wf: float = 0.3
    wbs: float = 0.5
    was: float = 1.5
    wfs: float = 0.5
    # -D
    delta: float = 0.01
    threshold: float = 0.7
    thre_snr: float = 1.0
    thre_shift: float = 2.0
    # -G: travel-time table extent (deg, km-style horizontal grid — see FDTCC docs)
    trx: float = 3.0
    trh: float = 20.0
    tdx: float = 0.02
    tdh: float = 2.0
    # -B bandpass; use -1/-1 for no filter in FDTCC
    band_low: float = 2.0
    band_high: float = 8.0
    # -F: 0 continuous SAC by date, 1 event segments by event id
    waveform_mode: int = 0
    # -C: 1 = pass explicit paths for event.sel, dt.ct, phase.dat on argv
    c_event_path: int = 1
    c_dt_ct_path: int = 1
    c_phase_path: int = 1


@dataclass
class FDTCCInputPaths:
    """Absolute paths passed to FDTCC (REAL ``station.dat``, ``ttdb``, SAC root, HypoDD files)."""

    station_dat: str
    tt_table: str
    wave_dir: str
    event_sel: str
    dt_ct: str
    phase_dat: str

    def validate(self) -> None:
        for name, p in asdict(self).items():
            if not isinstance(p, str) or not p.strip():
                raise ValueError(f"FDTCCInputPaths.{name} must be a non-empty path")
            if name == "wave_dir":
                if not os.path.isdir(p):
                    raise FileNotFoundError(f"wave_dir is not a directory: {p!r}")
            else:
                if not os.path.isfile(p):
                    raise FileNotFoundError(f"{name} is not a file: {p!r}")


@dataclass
class FDTCCResult:
    """Return value of :func:`run_fdtcc`: exit code, path to produced ``dt.cc``, and captured I/O.

    Attributes
    ----------
    returncode : int
        Subprocess exit status from the FDTCC binary.
    dt_cc_path : str
        Path to ``dt.cc`` under the run working directory.
    stdout, stderr : str
        Decoded process streams (for logging).
    argv : list of str
        Full command line passed to the executable.
    """

    returncode: int
    dt_cc_path: str
    stdout: str
    stderr: str
    argv: List[str] = field(default_factory=list)


def _tail_text(text: str, *, max_lines: int = 40, max_chars: int = 4000) -> str:
    """Return a compact tail for native program evidence."""
    lines = (text or "").splitlines()
    tail = "\n".join(lines[-max_lines:])
    if len(tail) > max_chars:
        tail = "...[truncated]\n" + tail[-max_chars:]
    return tail


def resolve_fdtcc_binary(explicit: Optional[str] = None) -> str:
    """
    Resolve path to the FDTCC executable.

    Order: ``explicit`` → env ``FDTCC_BIN`` →
    ``hypodd/fdtcc/FDTCC/bin/FDTCC`` (if built in-tree).
    """
    if explicit and explicit.strip():
        return os.path.abspath(explicit.strip())
    env = os.environ.get("FDTCC_BIN", "").strip()
    if env:
        return os.path.abspath(env)
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.abspath(
        os.path.join(package_dir, "fdtcc", "FDTCC", "bin", "FDTCC")
    )


def build_fdtcc_argv(
    binary: str,
    flags: FDTCCCliFlags,
    paths: FDTCCInputPaths,
    work_dir: Optional[str] = None,
    path_max: int = 1023,
) -> List[str]:
    """Build the argv used internally to invoke the native FDTCC binary.

    Pass ``work_dir`` (typically the FDTCC cwd) so input paths can be shortened
    with ``relpath`` when possible. FDTCC uses ``char[FDTCC_PATH_MAX]`` (1024)
    for argv paths; Python still caps strings at ``path_max``.
    """
    ife, ifd, ifp = flags.c_event_path, flags.c_dt_ct_path, flags.c_phase_path
    w = f"{flags.wb}/{flags.wa}/{flags.wf}/{flags.wbs}/{flags.was}/{flags.wfs}"
    d = f"{flags.delta}/{flags.threshold}/{flags.thre_snr}/{flags.thre_shift}"
    g = f"{flags.trx}/{flags.trh}/{flags.tdx}/{flags.tdh}"
    b = f"{flags.band_low}/{flags.band_high}"
    c = f"{ife}/{ifd}/{ifp}"

    def pth(t: str) -> str:
        return _argv_path_for_fdtcc(t, work_dir=work_dir, path_max=path_max)

    argv: List[str] = [
        os.path.abspath(binary),
        f"-F{int(flags.waveform_mode)}",
        f"-B{b}",
        f"-C{c}",
        f"-W{w}",
        f"-D{d}",
        f"-G{g}",
        pth(paths.station_dat),
        pth(paths.tt_table),
        pth(paths.wave_dir),
    ]
    if ife == 1:
        argv.append(pth(paths.event_sel))
    if ifd == 1:
        argv.append(pth(paths.dt_ct))
    if ifp == 1:
        argv.append(pth(paths.phase_dat))
    return argv


def run_fdtcc(
    *,
    work_dir: str,
    paths: FDTCCInputPaths,
    flags: Optional[FDTCCCliFlags] = None,
    fdtcc_binary: Optional[str] = None,
    cleanup_input_lists: bool = True,
    check: bool = True,
    timeout_sec: Optional[float] = None,
) -> FDTCCResult:
    """
    Internal low-level FDTCC execution.

    Run FDTCC with cwd ``work_dir`` and read ``dt.cc`` from that directory.
    Normal relocation workflows should call the public package API instead of
    this function.

    Parameters
    ----------
    work_dir
        Created if missing. FDTCC writes ``dt.cc`` and temporary ``Input.*`` here.
    paths
        Input files (typically absolute). Validated before the run.
    flags
        CLI tuning; default matches ``fdtcc/FDTCC/Demo/runFDTCC.sh`` roughly.
    fdtcc_binary
        Optional path to binary; else :func:`resolve_fdtcc_binary`.
    cleanup_input_lists
        If True, remove ``Input.p``, ``Input.s1``, ``Input.s2`` after a successful run.
    check
        If True, raise ``CalledProcessError`` when return code is non-zero.
    timeout_sec
        Optional subprocess timeout.

    Returns
    -------
    FDTCCResult
        Includes path to ``work_dir/dt.cc`` even if the run failed (caller can inspect).
    """
    paths.validate()
    flags = flags or FDTCCCliFlags()
    binary = resolve_fdtcc_binary(fdtcc_binary)
    if not os.path.isfile(binary):
        raise FileNotFoundError(
            f"FDTCC binary not found: {binary!r} (set FDTCC_BIN or build fdtcc/FDTCC)"
        )
    if not os.access(binary, os.X_OK):
        raise PermissionError(f"FDTCC binary is not executable: {binary!r}")

    os.makedirs(work_dir, exist_ok=True)
    argv = build_fdtcc_argv(binary, flags, paths, work_dir=work_dir)
    out_cc = os.path.join(os.path.abspath(work_dir), "dt.cc")

    proc = subprocess.run(
        argv,
        cwd=os.path.abspath(work_dir),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        check=False,
    )
    stdout, stderr = proc.stdout or "", proc.stderr or ""
    if proc.returncode != 0 and check:
        evidence = {
            "returncode": int(proc.returncode),
            "cwd": os.path.abspath(work_dir),
            "command": argv,
        }
        evidence_path = os.path.join(os.path.abspath(work_dir), "fdtcc_failure_evidence.json")
        stdout_path = os.path.join(os.path.abspath(work_dir), "fdtcc_stdout.log")
        stderr_path = os.path.join(os.path.abspath(work_dir), "fdtcc_stderr.log")
        with open(stdout_path, "w", encoding="utf-8") as f:
            f.write(stdout)
        with open(stderr_path, "w", encoding="utf-8") as f:
            f.write(stderr)
        with open(evidence_path, "w", encoding="utf-8") as f:
            import json

            json.dump(evidence, f, indent=2)

        msg = (
            f"FDTCC failed with return code {proc.returncode}.\n"
            f"cwd: {os.path.abspath(work_dir)}\n"
            f"command: {' '.join(argv)}\n"
            f"stdout_log: {stdout_path}\n"
            f"stderr_log: {stderr_path}\n"
            f"evidence_json: {evidence_path}"
        )
        stdout_tail = _tail_text(stdout)
        stderr_tail = _tail_text(stderr)
        if stdout_tail:
            msg += f"\n--- FDTCC stdout tail ---\n{stdout_tail}"
        if stderr_tail:
            msg += f"\n--- FDTCC stderr tail ---\n{stderr_tail}"
        raise RuntimeError(msg)
    if cleanup_input_lists and proc.returncode == 0:
        for name in ("Input.p", "Input.s1", "Input.s2"):
            p = os.path.join(work_dir, name)
            if os.path.isfile(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass

    return FDTCCResult(
        returncode=int(proc.returncode),
        dt_cc_path=out_cc,
        stdout=stdout,
        stderr=stderr,
        argv=argv,
    )


def copy_dt_cc_to(
    src_dt_cc: str,
    dest_path: str,
) -> None:
    """Copy FDTCC output ``dt.cc`` to e.g. ``output_folder/dt_0-0.cc``."""
    d = os.path.dirname(os.path.abspath(dest_path))
    if d:
        os.makedirs(d, exist_ok=True)
    shutil.copy2(os.path.abspath(src_dt_cc), os.path.abspath(dest_path))


def dt_cc_nonempty(path: str) -> bool:
    return os.path.isfile(path) and os.path.getsize(path) > 0


def summarize_dt_cc(path: str) -> Tuple[int, int]:
    """Return ``(n_pair_headers, n_data_lines)`` for quick logging."""
    if not os.path.isfile(path):
        return 0, 0
    n_hash, n_data = 0, 0
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                n_hash += 1
            else:
                n_data += 1
    return n_hash, n_data


def fdtcc_flags_from_mapping(m: Optional[Mapping[str, Any]]) -> FDTCCCliFlags:
    """Merge dict (e.g. JSON ``flags`` object) onto :class:`FDTCCCliFlags` defaults.

    Supports both the original short names (``wb/wa/wf/...``) and more readable aliases
    (e.g. ``p_window_before_sec``) for the same underlying CLI flags.
    """
    base = asdict(FDTCCCliFlags())
    if not m:
        return FDTCCCliFlags()

    # Friendly aliases -> canonical dataclass field names.
    # Keep aliases explicit (no magic) so configs remain grep-able.
    aliases: Dict[str, str] = {
        # -W (P then S)
        "p_window_before_sec": "wb",
        "p_window_after_sec": "wa",
        "p_max_shift_sec": "wf",
        "s_window_before_sec": "wbs",
        "s_window_after_sec": "was",
        "s_max_shift_sec": "wfs",
        # -D
        "sample_interval_sec": "delta",
        "cc_threshold": "threshold",
        "snr_threshold": "thre_snr",
        "max_abs_pick_diff_sec": "thre_shift",
        # -G
        "max_distance_deg": "trx",
        "max_depth_km": "trh",
        "distance_step_deg": "tdx",
        "depth_step_km": "tdh",
        # -B
        "bandpass_low_hz": "band_low",
        "bandpass_high_hz": "band_high",
        # -F
        "input_format": "waveform_mode",
        # -C
        "pass_event_sel_path": "c_event_path",
        "pass_dt_ct_path": "c_dt_ct_path",
        "pass_phase_dat_path": "c_phase_path",
    }

    # Apply canonical keys first, then aliases (aliases override if both are present).
    for k, v in m.items():
        if k in base and v is not None:
            base[k] = v
    for k, v in m.items():
        kk = aliases.get(k)
        if kk and kk in base and v is not None:
            base[kk] = v
    return FDTCCCliFlags(**base)  # type: ignore[arg-type]


def fdtcc_flags_to_human_mapping(flags: FDTCCCliFlags) -> Dict[str, Any]:
    """
    Export flags using the **readable** long names (the ones accepted in JSON).

    Internally we still use the canonical short field names (wb/trh/...) to build
    the CLI argv, but for `fdtcc_config_used.json` we want stable, clear keys.
    """
    d = asdict(flags)
    # canonical dataclass field -> human-readable JSON key
    to_human: Dict[str, str] = {
        # -W
        "wb": "p_window_before_sec",
        "wa": "p_window_after_sec",
        "wf": "p_max_shift_sec",
        "wbs": "s_window_before_sec",
        "was": "s_window_after_sec",
        "wfs": "s_max_shift_sec",
        # -D
        "delta": "sample_interval_sec",
        "threshold": "cc_threshold",
        "thre_snr": "snr_threshold",
        "thre_shift": "max_abs_pick_diff_sec",
        # -G
        "trx": "max_distance_deg",
        "trh": "max_depth_km",
        "tdx": "distance_step_deg",
        "tdh": "depth_step_km",
        # -B
        "band_low": "bandpass_low_hz",
        "band_high": "bandpass_high_hz",
        # -F
        "waveform_mode": "input_format",
        # -C
        "c_event_path": "pass_event_sel_path",
        "c_dt_ct_path": "pass_dt_ct_path",
        "c_phase_path": "pass_phase_dat_path",
    }
    out: Dict[str, Any] = {}
    for k, v in d.items():
        hk = to_human.get(k, k)
        out[hk] = v
    return out
