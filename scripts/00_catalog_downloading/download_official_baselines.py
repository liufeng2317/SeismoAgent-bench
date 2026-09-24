#!/usr/bin/env python3
"""Download frozen official operational catalog snapshots for all six cases."""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta


ROOT = pathlib.Path(__file__).resolve().parents[1]


def query_url(spec: dict, start=None, end=None) -> str:
    params = {k: spec[k] for k in (
        "format", "starttime", "endtime", "minlatitude", "maxlatitude",
        "minlongitude", "maxlongitude", "mindepth", "maxdepth", "orderby"
    ) if k in spec}
    if start is not None:
        params["starttime"] = start
    if end is not None:
        params["endtime"] = end
    params.setdefault("format", "csv")
    params.setdefault("orderby", "time-asc")
    return spec["service"] + "?" + urllib.parse.urlencode(params)


def write_readme(spec: dict, output: pathlib.Path, url: str, downloaded: str, rows: int | None) -> None:
    readme = output.parent / "README.md"
    readme.write_text(
        "# Official operational catalog snapshot\n\n"
        f"- `source_ref`: `{output.parent.name}`\n"
        f"- Provider: {spec['provider']}\n"
        f"- Network/source: {spec['network']}\n"
        "- Role: Q3 official operational baseline; not a high-resolution truth catalog.\n"
        f"- Query strategy: `{url}`\n"
        f"- Time range (half-open): `{spec['starttime']}` to `{spec['endtime']}`\n"
        f"- Latitude: {spec['minlatitude']} to {spec['maxlatitude']}\n"
        f"- Longitude: {spec['minlongitude']} to {spec['maxlongitude']}\n"
        f"- Depth: {spec['mindepth']} to {spec['maxdepth']} km\n"
        f"- Downloaded UTC: {downloaded}\n"
        f"- Returned data rows: {rows if rows is not None else 'not counted'}\n"
        "- Spatial and temporal filters are encoded in the query URL.\n"
        "- Service fields and rows are preserved; time chunks are merged and de-duplicated by stable event ID.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="download one case ID; default is all cases")
    parser.add_argument("--config", default=str(ROOT / "scripts/00_catalog_downloading/official_baseline_windows.json"))
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--direct", action="store_true", help="ignore HTTP(S)_PROXY environment variables")
    parser.add_argument("--scope", choices=("benchmark", "full"), default="full",
                        help="download the frozen benchmark window or the full case acquisition window")
    args = parser.parse_args()
    config = json.loads(pathlib.Path(args.config).read_text(encoding="utf-8"))
    selected = {args.case: config[args.case]} if args.case else config
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if args.direct else urllib.request.build_opener()
    for case_id, spec in selected.items():
        scope = spec[args.scope]
        output = ROOT / scope["output"]
        output.parent.mkdir(parents=True, exist_ok=True)
        start = datetime.fromisoformat(scope["starttime"])
        end = datetime.fromisoformat(scope["endtime"])
        # Chunking avoids silent service caps (notably ComCat's 20,000-row cap).
        chunks = []
        cursor = start
        chunk_days = int(scope.get("chunk_days", 30))
        while cursor < end:
            nxt = min(cursor + timedelta(days=chunk_days), end)
            url = query_url({**spec, **scope}, cursor.isoformat(), nxt.isoformat())
            print(f"[{case_id}/{args.scope}] {url}")
            request = urllib.request.Request(url, headers={"User-Agent": "SeismoAgentBench/official-baseline-downloader"})
            with opener.open(request, timeout=args.timeout) as response:
                chunks.append(response.read())
            cursor = nxt
        if scope.get("format", "csv") == "csv":
            fields, records, seen = None, [], set()
            for payload0 in chunks:
                reader = csv.DictReader(io.StringIO(payload0.decode("utf-8")))
                if fields is None: fields = reader.fieldnames
                for row in reader:
                    key = row.get("id") or row.get("time")
                    if key not in seen: seen.add(key); records.append(row)
            buffer = io.StringIO(newline="")
            if fields:
                writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
                writer.writeheader(); writer.writerows(records)
            payload = buffer.getvalue().encode("utf-8")
            rows = len(records)
        else:
            lines, seen = [], set()
            for payload0 in chunks:
                for line in payload0.splitlines():
                    if not line.strip() or line.startswith(b"#") or line.lower().startswith(b"publicid"):
                        if not lines and line.strip(): lines.append(line)
                        continue
                    key = line.split(b"|", 1)[0]
                    if key not in seen: seen.add(key); lines.append(line)
            payload = b"\n".join(lines) + (b"\n" if lines else b"")
            rows = len(seen)
        output.write_bytes(payload)
        downloaded = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        write_readme({**spec, **scope}, output, f"{chunk_days}-day chunks; {scope['starttime']} to {scope['endtime']}", downloaded, rows)
        print(f"  wrote {output} ({len(payload)} bytes, {rows} data rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
