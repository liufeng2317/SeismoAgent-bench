#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUT_ROOT = ROOT / "markdown"
HEADING_MAP = {
    "=": "#",
    "-": "##",
    "~": "###",
    "^": "####",
    '"': "#####",
}
HTML_BASENAME_MAP = {
    "index.html": "index.md",
    "programs.html": "programs.md",
    "control.html": "control.ControlFile.md",
    "Grid2GMT.html": "core.Grid2GMT.md",
    "Grid2Time.html": "core.Grid2Time.md",
    "Loc2ssst.html": "core.Loc2ssst.md",
    "LocSum.html": "core.LocSum.md",
    "NLLoc.html": "core.NLLoc.md",
    "Time2EQ.html": "core.Time2EQ.md",
    "Vel2Grid.html": "core.Vel2Grid.md",
    "Vel2Grid3D.html": "core.Vel2Grid3D.md",
}


def discover_sources() -> list[Path]:
    sources = [ROOT / "index.rst", ROOT / "programs.rst"]
    sources.extend(sorted((ROOT / "programs").glob("*.rst")))
    return [path for path in sources if path.exists()]


def build_output_map(sources: list[Path]) -> dict[Path, Path]:
    mapping: dict[Path, Path] = {}
    for src in sources:
        rel = src.relative_to(ROOT)
        mapping[src] = OUT_ROOT / rel.with_suffix(".md")
    return mapping


def parse_substitutions(lines: list[str]) -> dict[str, str]:
    substitutions: dict[str, str] = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"\.\. \|([^|]+)\| raw:: html", line)
        if not match:
            i += 1
            continue
        key = f"|{match.group(1)}|"
        i += 1
        block: list[str] = []
        while i < len(lines):
            current = lines[i]
            if current[:1].isspace() or current.strip() == "":
                block.append(current.strip())
                i += 1
                continue
            break
        html = " ".join(part for part in block if part)
        link = re.search(r'<a href="([^"]+)"[^>]*>(.*?)</a>', html)
        if link:
            substitutions[key] = f"[{link.group(2)}]({link.group(1)})"
        else:
            substitutions[key] = ""
    return substitutions


def apply_inline_markup(text: str, substitutions: dict[str, str]) -> str:
    for key, value in substitutions.items():
        text = text.replace(key, value)
    text = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", text)
    text = re.sub(r":ref:`([^`]+)`", r"\1", text)
    text = re.sub(r":doc:`([^`]+)`", r"\1", text)
    text = re.sub(r"`([^`<>]+?)\s*<([^>]+)>`__", r"[\1](\2)", text)
    text = re.sub(r"`([^`]+)`__", r"`\1`", text)
    text = text.replace("\\ ", " ")
    return text


def remap_html_links(content: str) -> str:
    def _replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        target = match.group(2)
        mapped = target
        for old_name, new_name in HTML_BASENAME_MAP.items():
            mapped = mapped.replace(old_name, new_name)
        return f"[{label}]({mapped})"

    content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _replace_link, content)
    return content


