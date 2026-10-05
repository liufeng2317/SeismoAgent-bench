"""Resolve phase file path for the hypodd_runner pipeline.

The pipeline ultimately calls ``mk_pha`` / ``read_fpha`` on a HypoDD-ready phase
file. ``phase_format='pal'`` is only a request for hypodd_runner to convert a
PAL/PALM-style phase file first; it is not a request to use the pal_hypodd
package.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterator, List, Optional, Tuple

try:
    from .errors import format_contract_error
    from .pha_format import looks_like_event_header_line
    from .pal2hypodd import PAL2HypoDD_PhaseConverter
except ImportError:  # pragma: no cover - legacy direct-script execution
    from errors import format_contract_error
    from pha_format import looks_like_event_header_line
    from pal2hypodd import PAL2HypoDD_PhaseConverter


@dataclass
class PhaseFileResult:
    """Prepared phase-file information for the HypoDD/FDTCC pipeline.

    Attributes
    ----------
    source_path
        Absolute path provided by the caller.
    effective_path
        Absolute path consumed by ``read_fpha`` / ``mk_pha``. This may be a
        converted file when the source is PAL/PALM format.
    requested_format
        User/API request: ``auto``, ``hypodd``, or ``pal``.
    detected_format
        Actual detected source format: ``hypodd`` or ``pal``.
    converted
        True when a PAL/PALM source was converted to a HypoDD-ready phase file.
    event_count, pick_line_count
        Lightweight counts for the effective HypoDD-ready phase file.
    first_data_line
        First non-empty, non-comment source line number, or ``None`` for empty
        files.
    """

    source_path: str
    effective_path: str
    requested_format: str
    detected_format: str
    converted: bool
    event_count: int
    pick_line_count: int
    first_data_line: Optional[int]

    def as_dict(self):
        return {
            "source_path": self.source_path,
            "effective_path": self.effective_path,
            "requested_format": self.requested_format,
            "detected_format": self.detected_format,
            "converted": self.converted,
            "event_count": self.event_count,
            "pick_line_count": self.pick_line_count,
            "first_data_line": self.first_data_line,
        }


def _iter_nonempty_lines(path: str) -> Iterator[Tuple[int, str]]:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, start=1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            yield lineno, line


def first_data_line_split(path: str) -> Optional[Tuple[int, List[str]]]:
    """Return the first non-comment data line split into fields.

    Parameters
    ----------
    path
        Phase file path to inspect.

    Returns
    -------
    tuple or None
        ``(lineno, fields)`` for the first non-empty, non-comment line, or
        ``None`` when the file has no data lines. Comma-separated lines are
        split on commas; otherwise whitespace splitting is used.
    """
    for lineno, line in _iter_nonempty_lines(path):
        codes = line.split(",")
        if len(codes) == 1:
            codes = line.split()
        return lineno, codes
    return None


def file_has_hypodd_event_header(path: str) -> bool:
    """Return true when the first data line is a HypoDD event header.

    Parameters
    ----------
    path
        Phase-file path to classify.

    A HypoDD-ready phase file starts with an event header like
    ``origin_time,lat,lon,depth,mag[,evid]``. This helper is a lightweight format
    classifier; use :func:`prepare_phase_file` for full validation and optional
    PAL conversion.
    """
    got = first_data_line_split(path)
    if got is None:
        return False
    _lineno, codes = got
    return looks_like_event_header_line(codes)


def file_looks_like_pal_phase(path: str) -> bool:
    """Return true when the first data line looks like PAL/PALM phase input.

    Parameters
    ----------
    path
        Phase-file path to classify.

    PAL/PALM files are converted internally when ``phase_format="auto"`` or
    ``phase_format="pal"``. This check only inspects the first data line and is
    intended for diagnostics and error messages.
    """
    for _lineno, line in _iter_nonempty_lines(path):
        return PAL2HypoDD_PhaseConverter.is_event_line(line)
    return False


def phase_input_format_help() -> str:
    """Return accepted phase-file formats for user-facing error messages.

    The returned text is intentionally long and concrete because it is embedded
    in ``ConfigContractError`` messages consumed by agents. It describes both
    HypoDD-ready event blocks and PAL/PALM input, including missing-pick tokens
    and station-id expectations.
    """
    return (
        "Accepted phase_file formats for hypodd_runner:\n"
        "1. HypoDD-ready event blocks:\n"
        "   Event line: origin_time,lat,lon,depth,mag[,evid]\n"
        "     - origin_time: compact YYYYMMDDHHMMSS.SS or ISO-8601.\n"
        "     - lat/lon/depth: numeric; evid optional but integer-like when present.\n"
        "     - mag should be numeric when available; empty/bad mag is filled with 0.0.\n"
        "   Pick line: station_id,ISO_P_pick,ISO_S_pick\n"
        "     - station_id may be NET.STA, for example CI.TOW2, or a bare station code.\n"
        "     - For catalog-only HypoDD, bare station codes are accepted.\n"
        "     - For FDTCC/CC, the station table must provide network information\n"
        "       (NET.STA or separate network/station columns), or the API call must\n"
        "       set station_default_network to a network code that matches the waveform files.\n"
        "     - missing P/S pick may be -1, nan, None, null, NA, or empty.\n"
        "2. PAL/PALM phase.dat input:\n"
        "   Event line starts with an ISO datetime or UNIX timestamp and is converted\n"
        "   by hypodd_runner when phase_format='auto' or phase_format='pal'.\n"
        "Do not switch to pal_hypodd for this error; fix phase_file or set the\n"
        "correct phase_format in the hypodd_runner API call."
    )


def _first_line_context(
    path: str,
    first_data_line: Optional[int],
    codes: Optional[List[str]],
) -> str:
    """Compact first-line context for phase-file classification errors."""
    if first_data_line is None or codes is None:
        return f"phase_file={path!r}; no non-empty data lines were found."
    preview = ",".join(str(c).strip() for c in codes[:8])
    if len(preview) > 240:
        preview = preview[:237] + "..."
    return (
        f"phase_file={path!r}; first_data_line={first_data_line}; "
        f"split_fields={len(codes)}; first_fields={preview!r}"
    )


def _format_phase_classification_error(title: str, real_error: str, source_path: str, first_data_line, first_codes) -> str:
    return format_contract_error(
        title=title,
        real_error=real_error,
        location=source_path,
        context=_first_line_context(source_path, first_data_line, first_codes),
        expected=phase_input_format_help(),
        minimal_example=(
            "HypoDD event-block example:\n"
            "2025-10-01T19:57:32.160000Z,39.315833,141.055000,97.320,0.0,55\n"
            "N.313S,2025-10-01T19:57:40.000000Z,-1,0.000e+00,1.00"
        ),
        recommendation=(
            "Use phase_format='auto' unless the source format is known. If this is "
            "already an event-block phase file, pass it directly; do not create an "
            "ad-hoc converted phase file."
        ),
        avoid=(
            "Do not switch packages or replace real pick times with placeholders. "
            "Fix the input format shown in Real error."
        ),
    )


def _count_hypodd_phase_file(path: str) -> Tuple[int, int]:
    """Return ``(event_count, pick_line_count)`` for a HypoDD-ready phase file."""
    events = 0
    picks = 0
    for _lineno, line in _iter_nonempty_lines(path):
        codes = line.split(",")
        if len(codes) == 1:
            codes = line.split()
        if looks_like_event_header_line(codes):
            events += 1
        else:
            picks += 1
    return events, picks


def prepare_phase_file(phase_path: str, phase_format: str = "auto") -> PhaseFileResult:
    """Validate, classify, and if needed convert a phase file for this pipeline.

    Parameters
    ----------
    phase_path
        Input phase file path. Relative paths are resolved against the caller's
        current working directory before validation.
    phase_format
        ``auto`` detects HypoDD-ready vs PAL/PALM input. ``hypodd`` requires the
        input to already be HypoDD-ready. ``pal`` requires PAL/PALM input and
        converts it to a HypoDD-ready file with :class:`PAL2HypoDD_PhaseConverter`.

    Returns
    -------
    PhaseFileResult
        Source/effective paths, detected format, conversion flag, and basic
        counts for the effective HypoDD-ready phase file.
    """
    source_path = os.path.abspath(phase_path)
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"phase_file does not exist: {source_path}")

    requested_format = str(phase_format).strip().lower()
    if requested_format not in ("auto", "hypodd", "pal"):
        raise ValueError(
            f"phase_format must be auto, hypodd, or pal, got {requested_format!r}"
        )

    first = first_data_line_split(source_path)
    if first is None:
        raise ValueError(
            _format_phase_classification_error(
                "hypodd_runner phase file classification failed.",
                "phase_file has no non-empty data lines",
                source_path,
                None,
                None,
            )
        )
    first_data_line, first_codes = first
    has_hypodd_header = file_has_hypodd_event_header(source_path)
    looks_pal = file_looks_like_pal_phase(source_path)

    if requested_format == "hypodd":
        if not has_hypodd_header:
            raise ValueError(
                _format_phase_classification_error(
                    "hypodd_runner phase file classification failed.",
                    "phase_format='hypodd' requires a HypoDD-ready phase file, "
                    "but the first data line is not a valid event header.",
                    source_path,
                    first_data_line,
                    first_codes,
                )
            )
        effective_path = source_path
        detected_format = "hypodd"
        converted = False
    elif requested_format == "pal":
        if not looks_pal:
            raise ValueError(
                _format_phase_classification_error(
                    "hypodd_runner phase file classification failed.",
                    "phase_format='pal' requires a PAL/PALM-style phase file, "
                    "but the first data line is not a PAL event line.",
                    source_path,
                    first_data_line,
                    first_codes,
                )
            )
        effective_path = os.path.abspath(PAL2HypoDD_PhaseConverter(source_path).transform())
        detected_format = "pal"
        converted = True
    elif has_hypodd_header:
        effective_path = source_path
        detected_format = "hypodd"
        converted = False
    elif looks_pal:
        effective_path = os.path.abspath(PAL2HypoDD_PhaseConverter(source_path).transform())
        detected_format = "pal"
        converted = True
    else:
        raise ValueError(
            _format_phase_classification_error(
                "hypodd_runner phase file classification failed.",
                "phase_format='auto' could not classify the first data line as "
                "either a HypoDD event header or a PAL event line.",
                source_path,
                first_data_line,
                first_codes,
            )
        )

    event_count, pick_line_count = _count_hypodd_phase_file(effective_path)
    if event_count <= 0:
        raise ValueError(
            _format_phase_classification_error(
                "hypodd_runner prepared phase validation failed.",
                "Prepared phase file has no valid HypoDD event headers.",
                effective_path,
                None,
                None,
            )
        )
    return PhaseFileResult(
        source_path=source_path,
        effective_path=effective_path,
        requested_format=requested_format,
        detected_format=detected_format,
        converted=converted,
        event_count=event_count,
        pick_line_count=pick_line_count,
        first_data_line=first_data_line,
    )


def resolve_phase_path_for_pipeline(phase_path: str, phase_format: str) -> str:
    """
    Return a path to a phase file suitable for ``read_fpha`` / ``mk_pha``.

    Parameters
    ----------
    phase_path
        Path to the input phase file. It may already be in hypodd_runner
        event-block format or may be a PAL/PALM-style phase table when
        ``phase_format`` is ``"pal"`` or ``"auto"``.
    phase_format
        - ``hypodd``: use ``phase_path`` as-is.
        - ``pal``: convert PAL/PALM-style input with :class:`PAL2HypoDD_PhaseConverter`
          (writes ``*_new.*`` beside input), then continue in hypodd_runner.
        - ``auto``: if the first data line is already a HypoDD header, use as-is;
          else if it looks like a PAL event line, convert; else raise.

    Returns
    -------
    str
        Existing or converted phase file path that can be passed to
        ``read_fpha`` / ``mk_pha``.
    """
    return prepare_phase_file(phase_path, phase_format).effective_path
