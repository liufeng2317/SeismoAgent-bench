#!/usr/bin/env python3
"""Normalize catalog quality labels while preserving the original rationale."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

QUALITY_MAP = {
    "COCHRAN2020_GJIGGAA153": ("Q2", "Enhanced detection/relative location; metric-specific Q1 structural auxiliary."),
    "ISKEN2017_BSSA0120160150": ("Q1", "Selective high-quality absolute/depth locations; not a complete event-existence catalog."),
    "MCMAHON2017_GL072944": ("Q2", "Enhanced S-phase detection and relocation; uncertainty-filtered subset is useful as a Q1 location anchor."),
    "MCMAHON2017_DISSERTATION": ("unknown", "Context-only source; no catalog quality can be assigned until the dissertation is parsed."),
    "CHAMBERLAIN2021_JB022304": ("Q2", "Long-duration matched-filter catalog with a high-quality relative-relocation subset and focal mechanisms."),
    "LANZA2019_GL082780": ("Q1", "High-precision absolute/relative relocation reference; completeness is lower than the dense detection products."),
    "TAN2024_JB028735": ("Q2", "Dense SUGAR detection/location catalog; S11 relative relocation is stronger for geometry than for absolute truth."),
    "MAPLE_RELATED_OPEN": ("unknown", "Out-of-case context paper; not a Yellowstone benchmark catalog."),
    "PANG2019_GL082376": ("Q1", "Article describes a high-quality absolute/GrowClust reference, but the local machine-readable release is missing."),
    "SHELLY2019_GL081607": ("Q1", "High-quality relative geometry and template-enhanced detection; the local phase release is an auxiliary observation table."),
    "LENGLINE2021_EPSL116653": ("Q2", "Focused dike-migration detection product; it is not a full hypocenter/magnitude catalog."),
    "MATOZA2014_GL059819": ("Q1", "High-precision historical LP relative-relocation product; it has no 2018-window events."),
    "MATOZA2021_EA001253": ("Q1", "Broad island-wide high-precision relative-relocation reference with heterogeneous historical coverage."),
    "QUAKEFLOW_GJI_GGAC355": ("unknown", "Method paper/context only; no dedicated Hawaii event release is identified."),
    "SHELLY2019_GL085636": ("Q1", "High-resolution summit event catalog; S2 polarity clusters and phase arrivals are derived/auxiliary products."),
    "USGS2019_SCIENCE_OVERVIEW": ("unknown", "Context overview; it is not a benchmark catalog."),
    "WEI2022_EA001979": ("Q2", "Broad automatic detection/location catalog using mixed onshore and offshore networks."),
    "AWR2025_CALTECHDATA": ("Q2", "Long-term PhaseNO/GaMMA/HypoSVI/GrowClust and moment-tensor release; network and version effects matter."),
    "LIU2020_GL086189": ("Q2", "Independent raw-waveform ML detection and relocation catalog; final hypoDD product is the strongest local subset."),
    "ROSS2019_SCIENCE": ("Q1", "High-quality relative fault-geometry/QTM reference; exact article subset parameters require Science DC1."),
    "SHELLY2020_0220190309": ("Q1", "High-resolution template-matched event catalog with differential-time relocation; phase CSV is auxiliary."),
    "BAKER2021_0220200316": ("Q3", "Pick-level/association product; article PDF and normalized event-level release are still missing."),
    "PANG2020_GL089798": ("Q1", "High-resolution Magna matched-filter/relative-location reference; local release lacks an explicit relocation flag."),
}

def normalize(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    source_id = data.get("article", {}).get("source_id") or path.name.split("__extraction", 1)[0]
    tier, detail = QUALITY_MAP[source_id]
    catalog = data.setdefault("catalog", {})
    catalog["quality_tier"] = tier
    catalog["quality_tier_detail"] = detail
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    paths = args.paths or sorted((root / "data").glob("*/references/*/parsed/extraction/*.json"))
    for raw in paths:
        path = raw if raw.is_absolute() else root / raw
        normalize(path.resolve())
        print(path.relative_to(root))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
