"""Export three-component MiniSEED to FDTCC SAC layouts.

- ``waveform_mode=1`` (FDTCC ``-F1``): event segments -> ``wave_out_root/EVID/NET.STA.*``
- ``waveform_mode=0`` (FDTCC ``-F0``): continuous by date -> ``wave_out_root/YYYYMMDD/NET.STA.*``
"""
from __future__ import annotations

import concurrent.futures
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from obspy import UTCDateTime, read
from obspy.core.util.attribdict import AttribDict
from obspy.core.stream import Stream
from obspy.core.trace import Trace

class MiniSEEDDayStore:
    """
    Minimal MiniSEED-day filename resolver (no cc_auto dependency).

    Only supports what this runner needs: building a candidate file path from:
    - `miniseed_root` (expected: root/<YYYYMMDD>/... or root/... fallback)
    - `filename_template` with placeholders {network},{station},{day},{next_day}
    - optional uppercasing for station/network parts.
    """

    def __init__(
        self,
        miniseed_root: str,
        *,
        filename_template: Optional[str] = None,
        station_upper: bool = True,
        network_upper: bool = True,
        default_filename_template: str = "{network}.{station}.{day}T000000Z.{next_day}T000000Z",
    ) -> None:
        self.miniseed_root = miniseed_root
        self.filename_template = filename_template or default_filename_template
        self.station_upper = station_upper
        self.network_upper = network_upper

    @staticmethod
    def _day_to_next_day(day: str) -> str:
        # day is expected to be YYYYMMDD (9 chars or 8 digits).
        d = datetime.strptime(day, "%Y%m%d").date()
        return (d + timedelta(days=1)).strftime("%Y%m%d")

    def file_path_for(self, net: str, sta: str, day: str) -> Optional[str]:
        net_s = (net or "").strip()
        sta_s = (sta or "").strip()
        if not net_s or not sta_s:
            return None

        if self.network_upper:
            net_s = net_s.upper()
        if self.station_upper:
            sta_s = sta_s.upper()

        next_day = self._day_to_next_day(day)
        try:
            fn = self.filename_template.format(
                network=net_s,
                station=sta_s,
                day=day,
                next_day=next_day,
            )
        except Exception:
            return None

        # Primary convention: root/<day>/<filename>
        day_dir = os.path.join(self.miniseed_root, day)
        p = os.path.join(day_dir, fn)
        if os.path.isfile(p):
            return p

        # Fallback: some stores keep files directly under root.
        p2 = os.path.join(self.miniseed_root, fn)
        return p2


def _parse_ph2dt_event_line(line: str) -> Optional[Tuple[UTCDateTime, int]]:
    """Parse ``event_{i}-{j}.dat`` / ``event.sel`` style lines."""
    import re
    from datetime import datetime

    s = line.strip()
    if not s or s.startswith("#"):
        return None

    parts = s.split()
    if len(parts) < 3:
        return None

    # HypoDD/ph2dt event line formats vary; be permissive:
    # - Date token: "YYYYMMDD" or "YYYY-MM-DD"
    # - Time token: "HHMMSS[.SS]" or "HHMMSSCC" (centiseconds)
    # - evid: usually last token (int/float)
    date_s, time_s = parts[0], parts[1]
    try:
        evid = int(float(parts[-1]))
    except ValueError:
        return None

    date_s = date_s.strip()
    time_s = time_s.strip()

    # Parse date
    try:
        if re.match(r"^\d{8}$", date_s):
            dt_date = datetime.strptime(date_s, "%Y%m%d").date()
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", date_s):
            dt_date = datetime.strptime(date_s, "%Y-%m-%d").date()
        else:
            return None
    except Exception:
        return None

    h = m = 0
    sec_i: int = 0
    micro_i: int = 0
    # Parse time
    # HypoDD/ph2dt often emits a compact integer token for time:
    # - usually HHMMSSCC (8 digits)
    # - sometimes leading zeros are omitted (6/7 digits), so pad to 8.
    if re.match(r"^\d{1,8}$", time_s):
        ts = time_s.zfill(8)
        h, m, sec_i = int(ts[0:2]), int(ts[2:4]), int(ts[4:6])
        cs = int(ts[6:8])  # centiseconds
        micro_i = cs * 10000
    else:
        # HHMMSS(.SS)?
        m1 = re.match(r"^(\d{2})(\d{2})(\d{2})(?:\.(\d+))?$", time_s)
        if m1:
            h, m, sec_i = int(m1.group(1)), int(m1.group(2)), int(m1.group(3))
            frac = m1.group(4)
            if frac:
                # Interpret .frac as decimal seconds; convert to microseconds.
                frac_s = (frac + "000000")[:6]
                micro_i = int(frac_s)
            else:
                micro_i = 0
        else:
            # HH:MM:SS(.SS)?
            m2 = re.match(r"^(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?$", time_s)
            if not m2:
                return None
            h, m, sec_i = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
            frac = m2.group(4)
            if frac:
                frac_s = (frac + "000000")[:6]
                micro_i = int(frac_s)
            else:
                micro_i = 0

    # ph2dt/HypoDD may emit SS=60 at minute boundaries; datetime rejects second=60.
    base = datetime(dt_date.year, dt_date.month, dt_date.day, h, m, 0, 0)
    ot = UTCDateTime(base + timedelta(seconds=sec_i, microseconds=micro_i))
    return ot, evid


