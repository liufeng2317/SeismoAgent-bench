#!/usr/bin/env python3
"""Parse SeismoAgentBench paper PDFs with the existing Knowledge_Graph MinerU service.

The source PDF stays in ``references/<SOURCE_ID>/paper``.  MinerU artifacts are
written to ``parsed/paper/mineru/<pdf-stem>/`` and the parsed Markdown is additionally
copied to ``parsed/paper/<pdf-stem>__mineru.md`` for convenient reading.

This wrapper intentionally reuses the login, submit, polling, image download,
and result-writing functions from Knowledge_Graph rather than maintaining a
second MinerU client implementation.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KG_ROOT = Path("/liufeng1afs/project/03_LLM/Knowledge_Graph")


def load_official_parser():
    """Load the official Knowledge_Graph wrapper; never use MinerU_local."""
    if str(KG_ROOT) not in sys.path:
        sys.path.insert(0, str(KG_ROOT))
    from KGForge.paper_parse.local_pdf_parser import parse_local_pdfs

    return parse_local_pdfs


def discover_pdfs(root: Path, case: str | None, source: str | None) -> list[Path]:
    papers = root / "data"
    paths = sorted(papers.glob("*/references/*/paper/*.pdf"))
    selected = []
    for path in paths:
        case_id = path.parents[3].name
        source_id = path.parents[1].name
        if case and case_id != case:
            continue
        if source and source_id != source:
            continue
        selected.append(path)
    return selected


def parsed_root(pdf: Path) -> Path:
    """Return the per-reference parsed tree for a paper or supplement PDF."""
    kind = pdf.parent.name
    if kind not in {"paper", "supplement"}:
        raise ValueError(f"Expected a paper or supplement PDF, got: {pdf}")
    return pdf.parent.parent / "parsed" / kind


def output_dir(pdf: Path) -> Path:
    return parsed_root(pdf) / "mineru" / pdf.stem


def complete(out: Path) -> bool:
    if not out.is_dir():
        return False
    return any(out.rglob("*.md")) and any(out.rglob("*_model.json"))


def parsed_markdown(out: Path) -> Path | None:
    """Select the canonical MinerU Markdown result from an output bundle."""
    if not out.is_dir():
        return None
    candidates = sorted(out.rglob("full.md")) or sorted(out.rglob("*.md"))
    return candidates[0] if candidates else None


def sync_stable_markdown(pdf: Path, out: Path | None = None) -> bool:
    """Copy an existing local MinerU result beside its source PDF."""
    out = out or output_dir(pdf)
    parsed = parsed_markdown(out)
    if parsed is None:
        return False
    text = parsed.read_text(encoding="utf-8")
    parsed_parent = parsed.parent.relative_to(out)
    image_prefix = (Path("mineru") / pdf.stem / parsed_parent / "images").as_posix().strip("./") + "/"
    text = re.sub(r"\]\(images/", f"]({image_prefix}", text)
    text = re.sub(r"(src=[\"'])images/", rf"\1{image_prefix}", text)
    stable_dir = parsed_root(pdf)
    stable_dir.mkdir(parents=True, exist_ok=True)
    (stable_dir / f"{pdf.stem}__mineru.md").write_text(text, encoding="utf-8")
    return True


def parse_one(args, pdf: Path, parse_local_pdfs) -> str:
    out = output_dir(pdf)
    if complete(out) and not args.force:
        synced = sync_stable_markdown(pdf, out)
        suffix = "; stable Markdown synced" if synced else "; stable Markdown unavailable"
        return f"SKIP  {pdf} (already parsed{suffix}; use --force to redo)"

    # Knowledge_Graph's PaperProcessor reads MINERU_API_BASE/MINERU_API_KEY
    # from the environment and owns the official upload/poll/download flow.
    result = parse_local_pdfs(
        process_all=False,
        specific_pdf_files=[pdf.name],
        data_dir=str(pdf.parent),
        output_dir=str(out.parent),
        max_retries=args.max_retries,
        continue_on_error=False,
        model_version=args.model_version,
        language=args.lang,
        is_ocr=args.ocr,
        poll_timeout=args.timeout,
        llm_aid=False,
        verbose=False,
        save_summary=True,
    )
    if not isinstance(result, dict):
        raise RuntimeError(
            "Knowledge_Graph official MinerU parser returned an unexpected result "
            f"of type {type(result).__name__}: {result!r}"
        )
    if result.get("successful", 0) != 1:
        raise RuntimeError(f"Knowledge_Graph official MinerU parser failed: {result}")

    if not sync_stable_markdown(pdf, out):
        raise RuntimeError(f"MinerU task succeeded but no Markdown result was found under {out}")
    return f"OK    {pdf} -> {out}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", help="Canonical case ID, e.g. 2011_prague_oklahoma")
    parser.add_argument("--source", help="SOURCE_ID, e.g. COCHRAN2020_GJIGGAA153")
    parser.add_argument("--pdf", type=Path, help="Parse one explicit PDF path")
    parser.add_argument("--list", action="store_true", help="List discovered PDFs without submitting tasks")
    parser.add_argument("--dry-run", action="store_true", help="Alias for --list")
    parser.add_argument("--force", action="store_true", help="Reparse completed outputs")
    parser.add_argument("--sync-stable", action="store_true", help="Copy existing local MinerU Markdown beside each PDF; no API call")
    parser.add_argument("--model-version", default="vlm", choices=("vlm", "pipeline"))
    parser.add_argument("--lang", default="auto")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--ocr", action="store_true", help="Enable MinerU OCR")
    args = parser.parse_args()

    if args.pdf:
        pdfs = [args.pdf.resolve()]
        if not pdfs[0].is_file() or pdfs[0].suffix.lower() != ".pdf":
            parser.error(f"PDF does not exist or is not a PDF: {pdfs[0]}")
    else:
        pdfs = discover_pdfs(PROJECT_ROOT, args.case, args.source)
    if not pdfs:
        print("No paper PDFs found.")
        return 0
    for pdf in pdfs:
        print(f"{pdf}")
    if args.list or args.dry_run:
        return 0
    if args.sync_stable:
        failures = 0
        for pdf in pdfs:
            if complete(output_dir(pdf)) and sync_stable_markdown(pdf):
                print(f"SYNC  {pdf}", flush=True)
            else:
                failures += 1
                print(f"MISS  {pdf}: no complete local MinerU bundle", file=sys.stderr, flush=True)
        return 1 if failures else 0

    # Load this project's credentials first and explicitly override any stale
    # MINERU_* values inherited from the shell or Knowledge_Graph environment.
    load_dotenv(PROJECT_ROOT / ".env", override=True)
    # MinerU upload and polling use two hosts. Keep them out of the broken
    # workspace proxy while leaving unrelated network traffic untouched.
    direct_hosts = "mineru.net,.mineru.net,aliyuncs.com,.aliyuncs.com"
    for proxy_var in ("NO_PROXY", "no_proxy"):
        current = os.environ.get(proxy_var, "")
        os.environ[proxy_var] = ",".join(x for x in (current, direct_hosts) if x)
    parse_local_pdfs = load_official_parser()
    failures = 0
    for pdf in pdfs:
        try:
            print(parse_one(args, pdf, parse_local_pdfs), flush=True)
        except Exception as exc:
            failures += 1
            print(f"FAIL  {pdf}: {exc}", file=sys.stderr, flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
