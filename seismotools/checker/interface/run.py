#!/usr/bin/env python3
"""Check the products of a catalog workflow stage by stage; report symptoms only.

Usage:
    run.py --stage data --stations <StationXML file or directory> --waveforms <waveform folder> \
        [--processed-waveforms <folder>] --output-dir checker/data
    run.py --stage picks --picks picks.csv --stations ... [--waveforms ...] --output-dir checker/picks
    run.py --stage association --catalog events.csv --picks picks.csv --stations ... --output-dir ...
    run.py --stage location --catalog catalog.csv --picks picks.csv --stations ... --output-dir ...
    run.py --stage relocation --catalog relocated.csv --catalog-before located.csv --picks picks.csv --stations ... [--dtcc dt.cc]
    run.py --stage magnitude --catalog catalog.csv --picks picks.csv --stations ... --output-dir ...
    run.py --stage all --catalog catalog.csv --picks picks.csv --stations ... --waveforms ... --output-dir ...

Stages, in processing order: ``data`` (stations, channels, gaps, representative records before and
after preprocessing), ``picks`` (picks, associated or not; with --waveforms also the onsets and
amplitudes under a sample of picks), ``association`` (picks and an event table whose locations may be
missing), ``location`` (the located catalog; with --model-ensemble also the relocation of a sample
with generic velocity models), ``relocation`` (the relocated catalog against --catalog-before), ``magnitude`` (with --waveforms and StationXML also the
recomputation of a standard local magnitude for a sample of events). Each stage also runs the
cheaper checks of the stages before it; ``all`` runs everything the given inputs allow.

On a pilot batch (``--pilot``), checks of the whole catalog's distribution (scope ``population``:
depth pile-ups and layers, isolated and duplicate events, b-value, rates) are reported without a
verdict: judge them on the full run. Every other check (scope ``item``) a pilot batch estimates.

Writes ``checker_report.json`` (``flags``: products out of their expected range, with the symptom;
``input_notes``: properties of the input data out of the usual range; ``measurements``: values
reported without an expected range; every check and every figure with its numbers) and the figures as PNG.
Exit code 0 whether or not flags are raised; 2 on unreadable inputs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "source"))

from catalog_checker.checks import STAGES, Data, apply_report_only, run_checks  # noqa: E402
from catalog_checker.io import read_catalog, read_channels, read_picks, read_stations, read_waveform_streams  # noqa: E402
from catalog_checker.report import build_report, write_figures, write_report  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", choices=STAGES, default="all")
    parser.add_argument("--catalog", type=Path, help="catalog or event table (stages association and later)")
    parser.add_argument("--picks", type=Path, help="picks file (stages picks and later)")
    parser.add_argument("--catalog-before", type=Path,
                        help="relocation stage: the absolutely located catalog that went into relocation (--catalog is the relocated one)")
    parser.add_argument("--dtcc", type=Path, help="relocation stage, optional: the hypoDD dt.cc file used")
    parser.add_argument("--stations", type=Path, required=True,
                        help="StationXML file, directory of StationXML files, or CSV station_id,latitude,longitude,elevation_m")
    parser.add_argument("--waveforms", type=Path,
                        help="waveform folder (NET.STA.LOC.CHA__start__end.mseed files, with or without waveform_inventory.json)")
    parser.add_argument("--processed-waveforms", type=Path,
                        help="the Agent's preprocessed records, same file naming; compared with the raw records in the data stage")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config", type=Path, help="JSON overriding default ranges (see README); records itself in the report")
    parser.add_argument("--location-setup", type=Path,
                        help="location stage, optional: JSON describing the location set-up in km below sea level "
                             "({\"interfaces_km_bsl\": [...], \"search_depth_km_bsl\": [top, bottom], \"grid_spacing_km\": g, "
                             "\"grid_origin_km_bsl\": z0, \"trial_depth_km_bsl\": z}); the report then says where the most common depth lies relative to it")
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--model-ensemble", action="store_true",
                        help="location stage: also relocate a sample of 100 events with six generic velocity models and report "
                             "how the catalog compares (10–45 minutes; reported only)")
    parser.add_argument("--no-model-ensemble", action="store_true", help="no effect (the ensemble is off unless --model-ensemble)")
    parser.add_argument("--keep-ensemble-dir", type=Path, help="keep the relocation inputs and outputs here")
    parser.add_argument("--pilot", action="store_true",
                        help="the products are from a pilot batch (a subset of the data): checks of the whole catalog's "
                             "distribution (scope 'population') are reported but not judged")
    args = parser.parse_args(argv)
    upto = STAGES.index(args.stage)
    if args.stage == "data" and args.waveforms is None:
        parser.error("--stage data needs --waveforms")
    if upto >= STAGES.index("picks") and args.picks is None:
        parser.error(f"--stage {args.stage} needs --picks")
    if upto >= STAGES.index("association") and args.catalog is None:
        parser.error(f"--stage {args.stage} needs --catalog")
    if args.stage == "relocation" and args.catalog_before is None:
        parser.error("--stage relocation needs --catalog-before")
    try:
        stations = read_stations(args.stations)
        events = read_catalog(args.catalog) if args.catalog and upto >= STAGES.index("association") else None
        picks = read_picks(args.picks) if args.picks and upto >= STAGES.index("picks") else \
            pd.DataFrame(columns=["event_id", "station_id", "phase", "time", "probability"])
        streams, window, stream_source = read_waveform_streams(args.waveforms) if args.waveforms else (None, None, None)
    except (OSError, KeyError, ValueError) as exc:
        print(f"checker: cannot read inputs: {exc}", file=sys.stderr)
        return 2
    if stations.empty:
        print(f"checker: no stations found in {args.stations}", file=sys.stderr)
        return 2
    config = json.loads(args.config.read_text()) if args.config else {}
    if args.location_setup:
        config["location_setup"] = json.loads(args.location_setup.read_text())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    figures_on = not args.no_figures
    wf_days = None if streams is None else pd.DataFrame({"station_id": streams.station_id, "channel": streams.channel,
                                                         "day": (streams.file_start + 1.0) // 86400 * 86400})
    data = Data(events, picks, stations, wf_days)
    checks, extras = run_checks(data, config, args.stage)
    sections: dict = {}
    figures: list[str] = []

    if streams is not None and args.stage in ("data", "all"):
        from catalog_checker.data_stage import data_checks, data_figures, representative_windows
        channels = read_channels(args.stations)
        dchecks, dextra = data_checks(stations, channels, streams, window, config)
        wchecks, wdetails, wnames = representative_windows(streams, window, args.processed_waveforms, args.output_dir,
                                                           config, figures=figures_on)
        checks = dchecks + wchecks + checks
        table = dextra.get("station_table")
        sections["data"] = {"waveform_metadata_source": stream_source,
                            "processing_window_utc": [f"{pd.Timestamp(t, unit='s', tz='UTC'):%Y-%m-%dT%H:%M:%SZ}" for t in window] if window else None,
                            "stations": table.drop(columns=["x", "y"], errors="ignore").to_dict("records") if table is not None else [],
                            "representative_windows": wdetails}
        if figures_on and table is not None:
            figures += data_figures(table, streams, window, args.output_dir) + wnames
        elif figures_on:
            figures += wnames

    if streams is not None and upto >= STAGES.index("picks") and not picks.empty:
        from catalog_checker.pick_waveforms import pick_figures, pick_waveform_checks
        from catalog_checker.waveforms import file_index
        index = streams[["file", "seed_id", "station_id", "location", "channel", "component", "file_start", "file_end"]].drop_duplicates("file")
        if index.empty:
            index = file_index(args.waveforms)
        pchecks, pdetails = pick_waveform_checks(data, index, config)
        checks += pchecks
        measured = pdetails.pop("measurements", pd.DataFrame())
        sections["picks"] = {"onset_sample": pdetails}
        if figures_on:
            names, fsum = pick_figures(data, index, measured, config, args.output_dir)
            figures += names
            sections["picks"]["figures"] = fsum

    if args.catalog_before is not None and upto >= STAGES.index("relocation"):
        from catalog_checker.relocation import read_dtcc, relocation_checks, relocation_figure
        rchecks, rextra = relocation_checks(read_catalog(args.catalog_before), data.events, data.lat0, data.lon0, config)
        checks += rchecks
        sections["relocation"] = {"dtcc": read_dtcc(args.dtcc) if args.dtcc else None}
        if figures_on:
            name = relocation_figure(rextra, args.output_dir)
            figures += [name] if name else []

    if args.stage in ("location", "all") and args.model_ensemble and not args.no_model_ensemble:
        from catalog_checker.ensemble import model_ensemble
        w = extras.get("wadati")
        vpvs = float(w.vpvs.median()) if w is not None and len(w) >= 20 else None
        ens_checks, ens = model_ensemble(data, extras["config"], vpvs, args.keep_ensemble_dir)
        checks += ens_checks
        sections["model_ensemble"] = ens

    if streams is not None and args.stage in ("magnitude", "all") and data.events.magnitude.notna().any():
        from catalog_checker.magnitude_recompute import largest_events_magnitude, magnitude_recompute
        index = streams[["file", "seed_id", "station_id", "location", "channel", "component", "file_start", "file_end"]].drop_duplicates("file")
        checks.append(magnitude_recompute(data, index, args.stations, config))
        checks.append(largest_events_magnitude(data, index, args.stations, config))

    if figures_on and upto >= STAGES.index("association") and args.stage != "relocation":
        from catalog_checker.stage_figures import association_figures, location_figures
        names, fsum = association_figures(data, args.output_dir)
        figures += names
        sections["association_figures"] = fsum
        if upto >= STAGES.index("location"):
            names, fsum = location_figures(data, checks, sections.get("model_ensemble"), args.output_dir)
            figures += names
            sections["location_figures"] = fsum
        if upto >= STAGES.index("magnitude"):
            from catalog_checker.stage_figures import magnitude_figures
            names, fsum = magnitude_figures(data, args.output_dir)
            figures += names
            sections["magnitude_figures"] = fsum
    if sections.get("model_ensemble"):
        sections["model_ensemble"].pop("_figure", None)

    apply_report_only(checks, pilot=args.pilot)
    inputs = {"stations": args.stations}
    for key in ("picks", "catalog", "catalog_before", "dtcc", "waveforms", "processed_waveforms"):
        if getattr(args, key):
            inputs[key] = getattr(args, key)
    report = build_report(checks, data, inputs, extras["config"])
    report["stage"] = args.stage
    report["pilot"] = bool(args.pilot)
    if figures_on and upto >= STAGES.index("location"):
        figures += write_figures(data, extras, args.output_dir)
    report["figures"] = figures
    report.update(sections)
    path = write_report(report, args.output_dir)
    flags = report["flags"]
    print(f"{path}: {len(flags)} flag(s), {len(report['input_notes'])} input note(s) from {len(checks)} checks; figures: {', '.join(figures) or 'none'}")
    for f in flags:
        print(f"  [{f['dimension']}] {f['symptom']}")
    for n in report["input_notes"]:
        print(f"  [input note] {n['symptom']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