def postprocess_content(content: str) -> str:
    def _replace_rst_link(match: re.Match[str]) -> str:
        label = " ".join(match.group(1).split())
        target = match.group(2).strip()
        for old_name, new_name in HTML_BASENAME_MAP.items():
            target = target.replace(old_name, new_name)
        return f"[{label}]({target})"

    content = re.sub(r'<a href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", content)
    content = re.sub(r"`([\s\S]*?)\s*<([^>]+)>`__", _replace_rst_link, content)
    content = re.sub(r"`([^`\n]+)`__", r"`\1`", content)
    content = re.sub(r":sub:`([^`]+)`", r"<sub>\1</sub>", content)
    content = re.sub(r":sup:`([^`]+)`", r"<sup>\1</sup>", content)
    content = content.replace("[[", "[").replace("]]", "]")
    content = content.replace("the development branches are , or the\nlatest stable release can be found .", "the development branches are [here](https://github.com/alomax/NonLinLoc/tree/develop), or the latest stable release can be found [here](https://github.com/alomax/NonLinLoc/releases).")
    content = content.replace("For other A. Lomax NonLinLoc publications, see http://alomax.net/pub_list.html", "For other A. Lomax NonLinLoc publications, see [http://alomax.net/pub_list.html](http://alomax.net/pub_list.html).")
    content = remap_html_links(content)
    return content


def is_heading_underline(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and len(set(stripped)) == 1 and stripped[0] in HEADING_MAP


def make_output_path(target: str, source_dir: Path, output_dir: Path, output_map: dict[Path, Path]) -> str | None:
    source_target = (source_dir / f"{target}.rst").resolve()
    output_target = output_map.get(source_target)
    if not output_target:
        return None
    return output_target.relative_to(output_dir).as_posix()


def consume_indented_block(lines: list[str], start: int) -> int:
    i = start
    while i < len(lines):
        current = lines[i]
        if current[:1].isspace() or current.strip() == "":
            i += 1
            continue
        break
    return i


def convert_file(src: Path, output_map: dict[Path, Path]) -> None:
    lines = src.read_text(encoding="utf-8", errors="replace").splitlines()
    substitutions = parse_substitutions(lines)
    out_lines: list[str] = []
    source_dir = src.parent
    output_path = output_map[src]
    output_dir = output_path.parent

    i = 0
    while i < len(lines):
        line = lines[i]

        if re.match(r"\.\. \|([^|]+)\| raw:: html", line):
            i = consume_indented_block(lines, i + 1)
            continue

        if line.startswith(".. COMMENTED-OUT BLOCK:"):
            i = consume_indented_block(lines, i + 1)
            continue

        if line.startswith(".. raw:: html"):
            i = consume_indented_block(lines, i + 1)
            continue

        image_match = re.match(r"\.\. image::\s+(.*)", line)
        if image_match:
            image_path = image_match.group(1).strip()
            out_lines.append(f"![{Path(image_path).name}]({image_path})")
            i = consume_indented_block(lines, i + 1)
            continue

        if line.startswith(".. toctree::"):
            i += 1
            entries: list[str] = []
            while i < len(lines):
                current = lines[i]
                if current.startswith("   :") or current.strip() == "":
                    i += 1
                    continue
                if current.startswith("   "):
                    entry = current.strip()
                    target = make_output_path(entry, source_dir, output_dir, output_map)
                    if target:
                        entries.append(f"- [{entry}]({target})")
                    else:
                        entries.append(f"- {entry}")
                    i += 1
                    continue
                break
            out_lines.extend(entries)
            if entries:
                out_lines.append("")
            continue

        if i + 1 < len(lines) and is_heading_underline(lines[i + 1]):
            heading = apply_inline_markup(line.strip(), substitutions)
            marker = lines[i + 1].strip()[0]
            out_lines.append(f"{HEADING_MAP[marker]} {heading}")
            out_lines.append("")
            i += 2
            continue

        if line.startswith(".. "):
            i += 1
            continue

        text = apply_inline_markup(line, substitutions)
        if text.startswith("| "):
            text = text[2:]
        out_lines.append(text.rstrip())
        i += 1

    normalized: list[str] = []
    blank = False
    for line in out_lines:
        if line.strip():
            normalized.append(line)
            blank = False
        elif not blank:
            normalized.append("")
            blank = True

    content = "\n".join(normalized).strip() + "\n"
    content = postprocess_content(content)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def copy_assets() -> None:
    for asset_name in ("NonLinLocLogo.gif",):
        src = ROOT / asset_name
        if not src.exists():
            continue
        dst = OUT_ROOT / asset_name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def write_readme() -> None:
    readme = OUT_ROOT / "README.md"
    content = """# NonLinLoc Markdown Docs

This directory contains Markdown files generated from the available NonLinLoc reStructuredText sources under `docs/Nonlinloc/`.

- `index.md` is the main entry page.
- `programs.md` is the program overview page.
- `programs/` contains per-program Markdown pages.

Some pages referenced by the original Sphinx index, such as `intro`, `installation`, `updates`, and `tutorial`, are not present in this repository snapshot, so they could not be converted here.
"""
    readme.write_text(content, encoding="utf-8")


def main() -> None:
    sources = discover_sources()
    output_map = build_output_map(sources)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    copy_assets()
    for src in sources:
        convert_file(src, output_map)
    write_readme()


if __name__ == "__main__":
    main()
