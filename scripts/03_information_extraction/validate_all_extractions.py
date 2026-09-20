#!/usr/bin/env python3
"""Batch validator for parsed/extraction JSON files.

Checks repository-local evidence, product-specific schemas, status semantics,
and counts for CSV/XLSX/QuakeML products when a source file declares a
``product_id``.  It intentionally reports unresolved article-versus-release
differences instead of trying to reconcile them silently.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def row_count(path: Path) -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
            return max(0, sum(1 for _ in csv.reader(f)) - 1)
    if suffix == ".xlsx":
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        return max(0, len(root.findall(".//m:row", ns)) - 1)
    if suffix in {".xml", ".quakeml"}:
        count = 0
        for _, elem in ET.iterparse(path, events=("end",)):
            if local_name(elem.tag) == "event":
                count += 1
            elem.clear()
        return count
    return None


def all_sources(obj):
    if isinstance(obj, dict):
        if isinstance(obj.get("source"), str):
            yield obj["source"]
        for value in obj.values():
            yield from all_sources(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from all_sources(value)


def validate(path: Path, root: Path) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    d = json.loads(path.read_text(encoding="utf-8"))
    rel = path.relative_to(root)
    sources = sorted(set(all_sources(d)))
    local_sources = [s for s in sources if not s.startswith(("http://", "https://"))]
    missing = [s for s in local_sources if not (root / s).exists()]
    if missing:
        errors.append(f"missing evidence: {missing}")

    quality = d.get("extraction_quality", {})
    if quality.get("status") == "verified" and quality.get("needs_human_review"):
        errors.append("verified conflicts with needs_human_review=true")
    if quality.get("status") in {"partial", "draft"} and not quality.get("needs_human_review"):
        warnings.append("partial/draft should normally keep needs_human_review=true")

    catalog = d.get("catalog", {})
    tier = catalog.get("quality_tier")
    if tier not in {None, "Q1", "Q2", "Q3", "Q4", "unknown"}:
        errors.append(f"quality_tier must be Q1/Q2/Q3/Q4/unknown, got {tier!r}")
    schemas = catalog.get("product_schemas", {})
    products = catalog.get("product_semantics", {})
    additional = d.get("additional_information", {})
    findings = additional.get("scientific_findings", [])
    if isinstance(findings, list):
        for index, finding in enumerate(findings):
            if isinstance(finding, str):
                errors.append(f"additional_information.scientific_findings[{index}] must carry evidence")
            elif isinstance(finding, dict) and not finding.get("evidence"):
                errors.append(f"additional_information.scientific_findings[{index}] has no evidence")
    context = additional.get("benchmark_context")
    if isinstance(context, str):
        errors.append("additional_information.benchmark_context must be an evidence-bearing object")
    elif isinstance(context, dict) and not context.get("evidence"):
        errors.append("additional_information.benchmark_context has no evidence")
    if catalog.get("role") != "not_a_catalog" and (not isinstance(schemas, dict) or len(schemas) < 1):
        errors.append("catalog.product_schemas is missing or empty")
    if len(products) > 1 and "schema" in catalog:
        errors.append("multiple products still use a merged catalog.schema")

    source_files = catalog.get("release", {}).get("source_files", [])
    counts = catalog.get("local_audit", {}).get("product_counts", {})
    for item in source_files if isinstance(source_files, list) else []:
        if not isinstance(item, dict):
            continue
        product_id = item.get("product_id")
        source_path = item.get("path")
        if not product_id or not isinstance(source_path, str) or source_path.startswith(("http://", "https://")):
            continue
        fp = root / source_path
        if not fp.exists():
            errors.append(f"missing release source for {product_id}: {source_path}")
            continue
        observed = row_count(fp)
        expected = counts.get(product_id)
        if observed is not None and isinstance(expected, int) and observed != expected:
            errors.append(f"{product_id} count mismatch: JSON={expected}, file={observed}")

    for population in catalog.get("populations", []):
        if not isinstance(population, dict):
            continue
        label = str(population.get("label", "")).lower()
        if "focal" in label and "catalog" in label:
            errors.append("focal-mechanism population mislabeled as a full catalog")
    for product_id, schema in schemas.items() if isinstance(schemas, dict) else []:
        if isinstance(schema, dict) and "focal" in product_id.lower() and "derived" not in str(schema.get("role", "")).lower():
            warnings.append(f"check that {product_id} is a derived focal-mechanism product")

    return errors, warnings, {"evidence": len(local_sources), "missing": len(missing), "status": quality.get("status")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    paths = args.paths or sorted((root / "data").glob("*/references/*/parsed/extraction/*.json"))
    total_errors = 0
    for raw in paths:
        path = raw if raw.is_absolute() else root / raw
        try:
            errors, warnings, stats = validate(path.resolve(), root)
        except Exception as exc:  # keep batch audit running for other cases
            errors, warnings, stats = [f"validator exception: {exc}"], [], {}
        tag = path.relative_to(root)
        print(f"{tag}: status={stats.get('status')} evidence={stats.get('evidence', 0)} missing={stats.get('missing', 0)}")
        for warning in warnings:
            print(f"  WARN {warning}")
        for error in errors:
            total_errors += 1
            print(f"  FAIL {error}")
    print(f"SUMMARY files={len(paths)} errors={total_errors}")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
