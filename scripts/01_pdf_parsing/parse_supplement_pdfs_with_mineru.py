#!/usr/bin/env python3
"""Parse supplementary PDFs with the project's official MinerU workflow.

Supplementary PDFs remain in references/<SOURCE>/supplement. MinerU output is
written under parsed/supplement/mineru/<PDF_STEM>, with a stable Markdown
derivative under parsed/supplement. This is the PDF-only companion to
scripts/02_supplement_processing/convert_nonpdf_supplements.py.
"""
from __future__ import annotations
import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def discover(case=None, source=None):
    paths = sorted((ROOT / "data").glob("*/references/*/supplement/*.pdf"))
    out=[]
    for p in paths:
        if case and p.parents[3].name != case: continue
        if source and p.parents[1].name != source: continue
        out.append(p)
    return out


def parse_one(pdf, force=False, timeout=3600):
    sys.path.insert(0, str(ROOT / "scripts/01_pdf_parsing"))
    from parse_papers_with_mineru import load_official_parser, parse_one as parse_paper
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env", override=True)
    except ImportError:
        pass
    for name in ("NO_PROXY", "no_proxy"):
        current=os.environ.get(name, "")
        os.environ[name]=",".join(x for x in (current,"mineru.net,.mineru.net,aliyuncs.com,.aliyuncs.com") if x)
    args=argparse.Namespace(force=force,max_retries=3,model_version="vlm",lang="auto",ocr=False,timeout=timeout)
    return parse_paper(args, pdf, load_official_parser())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--case"); ap.add_argument("--source"); ap.add_argument("--pdf",type=Path)
    ap.add_argument("--list",action="store_true"); ap.add_argument("--force",action="store_true")
    ap.add_argument("--timeout",type=int,default=3600)
    a=ap.parse_args()
    paths=[a.pdf.resolve()] if a.pdf else discover(a.case,a.source)
    paths=[p for p in paths if p.is_file() and p.suffix.lower()==".pdf"]
    if a.list:
        print("\n".join(map(str,paths))); return 0
    failures=0
    for p in paths:
        try: print(parse_one(p,a.force,a.timeout),flush=True)
        except Exception as e: print(f"FAIL  {p}: {e}",file=sys.stderr,flush=True); failures+=1
    return 1 if failures else 0

if __name__ == "__main__": raise SystemExit(main())
