"""Split a master phase catalog into per-grid files for ph2dt (``hypoDD_phase_i-j.dat``).

Filters events by origin-time and geographic ranges from config, assigns each event to
spatial sub-grids (with optional padding), and saves ``evid_lists.npy`` for downstream HypoDD.
"""
import os
import tempfile
import numpy as np
from obspy import UTCDateTime
import warnings

try:
    from .errors import format_contract_error
    from .pha_format import looks_like_event_header_line, normalize_event_magnitude
    from .station_id import station_code
except ImportError:  # pragma: no cover - legacy direct-script execution
    from errors import format_contract_error
    from pha_format import looks_like_event_header_line, normalize_event_magnitude
    from station_id import station_code

warnings.filterwarnings("ignore")


def _atomic_save_evid_lists(path, evid_lists):
    """Write ``evid_lists.npy`` via atomic replace to avoid truncated cache files."""
    arr = np.array(evid_lists, dtype=object)
    out_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(out_dir, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".npy",
            prefix=".evid_lists.",
            dir=out_dir,
            delete=False,
        ) as tmp:
            tmp_path = tmp.name
            np.save(tmp, arr)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_path, path)
    except Exception:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise

def _is_missing_pick(
    value,
    missing_pick_tokens=frozenset({"-1", "nan", "none", "", "null", "na"}),
):
    """True when a pick token represents a missing P/S arrival."""
    return str(value).strip().lower() in missing_pick_tokens


def _format_phase_parse_error(in_pha_file, lineno, line, codes, detail, current_event):
    event_hint = (
        "No valid event header has been parsed before this pick line."
        if current_event is None
        else f"Current event id/time: {current_event}"
    )
    return format_contract_error(
        title="hypodd_runner phase input parse failed.",
        real_error=detail,
        location=f"file={in_pha_file}\nline={lineno}",
        context=f"line: {line.strip()}\nsplit_fields={len(codes)}\n{event_hint}",
        expected=(
            "Event line: origin_time,lat,lon,depth,mag[,evid]\n"
            "- origin_time may be compact YYYYMMDDHHMMSS.SS or ISO-8601.\n"
            "- lat/lon/depth must be numeric; evid is optional but must be integer-like when present.\n"
            "- mag should be numeric when available; empty/bad mag is filled with 0.0.\n"
            "Pick line: station_id,ISO_P_pick,ISO_S_pick[,optional_numeric_columns...]\n"
            "- station_id may be NET.STA or bare STA for catalog-only HypoDD.\n"
            "- Missing P/S pick may be -1, nan, None, null, NA, or empty."
        ),
        minimal_example=(
            "2025-10-01T19:57:32.160000Z,39.315833,141.055000,97.320,0.0,55\n"
            "N.313S,2025-10-01T19:57:40.000000Z,-1,0.000e+00,1.00"
        ),
        recommendation=(
            "Fix the malformed phase row or set phase_format='auto'/'pal' when the "
            "source file is PAL/PALM format. Keep the original event-block phase "
            "file when it already follows this contract."
        ),
        avoid=(
            "Do not switch to pal_hypodd, replace real picks with -1, generate a "
            "new ad-hoc phase file, or change the workflow entry point unless the "
            "real error above proves the current input contract is wrong."
        ),
    )

