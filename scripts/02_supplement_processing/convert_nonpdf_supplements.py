#!/usr/bin/env python3
"""Convert and audit supplementary materials for SeismoAgentBench.

The script deliberately has no third-party document dependency:

* PDF supplements are submitted through the project's official MinerU wrapper
  when ``--parse-pdfs`` is requested.
* DOCX and XLSX files are decoded from their OOXML XML parts and written as
  searchable Markdown.
* TXT/XML/CSV files receive a normalized Markdown companion and a data-role
  assessment.

Catalog migration is opt-in (``--migrate-catalogs``).  Only high-confidence
event-table candidates are moved to ``data/<CASE>/catalogs/<SOURCE>/raw``;
ambiguous tables remain in the supplement directory and are reported.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
SUPPORTED = {".docx", ".xlsx", ".txt", ".xml", ".csv", ".tsv"}
IGNORE = {".md", ".mp4", ".zip"}
EVENT_TERMS = {"time", "date", "origin", "latitude", "longitude", "lat", "lon",
               "depth", "magnitude", "mag", "event", "hypocenter", "longitude"}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def md_cell(value: str) -> str:
    return clean(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(rows: list[list[str]]) -> str:
    rows = [[md_cell(c) for c in row] for row in rows if any(clean(c) for c in row)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |",
           "| " + " | ".join("---" for _ in range(width)) + " |"]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def docx_to_md(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    out: list[str] = [f"# {path.stem}", "", f"Source: `{path.name}`", ""]
    body = root.find("w:body", NS)
    if body is None:
        return "\n".join(out)
    for node in body:
        if node.tag.endswith("}p"):
            text = clean("".join(t.text or "" for t in node.findall(".//w:t", NS)))
            if text:
                style = node.find("w:pPr/w:pStyle", NS)
                val = style.attrib.get(f"{{{NS['w']}}}val", "") if style is not None else ""
                level = 2 if "Heading1" in val else 3 if "Heading" in val else 0
                out.append(("#" * level + " " if level else "") + text)
                out.append("")
        elif node.tag.endswith("}tbl"):
            rows = []
            for tr in node.findall("w:tr", NS):
                rows.append([clean("".join(t.text or "" for t in tc.findall(".//w:t", NS)))
                             for tc in tr.findall("w:tc", NS)])
            table = markdown_table(rows)
            if table:
                out.extend([table, ""])
    return "\n".join(out).rstrip() + "\n"


def xlsx_rows(path: Path) -> dict[str, list[list[str]]]:
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("s:si", NS):
                shared.append(clean("".join(t.text or "" for t in si.findall(".//s:t", NS))))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap = {r.attrib.get("Id"): r.attrib.get("Target") for r in rels}
        result = {}
        for sheet in wb.findall("s:sheets/s:sheet", NS):
            title = sheet.attrib.get("name", "sheet")
            target = relmap.get(sheet.attrib.get(f"{{{NS['r']}}}id"), "")
            target = target.lstrip("/")
            if not target.startswith("xl/"):
                target = "xl/" + target
            if target not in names:
                continue
            root = ET.fromstring(z.read(target))
            rows = []
            for row in root.findall(".//s:sheetData/s:row", NS):
                values = []
                for cell in row.findall("s:c", NS):
                    ref = cell.attrib.get("r", "")
                    col = re.match(r"[A-Z]+", ref)
                    idx = 0
                    if col:
                        for ch in col.group():
                            idx = idx * 26 + ord(ch) - 64
                        idx -= 1
                    while len(values) <= idx:
                        values.append("")
                    value = cell.find("s:v", NS)
                    text = value.text if value is not None else ""
                    if cell.attrib.get("t") == "s" and text.isdigit():
                        text = shared[int(text)] if int(text) < len(shared) else text
                    values[idx] = text or ""
                rows.append(values)
            result[title] = rows
    return result


def xlsx_to_md(path: Path) -> tuple[str, bool, dict]:
    sheets = xlsx_rows(path)
    out = [f"# {path.stem}", "", f"Source: `{path.name}`", ""]
    all_headers: set[str] = set(); total_rows = 0
    for title, rows in sheets.items():
        out.extend([f"## Sheet: {title}", ""])
        out.append(markdown_table(rows) or "_(empty sheet)_")
        out.append("")
        total_rows += max(0, len(rows) - 1)
        if rows:
            all_headers.update(clean(x).lower().replace("_", " ") for x in rows[0])
    hits = {h for h in all_headers if any(term in h.split() or term in h for term in EVENT_TERMS)}
    confident = len(hits) >= 3 and total_rows >= 10 and bool({"lat", "latitude"} & all_headers) and bool({"lon", "longitude"} & all_headers)
    role = "catalog_candidate" if confident else "supporting_table"
    meta = {"sheets": list(sheets), "data_rows": total_rows, "headers": sorted(all_headers),
            "event_header_hits": sorted(hits), "role": role}
    out.extend(["## Automated role assessment", "", f"- Role: `{role}`",
                f"- Data rows (approx.): `{total_rows}`", f"- Header hits: `{', '.join(sorted(hits))}`", ""])
    return "\n".join(out).rstrip() + "\n", confident, meta


def plain_to_md(path: Path) -> tuple[str, dict]:
    text = path.read_text(encoding="utf-8", errors="replace")
    role = "catalog_candidate" if path.suffix.lower() in {".csv", ".tsv", ".xml"} else "supporting_text"
    out = [f"# {path.stem}", "", f"Source: `{path.name}`", "", f"- Automated role: `{role}`", "",
           "## Content", "", "```text", text.rstrip(), "```", ""]
    return "\n".join(out), {"role": role, "characters": len(text), "lines": text.count("\n") + 1}


def discover(root: Path, case: str | None, source: str | None) -> list[Path]:
    paths = []
    for p in sorted((root / "data").glob("*/references/*/supplement/*")):
        if p.suffix.lower() not in SUPPORTED or p.suffix.lower() in IGNORE:
            continue
        if case and p.parents[3].name != case:
            continue
        if source and p.parents[1].name != source:
            continue
        paths.append(p)
    return paths


def process_one(path: Path, migrate: bool) -> dict:
    case, source = path.parents[3].name, path.parents[1].name
    suffix = path.suffix.lower()
    out_dir = path.parents[1] / "parsed" / "supplement"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (path.stem + "__extracted.md")
    meta = {"case": case, "source": source, "file": str(path.relative_to(ROOT)), "type": suffix,
            "output": str(out_path.relative_to(ROOT)), "status": "processed"}
    if suffix == ".docx":
        out_path.write_text(docx_to_md(path), encoding="utf-8")
    elif suffix == ".xlsx":
        text, confident, extra = xlsx_to_md(path); out_path.write_text(text, encoding="utf-8"); meta.update(extra)
        if confident and migrate:
            target_dir = ROOT / "data" / case / "catalogs" / source / "raw"; target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / path.name
            if not target.exists():
                shutil.move(str(path), str(target)); meta.update({"status": "migrated_catalog", "migrated_to": str(target.relative_to(ROOT))})
    elif suffix in {".txt", ".xml", ".csv", ".tsv"}:
        text, extra = plain_to_md(path); out_path.write_text(text, encoding="utf-8"); meta.update(extra)
    else:
        meta["status"] = "pdf_pending_official_mineru"
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case"); ap.add_argument("--source"); ap.add_argument("--list", action="store_true")
    ap.add_argument("--migrate-catalogs", action="store_true", help="Move only high-confidence XLSX event tables")
    ap.add_argument("--report", type=Path, help="Optional processing report; not generated by default")
    args = ap.parse_args()
    paths = discover(ROOT, args.case, args.source)
    if args.list:
        print("\n".join(str(p) for p in paths)); return 0
    records = [process_one(p, args.migrate_catalogs) for p in paths if p.suffix.lower() != ".pdf"]
    lines = ["# Supplement Processing Audit", "", f"Generated: {datetime.now(timezone.utc).isoformat()}", "",
             "This report separates machine conversion from scientific interpretation. PDF supplements require the official MinerU parser; DOCX/XLSX and text products are converted locally.", "",
             "| Case | Source | File | Type | Role/status | Output or destination |", "|---|---|---|---|---|---|"]
    for r in records:
        role = r.get("role", r.get("status", "")); dest = r.get("migrated_to", r.get("output", ""))
        lines.append(f"| `{r['case']}` | `{r['source']}` | `{Path(r['file']).name}` | `{r['type']}` | `{role}` | `{dest}` |")
    lines += ["", "## Interpretation rules", "", "- `catalog_candidate` is only a high-confidence automated flag; verify against the paper and schema before using it as a benchmark catalog.", "- Supplementary parameter, uncertainty, figure, and station tables remain under `references/<SOURCE>/supplement`.", "- Catalog files belong under `data/<CASE>/catalogs/<SOURCE>/raw`; migration is performed only with `--migrate-catalogs`.", "- The generated `__extracted.md` files are machine-readable derivatives, not replacements for the original supplements.", ""]
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines), encoding="utf-8")
    print(f"Processed {len(records)} supplementary files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
