"""Project-local Python layer for MatchLocate2 (Match&Locate, Zhang & Wen 2015).

Modules:

* ``native``     - INPUT.in / EventCase.out / SelectFinal formats, grid arithmetic,
                   command construction, Python port of the SelectFinal merge.
* ``sacheader``  - dependency-free SAC header reader used for validation.
* ``traveltime`` - layered 1-D first arrivals with analytic slownesses for the
                   native linear moveout, and its linearisation error.
* ``dataset``    - prepared dataset layout, tables and header validation.
* ``runner``     - one native job per (segment, template), resume, merge, outputs.
* ``prepare``    - ObsPy waveform processing, continuous SAC and template cutting.
* ``build``      - common case inputs (MiniSEED, stations, templates, picks, model)
                   -> prepared dataset; backs ``interface/prepare.py``.
* ``select``     - template-selection helper (greedy spatial cover).
``prepare`` and ``build`` need ObsPy and are imported on demand.
"""
from .native import (KM_PER_DEG, Detection, DetectionParams, InputRow, SearchGrid, build_command,
                     merge_detections, native_axis_count, parse_eventcase, parse_selectfinal,
                     write_input_file, write_selectfinal_input)
from .sacheader import SacHeader, read_sac_header
from .traveltime import LayeredModel, Ray, epicentral_km, first_arrival, linearisation_error_s
from .dataset import (ChannelPhase, Template, list_segments, read_channels, read_templates,
                      segment_reference, validate_segment, validate_template, write_channels,
                      write_templates)
from .runner import DEFAULT_CONFIG, grid_for, merge_config, run_dataset
from .select import select_templates

__all__ = [
    "KM_PER_DEG", "Detection", "DetectionParams", "InputRow", "SearchGrid", "build_command",
    "merge_detections", "native_axis_count", "parse_eventcase", "parse_selectfinal",
    "write_input_file", "write_selectfinal_input", "SacHeader", "read_sac_header",
    "LayeredModel", "Ray", "epicentral_km", "first_arrival", "linearisation_error_s",
    "ChannelPhase", "Template", "list_segments", "read_channels", "read_templates", "segment_reference",
    "validate_segment", "validate_template", "write_channels", "write_templates", "DEFAULT_CONFIG", "grid_for",
    "merge_config", "run_dataset", "select_templates",
]
