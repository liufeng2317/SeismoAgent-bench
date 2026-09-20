#!/usr/bin/env python3
"""Normalize the first TAN2024 extraction into product-specific catalog products."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = ROOT / "data/2016_kaikoura_new_zealand/references/TAN2024_JB028735"
OUT = REF / "parsed/extraction/TAN2024_JB028735__extraction.json"
SI_DIR = REF / "parsed/supplement"
SOURCE = SI_DIR / "mineru/2024jb028735-sup-0001-supporting information si-s01/full.md"
STABLE = SI_DIR / "2024jb028735-sup-0001-supporting-information-si-s01__mineru.md"


def evidence(source: str, locator: str, note: str) -> dict:
    return {"source": source, "locator": locator, "note": note}


def make_stable_sidecar() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    prefix = "mineru/2024jb028735-sup-0001-supporting information si-s01/"
    text = text.replace("](images/", f"]({prefix}images/")
    header = (
        "<!-- Stable sidecar generated from the MinerU supplementary bundle. "
        "The original bundle remains under parsed/supplement/mineru/. -->\n\n"
    )
    STABLE.write_text(header + text, encoding="utf-8")


def normalize() -> None:
    d = json.loads(OUT.read_text(encoding="utf-8"))
    stable_rel = "data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/supplement/2024jb028735-sup-0001-supporting-information-si-s01__mineru.md"

    # Use a status consistent with unresolved evidence and human review flags.
    q = d["extraction_quality"]
    q["status"] = "partial"
    q["warnings"] = [
        "S10/S11 generic M field must not be relabeled as ML without calibration.",
        "Article-reported final 41,392-event product is not a local file.",
        "Exact row-level uncertainty fields and magnitude calibration/type need review.",
    ]
    q["needs_human_review"] = True

    # Make the product boundary explicit instead of presenting one merged schema.
    cat = d["catalog"]
    cat["product_type"] = "multi_product_release"
    cat["product_semantics"] = {
        "S10": "67,660-row SUGAR detected/located catalog; local canonical event table.",
        "S11": "46,440-row GrowClust-relocated intermediate table; not the final filtered set.",
        "final_cluster_filtered": "41,392 events reported by the article after retaining clusters with at least 10 events; standalone membership file is not local.",
        "S12": "55 focal-mechanism measurements; derived product, not a complete event catalog.",
    }
    cat["product_schemas"] = {
        "S10": {
            "role": "detected_located_catalog",
            "identifier_field": "ID",
            "fields": ["Time", "Lat", "Lon", "Dep", "M", "Picks", "AI score", "Brightness", "Q_e", "residual", "ID"],
            "units": {"Time": "UTC", "Lat": "degree", "Lon": "degree", "Dep": "km", "M": "unspecified catalog magnitude"},
            "evidence": [evidence("data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/supplement/2024jb028735-sup-0003-table si-s10__extracted.md", "Sheet1 header: Time, Lat, Lon, Dep, M, Picks, AI score, Brightness, Q_e, residual, ID", "S10 product-specific fields.")],
        },
        "S11": {
            "role": "relocated_intermediate_catalog",
            "identifier_field": "event identity carried from S10; exact ID mapping requires row-level audit",
            "fields": ["split origin-time fields", "relocated latitude", "relocated longitude", "relocated depth", "magnitude", "cluster id", "events in cluster"],
            "units": {"time": "UTC", "latitude": "degree", "longitude": "degree", "depth": "km", "magnitude": "inherited/unspecified M"},
            "evidence": [evidence("data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/supplement/2024jb028735-sup-0004-table si-s11__extracted.md", "Sheet1 header: relocation and cluster columns", "S11 product-specific fields.")],
        },
        "S12": {
            "role": "focal_mechanism_derived_product",
            "identifier_field": "event identifier in S12",
            "fields": ["event identity", "origin time", "location", "M", "strike", "dip", "rake", "mechanism quality fields"],
            "evidence": [evidence("data/2016_kaikoura_new_zealand/references/TAN2024_JB028735/parsed/supplement/2024jb028735-sup-0005-table si-s12__extracted.md", "Sheet1 header and 55 data rows", "S12 is a derived focal-mechanism product, not the full catalog.")],
        },
    }
    cat.pop("schema", None)
    cat["release"]["evidence"].append(evidence(stable_rel, "Data products and supplementary tables", "Stable supplementary sidecar used for extraction review."))
    cat["local_audit"]["event_count"] = None
    cat["local_audit"]["row_count"] = None
    cat["local_audit"]["product_counts"] = {"S10": 67660, "S11": 46440, "S12": 55, "final_cluster_filtered_reported": 41392}
    cat["local_audit"]["article_local_discrepancy"] = "S10 (67,660), S11 (46,440), and S12 (55) match local products; 41,392 is article-reported final membership without a local standalone file."

    # Replace broad section-only locators where the extraction already knows the product.
    for pop in cat["populations"]:
        if pop["population_id"] == "P1":
            pop["evidence"][1]["locator"] = "Section 4, S10 discussion; Supplementary Table S10 description"
        elif pop["population_id"] == "P2":
            pop["evidence"][1]["locator"] = "Section 4, GrowClust paragraph; Supplementary Table S11 description"
        elif pop["population_id"] == "P3":
            pop["evidence"][0]["locator"] = "Section 4, paragraph describing clusters with at least 10 events"
        elif pop["population_id"] == "P4":
            pop["evidence"][1]["locator"] = "Supplementary Table S12 discussion and mechanism-table description"
    # Use stable paragraph/table-level locators for the workflow evidence.
    stage_locators = {
        "ST1": "Section 2.2.1, source-scanning brightness-video construction paragraph",
        "ST2": "Sections 2.1–3.1, 3-D U-Net architecture/training paragraphs and real-data threshold",
        "ST3": "Section 2.2.3, candidate merging and guided P/S picking paragraph",
        "ST4": "Section 2.2.3, Equations 5–7 and event-retention paragraph",
        "ST5": "Sections 2.2.3–2.2.4, local-magnitude equation and station-correction paragraph",
        "ST6": "Section 4, GrowClust relocation paragraph and Supplementary Table S11 description",
        "ST7": "Section 4, cluster-size filtering paragraph and Supplementary Table S12 discussion",
    }
    for stage in d["construction_workflow"]["stages"]:
        if stage["stage_id"] in stage_locators:
            for item in stage.get("evidence", []):
                if item["source"].endswith("__paper__mineru.md"):
                    item["locator"] = stage_locators[stage["stage_id"]]

    d["article"]["evidence"][0]["locator"] = "title, abstract, author/DOI metadata"
    d["article"]["evidence"][1]["source"] = stable_rel
    d["article"]["evidence"][1]["locator"] = "supplementary-information contents and data-product sections"
    d["construction_workflow"]["evidence"][1]["source"] = stable_rel
    d["construction_workflow"]["evidence"][1]["locator"] = "supplementary-information method and data-product sections"

    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    make_stable_sidecar()


if __name__ == "__main__":
    normalize()
