#!/usr/bin/env python3
"""Apply evidence/schema corrections to the first batch of extraction records.

This is deliberately conservative: it only normalizes known structural
patterns and explicitly documented product-count/metadata corrections. It
does not infer facts from catalog rows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def evidence(source: str, locator: str, note: str) -> dict:
    return {"source": source, "locator": locator, "note": note}


def replace_legacy_paper_evidence(data: dict) -> None:
    """Prefer stable parsed paper/supplement sidecars when available."""
    stable_supplement = {
        "data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/parsed/supplement/mineru/Pang2019_MapleCreek_SI/full.md":
            "data/2017_maple_creek_yellowstone/references/PANG2019_GL082376/parsed/supplement/PANG2019_GL082376__supplement__mineru.md",
        "data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/parsed/supplement/mineru/Shelly2019_MapleCreek_SI/full.md":
            "data/2017_maple_creek_yellowstone/references/SHELLY2019_GL081607/parsed/supplement/SHELLY2019_GL081607__supplement__mineru.md",
        "data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/parsed/supplement/mineru/Shelly2019_Kilauea_Figure_SI/full.md":
            "data/2018_kilauea_hawaii/references/SHELLY2019_GL085636/parsed/supplement/SHELLY2019_GL085636__supplement__mineru.md",
        "data/2018_kilauea_hawaii/references/WEI2022_EA001979/parsed/supplement/mineru/Wei2022_Kilauea_SI/full.md":
            "data/2018_kilauea_hawaii/references/WEI2022_EA001979/parsed/supplement/WEI2022_EA001979__supplement__mineru.md",
    }
    def walk(value):
        if isinstance(value, dict):
            if isinstance(value.get("source"), str):
                old = value["source"]
                candidate = old.replace("__paper_reading.md", "__paper__mineru.md")
                candidate = stable_supplement.get(candidate, candidate)
                if candidate != old and (ROOT / candidate).exists():
                    value["source"] = candidate
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)


def normalize_secondary_information(data: dict) -> None:
    additional = data.setdefault("additional_information", {})
    block_evidence = additional.get("evidence", [])
    sequence = data.get("article", {}).get("sequence")
    findings = additional.get("scientific_findings")
    if isinstance(findings, list):
        normalized = []
        for item in findings:
            if isinstance(item, str):
                normalized.append(
                    {
                        "statement": item,
                        "depends_on": None,
                        "scope": sequence,
                        "evidence": list(block_evidence),
                    }
                )
            else:
                normalized.append(item)
        additional["scientific_findings"] = normalized

    context = additional.get("benchmark_context")
    if isinstance(context, str):
        tier = data.get("catalog", {}).get("quality_tier")
        detail = data.get("catalog", {}).get("quality_tier_detail")
        additional["benchmark_context"] = {
            "quality_interpretation": detail or tier,
            "recommended_role": context,
            "comparison_or_baseline_sources": None,
            "valid_comparisons": None,
            "caveats": context,
            "evidence": list(block_evidence),
        }


def correct_matoza2014(data: dict) -> None:
    if data.get("article", {}).get("source_id") != "MATOZA2014_GL059819":
        return
    data["article"]["authors"] = ["Robin S. Matoza", "Peter M. Shearer", "Paul G. Okubo"]
    catalog = data["catalog"]
    catalog["product_semantics"] = {
        "LP_selected": "12,290 LP events classified by FI ≤ −1",
        "cross_correlation_relocated_article": "5,327 LP events relocated using waveform cross-correlation and cluster analysis",
        "SSST_aligned_final": "5,199 of the relocated events after the SSST cluster-centroid alignment criterion",
    }
    catalog["populations"] = [
        catalog["populations"][0],
        {
            "population_id": "P2",
            "label": "Cross-correlation/cluster relocated LP events",
            "unit": "events",
            "count_article": 5327,
            "count_local": None,
            "selection_rule": "Average P-wave correlation >0.45, at least eight differential-time measurements with correlation >0.75 and source–station distance <80 km.",
            "time_range": "1986-01-02 to 2009-03-31 UTC",
            "spatial_depth_scope": "Relocated LP products; native local coordinates",
            "magnitude_scope": "Inherited CUSP magnitude",
            "evidence": [
                evidence(
                    "data/2018_kilauea_hawaii/references/MATOZA2014_GL059819/parsed/paper/MATOZA2014_GL059819__paper__mineru.md",
                    "Abstract paragraph; §3, cross-correlation and relocation paragraph",
                    "Article reports 5,327 cross-correlation/cluster relocations.",
                )
            ],
        },
        {
            "population_id": "P3",
            "label": "SSST-aligned final relocated LP events",
            "unit": "events",
            "count_article": 5199,
            "count_local": 5199,
            "selection_rule": "Relocated clusters with at least 10 events and 20% of events having independent SSST locations; cluster centroids shifted to SSST centroids.",
            "time_range": "1986-01-02 to 2009-03-31 UTC",
            "spatial_depth_scope": "Final local rows with relocation flag=1",
            "magnitude_scope": "Inherited CUSP magnitude",
            "evidence": [
                evidence(
                    "data/2018_kilauea_hawaii/references/MATOZA2014_GL059819/parsed/paper/MATOZA2014_GL059819__paper__mineru.md",
                    "§3, SSST alignment paragraph; Figure 4 caption",
                    "Article/local archive distinguish the 5,199 final SSST-aligned rows.",
                )
            ],
        },
    ]
    catalog["local_audit"]["product_counts"] = {
        "lp_events": 12290,
        "SSST_aligned_final": 5199,
    }
    catalog["local_audit"]["article_local_discrepancy"] = (
        "Article reports 5,327 cross-correlation/cluster relocations and 5,199 final SSST-aligned events; "
        "the local archive exposes the 5,199 relocation-flag rows but not a separate 5,327 membership flag."
    )
    for stage in data.get("construction_workflow", {}).get("stages", []):
        if stage.get("stage_id") == "ST2":
            stage["outputs"] = ["5,327 cross-correlation/cluster relocations", "5,199 SSST-aligned final events"]
            stage["intermediate_result"] = "5,327 article relocations; 5,199 final SSST-aligned rows"
            stage["evidence"] = [
                evidence(
                    "data/2018_kilauea_hawaii/references/MATOZA2014_GL059819/parsed/paper/MATOZA2014_GL059819__paper__mineru.md",
                    "§3, paragraphs on 5,327 relocation and 5,199 SSST alignment",
                    "Separate intermediate and final products.",
                )
            ]
    data["catalog"]["release"]["evidence"].append(
        evidence(
            "data/2018_kilauea_hawaii/references/MATOZA2014_GL059819/parsed/paper/MATOZA2014_GL059819__paper__mineru.md",
            "Data availability; §3 product accounting",
            "Supporting-information release contains the relocated catalog.",
        )
    )


def correct_matoza2021(data: dict) -> None:
    if data.get("article", {}).get("source_id") != "MATOZA2021_EA001253":
        return
    data["article"]["authors"] = ["Robin S. Matoza", "Paul G. Okubo", "Peter M. Shearer"]
    # The parsed citation block and DOI identify the 2020 online/article year;
    # the project source ID remains MATOZA2021 for historical folder stability.
    data["article"]["year"] = 2020
    data["article"].setdefault("evidence", []).append(
        evidence(
            "data/2018_kilauea_hawaii/references/MATOZA2021_EA001253/parsed/paper/MATOZA2021_EA001253__paper__mineru.md",
            "citation block, lines 27–39",
            "Citation gives 2020 and full author names; source ID is retained for repository compatibility.",
        )
    )


def correct_usgs_overview(data: dict) -> None:
    if data.get("article", {}).get("source_id") != "USGS2019_SCIENCE_OVERVIEW":
        return
    data["article"]["authors"] = [
        "C. A. Neal", "S. R. Brantley", "L. Antolik", "J. L. Babb", "M. Burgess", "K. Calles", "M. Cappos",
        "J. C. Chang", "S. Conway", "L. Desmither", "P. Dotray", "T. Elias", "P. Fukunaga", "S. Fuke",
        "I. A. Johanson", "K. Kamibayashi", "J. Kauahikaua", "R. L. Lee", "S. Pekalib", "A. Miklius",
        "W. Million", "C. J. Moniz", "P. A. Nadeau", "P. Okubo", "C. Parcheta", "M. R. Patrick", "B. Shiro",
        "D. A. Swanson", "W. Tollett", "F. Trusdell", "E. F. Younger", "M. H. Zoeller", "E. K. Montgomery-Brown",
        "K. R. Anderson", "M. P. Poland", "J. L. Ball", "J. Bard", "M. Coombs", "H. R. Dietterich", "C. Kern",
        "W. A. Thelen", "P. F. Cervelli", "T. Orr", "B. F. Houghton", "C. Gansecki", "R. Hazlett", "P. Lundgren",
        "A. K. Diefenbach", "A. H. Lerner", "G. Waite", "P. Kelly", "L. Clor", "C. Werner", "K. Mulliken",
        "G. Fisher", "D. Damby",
    ]
    data["extraction_quality"]["status"] = "partial"
    data["extraction_quality"]["extraction_confidence"] = "medium"
    data["extraction_quality"]["needs_human_review"] = True
    data["extraction_quality"]["warnings"].append("Author/DOI metadata was recovered from the parsed title/citation block; DOI remains unresolved locally.")


def normalize(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    replace_legacy_paper_evidence(data)
    normalize_secondary_information(data)
    correct_matoza2014(data)
    correct_matoza2021(data)
    correct_usgs_overview(data)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    paths = args.paths or sorted((ROOT / "data").glob("*/references/*/parsed/extraction/*.json"))
    for raw in paths:
        path = raw if raw.is_absolute() else ROOT / raw
        normalize(path.resolve())
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
