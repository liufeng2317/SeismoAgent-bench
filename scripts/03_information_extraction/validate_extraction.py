#!/usr/bin/env python3
"""Validate extraction evidence paths, product counts, status, and product boundaries."""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def xlsx_rows(path: Path) -> int:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    return max(0, len(root.findall(".//m:row", ns)) - 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("extraction", type=Path)
    args = ap.parse_args()
    p = args.extraction.resolve()
    root = p.parents[6] if len(p.parents) > 6 else p.parent
    d = json.loads(p.read_text(encoding="utf-8"))
    errors, warnings = [], []

    # Evidence paths are repository-relative.
    sources = []
    def walk(x):
        if isinstance(x, dict):
            if isinstance(x.get("source"), str): sources.append(x["source"])
            for v in x.values(): walk(v)
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(d)
    missing = sorted({s for s in sources if not (root / s).exists()})
    if missing: errors.append(f"missing evidence paths: {missing}")

    q = d.get("extraction_quality", {})
    if q.get("status") == "verified" and q.get("needs_human_review"):
        errors.append("status=verified conflicts with needs_human_review=true")
    if q.get("status") == "partial" and not q.get("needs_human_review"):
        warnings.append("status=partial but needs_human_review is false")

    cat = d.get("catalog", {})
    if "product_schemas" not in cat:
        errors.append("catalog lacks product-specific product_schemas")
    if cat.get("product_type") == "event_catalog_plus_relocated_subset":
        errors.append("catalog product_type still implies an undifferentiated merged product")
    counts = cat.get("local_audit", {}).get("product_counts", {})
    expected = {
        "S10": ("catalogs/TAN2024_JB028735/TAN2024_JB028735__catalog_sugar_S10.xlsx", 67660),
        "S11": ("catalogs/TAN2024_JB028735/TAN2024_JB028735__catalog_sugar_relocated_S11.xlsx", 46440),
    }
    for product, (rel, expected_n) in expected.items():
        fp = p.parents[4] / rel
        if not fp.exists():
            errors.append(f"{product} local file missing: {fp}")
            continue
        actual = xlsx_rows(fp)
        if counts.get(product) != actual or actual != expected_n:
            errors.append(f"{product} count mismatch: JSON={counts.get(product)}, file={actual}, expected={expected_n}")

    labels = [str(x.get("label", "")).lower() for x in cat.get("populations", []) if isinstance(x, dict)]
    if any("focal" in x and "catalog" in x for x in labels):
        errors.append("focal-mechanism product is mislabeled as a full catalog")
    if counts.get("final_cluster_filtered_reported") == counts.get("S11"):
        errors.append("final cluster-filtered count is incorrectly merged with S11 count")

    print(f"PASS evidence_paths={len(sources)-len(missing)} missing={len(missing)}")
    print(f"PASS status={q.get('status')} needs_human_review={q.get('needs_human_review')}")
    print(f"PASS product_counts={counts}")
    for w in warnings: print(f"WARN {w}")
    for e in errors: print(f"FAIL {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
