"""Convert PAL-style ``phase.dat`` (ISO / Unix event headers) to HypoDD-readable phase files.

:class:`PAL2HypoDD_PhaseConverter` writes a sibling ``*_new.*`` file preserving picks in
the compact origin-time and station-line format expected by :func:`ph2dt.read_fpha`.
"""
import os
import numpy as np
from datetime import datetime, timezone

class PAL2HypoDD_PhaseConverter:
    """
    A class to parse and transform a phase.dat file into a format 
    that can be used for HypoDD relocation.
    """

    def __init__(self, phase_dat_path: str):
        """
        Initialize with the path to the original phase.dat file.
        """
        self.phase_dat_path = phase_dat_path
        phase_dat_name = os.path.basename(phase_dat_path).split(".")[0]
        phase_dat_ext = os.path.basename(phase_dat_path).split(".")[-1]
        self.new_phase_dat_path = os.path.join(
            os.path.dirname(phase_dat_path), f"{phase_dat_name}_new.{phase_dat_ext}"
        )

    @staticmethod
    def is_event_line(line: str) -> bool:
        """
        Check if a line is an event line.
        Event lines may start with an ISO datetime string 
        (e.g. '2019-07-04T16:13:42.989200Z') 
        or a UNIX timestamp (e.g. '1562256822.98').
        """
        line = line.strip()
        if not line:
            return False
        parts = line.strip().split(",")
        if len(parts) == 1:
            parts = line.strip().split()
        first_field = parts[0].strip()

        # Try ISO8601
        test_str = first_field[:-1] if first_field.endswith("Z") else first_field
        try:
            datetime.fromisoformat(test_str)
            return True
        except ValueError:
            pass
        # Try UNIX timestamp
        try:
            float(first_field.strip())
            return True
        except ValueError:
            return False

    @staticmethod
    def convert_time_to_YYYYMMDDHHMMSS(timestr) -> str:
        """
        Convert input into 'YYYYMMDDHHMMSS.SS' format.
        Accepts:
        - ISO8601 string like '2019-07-04T16:13:42.989200Z'
        - UNIX timestamp (int/float/str) like '1562256822.98'
        - datetime object
        - Already formatted string 'YYYYMMDDHHMMSS.SS' (returns unchanged)
        """

        # Case 1: Already formatted string
        if isinstance(timestr, str):
            if len(timestr.split(".")[0]) == 14:
                try:
                    # Validate if it is already in target format
                    datetime.strptime(timestr.split(".")[0], "%Y%m%d%H%M%S")
                    if "." in timestr:
                        float("0" + timestr.split(".")[1])  # check fractional part
                    return timestr
                except Exception:
                    pass
        
        # string like UNIX timestamp (int/float/str)
        if isinstance(timestr, str):
            try:
                timestr = float(timestr)
            except Exception:
                pass

        # Case 2: datetime object
        if isinstance(timestr, datetime):
            dt = timestr
        # Case 3: numeric timestamp (int/float/numpy types)
        elif isinstance(timestr, (int, float, np.integer, np.floating)):
            dt = datetime.fromtimestamp(float(timestr), tz=timezone.utc)
        # Case 4: ISO8601 string
        elif isinstance(timestr, str):
            if timestr.endswith("Z"):
                timestr = timestr[:-1]
            try:
                dt = datetime.fromisoformat(timestr)
            except ValueError:
                dt = datetime.fromtimestamp(float(timestr), tz=timezone.utc)
        else:
            raise TypeError(f"Unsupported input type: {type(timestr)}")

        # Format output
        base = dt.strftime("%Y%m%d%H%M%S")
        sec_frac = round(dt.microsecond / 1e6, 2)  # keep 2 decimal places
        return base + f"{sec_frac:.2f}"[1:]

    @staticmethod
    def convert_time_to_iso8601(value) -> str:
        """
        Convert input to ISO8601 string format with microseconds and Z suffix.
        Accepts:
        - datetime object -> converts directly
        - float/int timestamp -> converts to UTC datetime
        - string already in ISO8601 -> returns unchanged
        """
        # Case 1: datetime object
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Case 2: numeric timestamp
        if isinstance(value, (int, float, np.integer, np.floating)):
            dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Case 3: string
        if isinstance(value, str):
            # Check if already in ISO8601 format (simple validation)
            try:
                if value.endswith("Z"):
                    datetime.fromisoformat(value[:-1])
                else:
                    datetime.fromisoformat(value)
                return value  # already ISO8601
            except ValueError:
                # Try to parse as timestamp string
                try:
                    ts = float(value)
                    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                    return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                except ValueError:
                    raise ValueError(f"Cannot parse value {value} as datetime or timestamp")
        
        raise TypeError(f"Unsupported input type: {type(value)}")
    
    def transform(self) -> str:
        """
        Transform the phase.dat file into HypoDD format.
        Event lines are assigned an event ID and their times are converted.
        Station lines remain unchanged.
        Returns the path to the new file.
        """
        evt_id = 0
        with open(self.phase_dat_path, "r") as f_in, open(self.new_phase_dat_path, "w") as f_out:
            for line in f_in:
                if line.startswith('#'): continue
                # event line
                if self.is_event_line(line):
                    parts = line.strip().split(",")
                    if len(parts)==1: parts = line.split()
                    parts[0] = self.convert_time_to_YYYYMMDDHHMMSS(parts[0])

                    # Check if last field is an integer event ID
                    try:
                        last_val = parts[-1]
                        if not last_val.isdigit():  # not an integer
                            parts.append(str(evt_id))
                            evt_id += 1
                    except Exception:
                        parts.append(str(evt_id))
                        evt_id += 1

                    f_out.write(",".join(parts) + "\n")
                # phase line
                else:
                    parts = line.strip().split(",")
                    if len(parts)==1: parts = line.split()
                    # convert time to iso8601 if not null/-1/nan/None/
                    if parts[1] not in ['null', '-1', 'nan', 'None', '']:
                        parts[1] = self.convert_time_to_iso8601(parts[1])
                    else:
                        parts[1] = '-1'
                    if parts[2] not in ['null', '-1', 'nan', 'None', '']:
                        parts[2] = self.convert_time_to_iso8601(parts[2])
                    else:
                        parts[2] = '-1'
                    f_out.write(",".join(parts) + "\n")
        return self.new_phase_dat_path
