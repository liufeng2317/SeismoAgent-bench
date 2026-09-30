#!/usr/bin/env python3
"""Add stable links to extraction JSON files in reference READMEs."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    changed = 0
    for extraction in sorted((ROOT / "data").glob("*/references/*/parsed/extraction/*__extraction.json")):
        reference = extraction.parents[2]
        readme = reference / "README.md"
        rel = extraction.relative_to(reference).as_posix()
        line = f"- Structured extraction: [`{rel}`]({rel}).\n"
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
        else:
            text = f"# {reference.name}\n\n"
        if rel in text:
            continue
        # Keep the link close to the paper-reading/parsed-material links.
        text = text.rstrip() + "\n" + line
        readme.write_text(text, encoding="utf-8")
        changed += 1
    print(f"updated {changed} reference READMEs")


if __name__ == "__main__":
    main()