def mk_pha(in_pha_file, output_folder, config):
    """
    Generate grid-based phase files from a global input phase file for HypoDD.

    Parameters
    ----------
    in_pha_file : str
        - Path to the input phase file. Each line should contain:
            - Event information (1 line per event):
                origin time (YYYYMMDDHHMMSS.SS or ISO-8601), latitude, longitude, depth,
                magnitude, and optional event ID.
            - Phase picks (multiple lines per event):
                station id, P pick time (ISO-8601 or missing token), S pick time
                (ISO-8601 or missing token). ``station_id`` may be ``NET.STA`` or
                a bare station code. Extra columns are ignored by this parser.
            - Example:
                ```
                    20190704161343.44,35.7158,-117.5010,14.6,1.60,1001
                    CI.TOW2,2019-07-04T16:13:48.528000Z,2019-07-04T16:13:53.308000Z
                    TOW2,2019-07-04T16:13:48.528000Z,2019-07-04T16:13:53.308000Z
                    CI.SRT,2019-07-04T16:13:47.888000Z,-1
                    ...
                ```
    config : object
        Config with:
            - dep_corr (float): depth correction (km).
            - ot_range (str): time range.
            - lat_range (list): latitude range [min, max].
            - lon_range (list): longitude range [min, max].
            - num_grids (tuple): number of grids along (lon, lat) axes.
            - xy_pad (tuple): padding along x (lon) and y (lat) in degrees to allow overlap between grids.

    Notes
    -----
    - Each grid produces a separate phase file named `phase_i-j.dat`.
    - Phase files contain headers for events and P/S picks relative to each event.
    - The function automatically clips events to the specified OT and spatial bounds.
    - The function saves `evid_lists.npy` for event IDs in each grid.

    Returns
    -------
    None
        Files are written to `output_folder` and `evid_lists.npy` is saved.
    
    Examples
    --------
    >>> mk_pha(in_pha_file='eg_pal_hyp_full.pha', config=config)
    """
    dep_corr         = config.dep_corr
    ot_range         = config.ot_range
    lat_min, lat_max = config.lat_range
    lon_min, lon_max = config.lon_range
    num_grids        = config.num_grids
    xy_pad           = config.xy_pad
    ot_min, ot_max   = [UTCDateTime(date) for date in ot_range.split('-')]
    
    # phase file for each grid
    fouts, evid_lists = [], []
    for i in range(num_grids[0]):
        evid_lists.append([])
        for j in range(num_grids[1]):
            evid_lists[i].append([])
            fouts.append(open(os.path.join(output_folder, 'hypoDD_phase_%s-%s.dat'%(i,j)),'w'))

    # lat-lon range for each grid
    dx = (lon_max - lon_min) / num_grids[0]
    dy = (lat_max - lat_min) / num_grids[1]

    def get_fout_idx(lat, lon):
        evid_idx, fout_idx = [], []
        for i in range(num_grids[0]):
            for j in range(num_grids[1]):
                # which phase files to write 
                if lon_min+i*dx-xy_pad[0]<lon<=lon_min+(i+1)*dx+xy_pad[0] \
                and lat_min+j*dy-xy_pad[1]<lat<=lat_min+(j+1)*dy+xy_pad[1]: 
                    fout_idx.append(i*num_grids[1]+j)
                # belong to which grid
                if lon_min+i*dx<lon<=lon_min+(i+1)*dx \
                and lat_min+j*dy<lat<=lat_min+(j+1)*dy:
                    evid_idx = [i,j]
        return evid_idx, fout_idx
    
    f=open(in_pha_file); lines=f.readlines(); f.close()
    auto_evid = 0
    fout_idx = []
    ot = None
    current_event = None
    for lineno,line in enumerate(lines, start=1):
        try:
            if line.startswith('#'): continue
            codes = line.split(',')
            if len(codes)==1: codes = line.split()
            codes = [code.strip() for code in codes]

            if looks_like_event_header_line(codes):
                # write head line
                ot = UTCDateTime(codes[0])
                lat, lon, dep = [float(code) for code in codes[1:4]]
                mag = normalize_event_magnitude(codes[4])
                dep += dep_corr
                if len(codes) >= 6:
                    evid = int(float(codes[-1]))
                else:
                    auto_evid += 1
                    evid = auto_evid
                current_event = f"{evid}/{ot.isoformat()}"
                evid_idx, fout_idx = get_fout_idx(lat, lon) # which grid to write
                if len(evid_idx)!=0: evid_lists[evid_idx[0]][evid_idx[1]].append(evid) # which event to write
                if len(fout_idx)==0: continue
                if not ot_min<ot<ot_max: continue
                # format time info
                date = '{:4} {:2} {:2}'.format(ot.year, ot.month, ot.day)
                time = '{:2} {:2} {:5.2f}'.format(ot.hour, ot.minute, ot.second + ot.microsecond/1e6)
                # format loc info
                loc = '{:7.4f} {:9.4f}  {:6.2f} {:4.2f}'.format(lat, lon, dep, mag)
                for idx in fout_idx: fouts[idx].write('# {} {}  {}  0.00  0.00  0.00  {:>9}\n'.format(date, time, loc, evid))
            else:
                try:
                    UTCDateTime(codes[0])
                    first_field_is_time = True
                except Exception:
                    first_field_is_time = False
                if first_field_is_time:
                    raise ValueError(
                        "line starts with an origin-time-like field but is not a valid event "
                        "header; expected origin_time,lat,lon,depth,mag[,evid]"
                    )
                if len(codes) < 3:
                    raise ValueError(
                        f"pick line must have at least 3 comma-separated fields "
                        f"(station_id,P_pick,S_pick), got {len(codes)}"
                    )
                if len(fout_idx)==0: continue
                if not ot_min<ot<ot_max: continue
                # write sta pick lines
                sta = station_code(codes[0])
                wp, ws = 1., 1.
                if not _is_missing_pick(codes[1]):
                    tp = UTCDateTime(codes[1])
                    ttp = tp - ot
                    for idx in fout_idx: fouts[idx].write('{:<5}{}{:6.3f}  {:6.3f}   P\n'.format(sta, ' '*6, ttp, wp))
                if not _is_missing_pick(codes[2]):
                    ts = UTCDateTime(codes[2])
                    tts = ts - ot
                    for idx in fout_idx: fouts[idx].write('{:<5}{}{:6.3f}  {:6.3f}   S\n'.format(sta, ' '*6, tts, ws))
        except Exception as e:
            raise RuntimeError(
                _format_phase_parse_error(
                    in_pha_file, lineno, line, codes, str(e), current_event
                )
            ) from e
    for fout in fouts: fout.close()
    _atomic_save_evid_lists(os.path.join(output_folder, 'evid_lists.npy'), evid_lists)
    return
