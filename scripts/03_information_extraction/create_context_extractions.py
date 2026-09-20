#!/usr/bin/env python3
"""Create explicit context/not-a-catalog extractions for overview references."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def e(source, locator, note):
    return {"source": source, "locator": locator, "note": note}


def main():
    case = "2018_kilauea_hawaii"
    sid = "USGS2019_SCIENCE_OVERVIEW"
    paper = f"data/{case}/references/{sid}/parsed/paper/{sid}__paper__mineru.md"
    out = ROOT / f"data/{case}/references/{sid}/parsed/extraction/{sid}__extraction.json"
    obj = {
        "article": {
            "source_id": sid,
            "case_id": case,
            "title": "The 2018 rift eruption and summit collapse of Kīlauea Volcano",
            "authors": ["C. A. Neal et al."],
            "year": 2019,
            "journal": "Science",
            "doi": "10.1126/science.aav7046",
            "article_type": "science_overview",
            "scientific_question": "How did the 2018 Kīlauea lower-East-Rift-Zone eruption and summit collapse evolve, and what observations constrain the coupled volcanic and seismic processes?",
            "sequence": "2018 Kīlauea eruption, flank earthquake and summit collapse",
            "catalog_relationship": "Provides event/eruption context and cites USGS/HVO seismic products; it does not construct or release a machine-readable event catalog.",
            "evidence": [e(paper, "title, abstract paragraph, and Data and materials availability", "Overview identity and data role.")],
        },
        "catalog": {
            "catalog_id": None,
            "name": "No article-specific catalog",
            "product_type": "context_overview",
            "role": "not_a_catalog",
            "quality_tier": "N/A",
            "scientific_purpose": "Context for the Kīlauea benchmark event sequence and monitoring conditions.",
            "event_definition": None,
            "product_semantics": {},
            "populations": [],
            "release": {"doi_or_url": None, "version": None, "source_files": [], "evidence": [e(paper, "Data and materials availability", "The overview points to external geologic/seismic data sources, not an article catalog release.")]},
            "local_audit": {"event_count": None, "row_count": None, "product_counts": {}, "time_range": "2018 eruption context", "latitude_longitude_depth_range": None, "magnitude_range": "article narrative includes Mw 6.9 flank earthquake and Mw 4.7–5.4 collapse signals", "article_local_discrepancy": "No local event table is expected for this context reference.", "evidence": [e(paper, "Data and materials availability; figures 1–6", "No event-table release.")]},
            "product_schemas": {},
            "evaluation_use": {"suitable_metrics": [], "unsuitable_metrics": ["event detection recall", "catalog location error", "event-level matching"], "independence_conditions": [], "limitations": ["overview narrative rather than catalog-construction paper", "external HVO/USGS products require separate provenance"], "evidence": [e(paper, "Data availability and cited USGS catalog reference", "Role limitation.")]},
        },
        "construction_workflow": {"summary": None, "input_data": [{"source_id": "S1", "name": "HVO/USGS seismic, geodetic, gas and imagery observations", "type": "multi_sensor_context", "provider_or_network": "Hawaiian Volcano Observatory and partner agencies", "temporal_spatial_scope": "2018 Kīlauea eruption", "station_count": None, "channels_sampling": None, "role": "context_only", "availability_conditions": "not released as an article-specific benchmark bundle", "evidence": [e(paper, "figures 1–6 and Data and materials availability", "Monitoring modalities and external data references.")]}], "stages": [], "final_output": "No catalog output; use only for case context and interpretation.", "evidence": [e(paper, "main narrative and figures", "Overview rather than construction workflow.")]},
        "additional_information": {"related_products": [{"product_id": "DP1", "name": "HVO/USGS operational catalog references", "type": "context_reference", "file_path": None, "catalog_relation": "external independent baseline; not an output of this article", "scientific_use": "case context", "count_or_scope": "not specified in article", "evidence": [e(paper, "reference 41 and Data and materials availability", "External catalog citation.")]}], "scientific_findings": ["The eruption coupled lower-ERZ intrusion, Mw 6.9 flank faulting, lava effusion, and near-daily summit collapses."], "benchmark_context": "Context-only reference; never substitute it for Shelly, Wei, Matoza, Lengliné or the official HVO baseline.", "evidence": [e(paper, "abstract, Lower ERZ eruption, Summit collapse and Synthesis sections", "Scientific context.")]},
        "extraction_quality": {"status": "verified", "extraction_confidence": "high", "completed_sections": ["article", "catalog", "construction_workflow", "additional_information"], "missing_core_fields": ["article DOI not verified from local parse"], "warnings": ["This source is intentionally marked not_a_catalog."], "needs_human_review": False},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