def read_ph2dt_events(event_dat_path: str) -> List[Tuple[UTCDateTime, int]]:
    out: List[Tuple[UTCDateTime, int]] = []
    with open(event_dat_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            p = _parse_ph2dt_event_line(line)
            if p is not None:
                out.append(p)
    return out


def _real_station_rows(real_station_dat: str) -> List[Tuple[str, str, str]]:
    """Return list of (net, sta, comp3) from REAL ``station.dat``."""
    rows: List[Tuple[str, str, str]] = []
    with open(real_station_dat, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            tok = s.split()
            if len(tok) < 6:
                continue
            lon, lat, net, sta, comp, *_ = tok[0], tok[1], tok[2], tok[3], tok[4]
            try:
                float(lon)
                float(lat)
            except ValueError:
                continue
            rows.append((net, sta, comp))
    return rows


def _pick_zne(
    st: Stream, net: str, sta: str
) -> Tuple[Optional[Trace], Optional[Trace], Optional[Trace]]:
    st2 = st.select(network=net, station=sta)
    if len(st2) == 0:
        st2 = st.select(station=sta)
    tz = tn = te = None
    for tr in st2:
        c = (tr.stats.channel or "").upper()
        if not c:
            continue
        orient = c[-1]
        if orient == "Z" or orient == "3":
            tz = tr
        elif orient == "N" or orient == "Y":
            tn = tr
        elif orient == "E" or orient == "X":
            te = tr
    return tz, te, tn


def _continuous_sac_worker(
    task: Tuple[str, str, str, str, str, str, bool]
) -> Tuple[int, int]:
    day, day_dir, net, sta, comp3, path, skip_existing = task
    c0, c1 = comp3[0], comp3[1]
    base = f"{net}.{sta}"
    outputs = [
        os.path.join(day_dir, f"{base}.{c0}{c1}Z"),
        os.path.join(day_dir, f"{base}.{c0}{c1}E"),
        os.path.join(day_dir, f"{base}.{c0}{c1}N"),
    ]
    if skip_existing:
        existing = [p for p in outputs if os.path.isfile(p) and os.path.getsize(p) > 0]
        if len(existing) == len(outputs):
            return (0, len(existing))

    day_start = UTCDateTime.strptime(day, "%Y%m%d")
    day_end = day_start + 86400.0 - 1e-3

    try:
        st = read(path)
    except Exception:
        return (0, 0)
    if len(st) == 0:
        return (0, 0)
    st.merge(fill_value=0)
    tz, te, tn = _pick_zne(st, net, sta)
    wrote = 0
    for tr, suf in (
        (tz, f"{c0}{c1}Z"),
        (te, f"{c0}{c1}E"),
        (tn, f"{c0}{c1}N"),
    ):
        dest = os.path.join(day_dir, f"{base}.{suf}")
        if skip_existing and os.path.isfile(dest) and os.path.getsize(dest) > 0:
            continue
        if tr is None:
            continue
        tr2 = tr.copy().trim(
            starttime=day_start, endtime=day_end, pad=True, fill_value=0
        )
        if tr2.stats.npts < 2:
            continue
        # FDTCC reads SAC using tmark=-3 (SAC header "o").
        # If "o" is left as undefined (-12345), read_sac2() returns NULL.
        sac = getattr(tr2.stats, "sac", None)
        if sac is None:
            tr2.stats.sac = AttribDict()
            sac = tr2.stats.sac
        sac.o = 0.0
        tr2.write(dest, format="SAC")
        wrote += 1
    return (wrote, 0)


def export_miniseed_to_fdtcc_sac_tree(
    *,
    miniseed_root: str,
    real_station_dat: str,
    event_dat_path: str,
    wave_out_root: str,
    filename_template: str,
    pre_sec: float = 120.0,
    post_sec: float = 300.0,
    station_upper: bool = True,
    network_upper: bool = True,
    show_progress: bool = True,
) -> int:
    """
    For each event in ``event_dat_path``, write ``wave_out_root/EVID/NET.STA.?HZ``
    (+ ``E``/``N`` horizontal names per FDTCC) from day-volumed MiniSEED.

    Returns
    -------
    int
        Number of event directories created with at least one SAC file.
    """
    store = MiniSEEDDayStore(
        miniseed_root,
        filename_template=filename_template,
        station_upper=station_upper,
        network_upper=network_upper,
    )
    stations = _real_station_rows(real_station_dat)
    events = read_ph2dt_events(event_dat_path)
    total_events = len(events)
    os.makedirs(wave_out_root, exist_ok=True)

    def _discover_miniseed_path_heuristic(
        *,
        search_root: str,
        net: str,
        sta: str,
        day: str,
    ) -> Optional[str]:
        """
        Best-effort locate a MiniSEED file when filename_template doesn't match.

        Heuristic:
        - Search within `search_root/day/` first if it exists, else `search_root/`.
        - Match by substring: file basename contains net, sta, and day.
        - Limit to common MiniSEED extensions.
        """
        roots_to_try: List[str] = []
        day_dir = os.path.join(search_root, day)
        if os.path.isdir(day_dir):
            roots_to_try.append(day_dir)
        roots_to_try.append(search_root)

        net_u = net.upper()
        sta_u = sta.upper()
        day_u = day
        exts = (".mseed", ".miniseed", ".ms")

        for r in roots_to_try:
            for _root, _dirs, files in os.walk(r):
                for fn in files:
                    fn_l = fn.lower()
                    if not fn_l.endswith(exts):
                        continue
                    b = os.path.basename(fn)
                    b_u = b.upper()
                    if net_u in b_u and sta_u in b_u and day_u in b_u:
                        return os.path.join(_root, fn)
        # If filename matching fails, do a head-only scan of a limited number of
        # MiniSEED files under the day directory. This is slower but far more robust
        # across naming schemes.
        for r in roots_to_try:
            if not os.path.isdir(r):
                continue
            candidates: List[str] = []
            for _root, _dirs, files in os.walk(r):
                for fn in files:
                    fn_l = fn.lower()
                    if fn_l.endswith(exts) and day_u in fn.upper():
                        candidates.append(os.path.join(_root, fn))
            candidates = sorted(candidates)[:200]
            for p in candidates:
                try:
                    st_head = read(p, headonly=True)
                except Exception:
                    continue
                if not st_head:
                    continue
                # Compare against first trace header (usually enough to identify station).
                tr0 = st_head[0]
                tr_net = (tr0.stats.network or "").upper()
                tr_sta = (tr0.stats.station or "").upper()
                if tr_net == net_u and tr_sta == sta_u:
                    return p
            # Only scan one root (prefer day dir) once.
            break

        return None

    n_dirs = 0
    attempted_pairs = 0
    found_by_template = 0
    found_by_fallback = 0
    missing_files = 0
    read_errors = 0
    empty_streams = 0
    for idx, (ot, evid) in enumerate(events, start=1):
        day = ot.strftime("%Y%m%d")
        evdir = os.path.join(wave_out_root, str(evid))
        os.makedirs(evdir, exist_ok=True)
        wrote = 0
        # Cache discovered files for this day to avoid repeating directory walks.
        path_cache: Dict[Tuple[str, str], Optional[str]] = {}
        for net, sta, comp3 in stations:
            cache_key = (net, sta)
            if cache_key in path_cache:
                path = path_cache[cache_key]
            else:
                attempted_pairs += 1
                path = store.file_path_for(net, sta, day)
                if not path or not os.path.isfile(path):
                    # Fallback for mismatched naming schemes.
                    path = _discover_miniseed_path_heuristic(
                        search_root=miniseed_root,
                        net=net,
                        sta=sta,
                        day=day,
                    )
                    if path and os.path.isfile(path):
                        found_by_fallback += 1
                    else:
                        missing_files += 1
                        path_cache[cache_key] = path
                        continue
                else:
                    found_by_template += 1
                path_cache[cache_key] = path
            # (path_cache may contain None) Validate again.
            if not path or not os.path.isfile(path):
                continue
            try:
                st = read(path)
            except Exception:
                read_errors += 1
                continue
            if len(st) == 0:
                empty_streams += 1
                continue
            st.merge(fill_value=0)
            tz, te, tn = _pick_zne(st, net, sta)
            c0, c1 = comp3[0], comp3[1]
            base = f"{net}.{sta}"
            t0, t1 = ot - float(pre_sec), ot + float(post_sec)
            for tr, suf in ((tz, f"{c0}{c1}Z"), (te, f"{c0}{c1}E"), (tn, f"{c0}{c1}N")):
                if tr is None:
                    continue
                tr2 = tr.copy().trim(starttime=t0, endtime=t1, pad=True, fill_value=0)
                if tr2.stats.npts < 2:
                    continue
                # FDTCC reads SAC using tmark=-3 (SAC header "o"). Ensure "o" is defined,
                # otherwise read_sac2() returns NULL and dt.cc becomes empty.
                sac = getattr(tr2.stats, "sac", None)
                if sac is None:
                    tr2.stats.sac = AttribDict()
                    sac = tr2.stats.sac
                sac.o = 0.0
                dest = os.path.join(evdir, f"{base}.{suf}")
                tr2.write(dest, format="SAC")
                wrote += 1
        if wrote > 0:
            n_dirs += 1
        if show_progress and total_events > 0:
            # Print progress at ~5% increments (bounded by number of events).
            step = max(1, total_events // 20)
            if idx == total_events or idx % step == 0:
                print(
                    "export_miniseed_to_fdtcc_sac_tree progress: "
                    f"{idx}/{total_events} events ({(idx/total_events)*100:.1f}%), "
                    f"n_event_dirs_with_sac={n_dirs}",
                    file=sys.stderr,
                )
    print(
        "export_miniseed_to_fdtcc_sac_tree summary: "
        f"events={len(events)} stations={len(stations)} attempted_pairs={attempted_pairs} "
        f"found_by_template={found_by_template} found_by_fallback={found_by_fallback} "
        f"missing_files={missing_files} read_errors={read_errors} empty_streams={empty_streams} "
        f"n_event_dirs_with_sac={n_dirs}",
        file=sys.stderr,
    )
    return n_dirs


def export_miniseed_to_fdtcc_continuous_sac_tree(
    *,
    miniseed_root: str,
    real_station_dat: str,
    event_dat_path: str,
    wave_out_root: str,
    filename_template: str,
    station_upper: bool = True,
    network_upper: bool = True,
    max_workers: Optional[int] = None,
    skip_existing: bool = True,
    parallel_backend: str = "process",
    show_progress: bool = True,
) -> int:
    """
    Export continuous SAC files by day (FDTCC ``-F0`` expectation).

    The required days are inferred from ``event_dat_path`` (parsed as ph2dt event lines).
    """
    store = MiniSEEDDayStore(
        miniseed_root,
        filename_template=filename_template,
        station_upper=station_upper,
        network_upper=network_upper,
    )
    stations = _real_station_rows(real_station_dat)
    events = read_ph2dt_events(event_dat_path)
    days = sorted({ot.strftime("%Y%m%d") for ot, _e in events})
    # Fallback: if event file parsing fails, infer days from the MiniSEED root.
    # This makes -F0 export robust against small event.dat format differences.
    if not days:
        try:
            # day-part directly under miniseed_root: root/<YYYYMMDD>/...
            for entry in os.listdir(miniseed_root):
                if len(entry) == 8 and entry.isdigit():
                    p = os.path.join(miniseed_root, entry)
                    if os.path.isdir(p):
                        days.append(entry)
            days = sorted(set(days))
        except Exception:
            days = []
    if not days:
        # If miniseed_root is already a day dir, accept it.
        base = os.path.basename(os.path.normpath(miniseed_root))
        if len(base) == 8 and base.isdigit():
            days = [base]

    os.makedirs(wave_out_root, exist_ok=True)

    def _discover_miniseed_path_heuristic(
        *,
        search_root: str,
        net: str,
        sta: str,
        day: str,
    ) -> Optional[str]:
        """
        Best-effort locate a MiniSEED file when filename_template doesn't match.
        """
        roots_to_try: List[str] = []
        day_dir = os.path.join(search_root, day)
        if os.path.isdir(day_dir):
            roots_to_try.append(day_dir)
        roots_to_try.append(search_root)

        net_u = net.upper()
        sta_u = sta.upper()
        day_u = day
        exts = (".mseed", ".miniseed", ".ms")

        for r in roots_to_try:
            for _root, _dirs, files in os.walk(r):
                for fn in files:
                    fn_l = fn.lower()
                    if not fn_l.endswith(exts):
                        continue
                    b = os.path.basename(fn)
                    b_u = b.upper()
                    if net_u in b_u and sta_u in b_u and day_u in b_u:
                        return os.path.join(_root, fn)
        for r in roots_to_try:
            if not os.path.isdir(r):
                continue
            candidates: List[str] = []
            for _root, _dirs, files in os.walk(r):
                for fn in files:
                    fn_l = fn.lower()
                    if fn_l.endswith(exts) and day_u in fn.upper():
                        candidates.append(os.path.join(_root, fn))
            candidates = sorted(candidates)[:200]
            for p in candidates:
                try:
                    st_head = read(p, headonly=True)
                except Exception:
                    continue
                if not st_head:
                    continue
                tr0 = st_head[0]
                tr_net = (tr0.stats.network or "").upper()
                tr_sta = (tr0.stats.station or "").upper()
                if tr_net == net_u and tr_sta == sta_u:
                    return p
            break
        return None

    def _resolve_and_build_tasks() -> List[Tuple[str, str, str, str, str, str, bool]]:
        """
        Build tasks list: (day, day_dir, net, sta, comp3, miniseed_path).
        We resolve MiniSEED paths in the main thread to avoid repeated os.walk scans.
        """
        tasks: List[Tuple[str, str, str, str, str, str, bool]] = []
        total_pairs = len(days) * len(stations)
        resolved_pairs = 0
        missing_pairs = 0
        checked_pairs = 0
        progress_step = max(1, total_pairs // 20)
        if show_progress:
            print(
                "export_miniseed_to_fdtcc_continuous_sac_tree resolving: "
                f"days={len(days)}, stations={len(stations)}, pairs={total_pairs}",
                file=sys.stderr,
            )
        for day_idx, day in enumerate(days, start=1):
            day_dir = os.path.join(wave_out_root, day)
            os.makedirs(day_dir, exist_ok=True)
            for net, sta, comp3 in stations:
                checked_pairs += 1
                c0, c1 = comp3[0], comp3[1]
                # base and component filename are derived in the worker; here we only
                # need the MiniSEED source file path.
                path = store.file_path_for(net, sta, day)
                if not path or not os.path.isfile(path):
                    path = _discover_miniseed_path_heuristic(
                        search_root=miniseed_root,
                        net=net,
                        sta=sta,
                        day=day,
                    )
                    if not path or not os.path.isfile(path):
                        missing_pairs += 1
                        if show_progress and (checked_pairs == total_pairs or checked_pairs % progress_step == 0):
                            print(
                                "export_miniseed_to_fdtcc_continuous_sac_tree resolving progress: "
                                f"{checked_pairs}/{total_pairs} pairs "
                                f"({(checked_pairs/total_pairs)*100:.1f}%), "
                                f"tasks={resolved_pairs}, missing={missing_pairs}",
                                file=sys.stderr,
                            )
                        continue
                tasks.append((day, day_dir, net, sta, comp3, path, skip_existing))
                resolved_pairs += 1
                if show_progress and (checked_pairs == total_pairs or checked_pairs % progress_step == 0):
                    print(
                        "export_miniseed_to_fdtcc_continuous_sac_tree resolving progress: "
                        f"{checked_pairs}/{total_pairs} pairs "
                        f"({(checked_pairs/total_pairs)*100:.1f}%), "
                        f"tasks={resolved_pairs}, missing={missing_pairs}",
                        file=sys.stderr,
                    )
        if show_progress:
            print(
                "export_miniseed_to_fdtcc_continuous_sac_tree resolving summary: "
                f"tasks={resolved_pairs}, missing={missing_pairs}",
                file=sys.stderr,
            )
        return tasks

    tasks = _resolve_and_build_tasks()
    total = len(tasks)
    if total == 0:
        print(
            "export_miniseed_to_fdtcc_continuous_sac_tree: no export tasks (days/stations/path resolution) "
            f"for event_dat_path={event_dat_path!r}",
            file=sys.stderr,
        )
        return 0

    n_sac_written = 0
    n_sac_reused = 0
    max_workers_eff = int(max_workers) if max_workers and max_workers > 0 else os.cpu_count() or 1
    backend = (parallel_backend or "process").strip().lower()
    if backend not in ("process", "thread"):
        raise ValueError("parallel_backend must be 'process' or 'thread'")
    done = 0
    if show_progress:
        print(
            "export_miniseed_to_fdtcc_continuous_sac_tree: "
            f"tasks={total}, max_workers={max_workers_eff}, backend={backend}, "
            f"skip_existing={skip_existing}",
            file=sys.stderr,
        )

    executor_cls = (
        concurrent.futures.ProcessPoolExecutor
        if backend == "process"
        else concurrent.futures.ThreadPoolExecutor
    )
    with executor_cls(max_workers=max_workers_eff) as ex:
        fut_to_task = {ex.submit(_continuous_sac_worker, t): t for t in tasks}
        for fut in concurrent.futures.as_completed(fut_to_task):
            wrote, reused = fut.result()
            n_sac_written += wrote
            n_sac_reused += reused
            done += 1
            if show_progress:
                # lightweight progress print; avoid spamming too much
                if done == total or done % max(1, total // 20) == 0:
                    print(
                        f"export_miniseed_to_fdtcc_continuous_sac_tree progress: {done}/{total} tasks "
                        f"({(done/total)*100:.1f}%), sac_written={n_sac_written}, sac_reused={n_sac_reused}",
                        file=sys.stderr,
                    )

    print(
        "export_miniseed_to_fdtcc_continuous_sac_tree summary: "
        f"days={len(days)} stations={len(stations)} sac_written={n_sac_written} "
        f"sac_reused={n_sac_reused} sac_files={n_sac_written + n_sac_reused} "
        f"from event_dat_path={event_dat_path!r}",
        file=sys.stderr,
    )
    return n_sac_written + n_sac_reused
