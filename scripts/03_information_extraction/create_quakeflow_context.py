#!/usr/bin/env python3
"""Record QuakeFlow as method context, not as a falsely substituted catalog."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def e(source, locator, note):
    return {"source": source, "locator": locator, "note": note}


def main():
    case, sid = "2018_kilauea_hawaii", "QUAKEFLOW_GJI_GGAC355"
    paper = f"data/{case}/references/{sid}/parsed/paper/{sid}__paper__mineru.md"
    evaluation = f"data/{case}/references/{sid}/parsed/paper/{sid}__evaluation__mineru.md"
    out = ROOT / f"data/{case}/references/{sid}/parsed/extraction/{sid}__extraction.json"
    obj = {
        "article": {
            "source_id": sid,
            "case_id": case,
            "title": "QuakeFlow: a scalable machine-learning-based earthquake monitoring workflow with cloud computing",
            "authors": ["W. Zhu", "A. B. Hou", "R. Yang", "A. Datta", "S. M. Mousavi", "W. L. Ellsworth", "G. C. Beroza"],
            "year": 2022,
            "journal": "Geophysical Journal International",
            "doi": "10.1093/gji/ggac355",
            "article_type": "workflow_method_paper",
            "scientific_question": "Can a scalable PhaseNet–GaMMA monitoring workflow process continuous seismic data and improve event detection across regional applications?",
            "sequence": "Hawaii application including Kīlauea context",
            "catalog_relationship": "Describes a workflow and Hawaii application, but no dedicated machine-readable Hawaii event catalog is released locally or identified by the paper.",
            "evidence": [e(paper, "title, abstract, Hawaii application and Data Availability", "Peer-reviewed workflow identity."), e(evaluation, "scope and article–catalog alignment", "Evaluation document explicitly separates method paper from catalog.")],
        },
        "catalog": {
            "catalog_id": None,
            "name": "No dedicated QuakeFlow Hawaii catalog",
            "product_type": "method_context",
            "role": "not_a_catalog",
            "quality_tier": "N/A",
            "scientific_purpose": "Method context and future reproduction target for automated earthquake monitoring.",
            "event_definition": None,
            "product_semantics": {},
            "populations": [],
            "release": {"doi_or_url": "https://github.com/AI4EPS/QuakeFlow; https://doi.org/10.5281/zenodo.7023970", "version": None, "source_files": [], "evidence": [e(paper, "Data Availability", "Code release is not an event-catalog release.")]},
            "local_audit": {"event_count": None, "row_count": None, "product_counts": {}, "time_range": None, "latitude_longitude_depth_range": None, "magnitude_range": None, "article_local_discrepancy": "The article's qualitative 'more events than HVO' statement has no released numerator/denominator or frozen query locally.", "evidence": [e(evaluation, "article–catalog alignment decision", "No local QuakeFlow event table.")]},
            "product_schemas": {},
            "evaluation_use": {"suitable_metrics": ["workflow design", "catalog-QC procedure design", "future reproduction comparison"], "unsuitable_metrics": ["event-level scoring now", "catalog recall/precision", "using HVO/Wei/Shelly files as QuakeFlow output"], "independence_conditions": ["obtain and freeze a genuine QuakeFlow Hawaii event/pick release before scoring"], "limitations": ["no Hawaii event file", "no exact Hawaii time/space window", "no station-day or waveform manifest"], "evidence": [e(evaluation, "benchmark role and acquisition/reproduction gate", "Current role and missing release.")]},
        },
        "construction_workflow": {
            "summary": "Continuous waveforms → PhaseNet phase picking → GaMMA association → event location/magnitude → database/web application; Hawaii application is not accompanied by a released event table.",
            "input_data": [{"source_id": "S1", "name": "Continuous seismic waveforms", "type": "waveform", "provider_or_network": "HVO/USGS and other named data centers", "temporal_spatial_scope": "application-dependent; Hawaii exact bounds not specified", "station_count": None, "channels_sampling": None, "role": "primary_input", "availability_conditions": "no Hawaii request manifest locally", "evidence": [e(paper, "Data Availability and workflow description", "Named waveform sources."), e(evaluation, "input data and observation conditions", "No reproducible Hawaii manifest.")] }],
            "stages": [{"stage_id": "ST1", "order": 1, "name": "neural phase picking", "category": "picking", "purpose": "Detect P/S phases from continuous waveforms", "inputs": ["continuous waveforms"], "outputs": ["phase picks"], "method": "PhaseNet-style machine-learning phase picking", "software_or_model": "PhaseNet", "parameters": [], "qc_and_rejection_rules": [], "intermediate_result": None, "analyst_intervention": None, "dependencies": "waveform quality and station metadata", "evidence": [e(paper, "workflow architecture and processing sections", "Generic workflow stage.")]}, {"stage_id": "ST2", "order": 2, "name": "phase association", "category": "association", "purpose": "Group picks into event hypotheses", "inputs": ["P/S picks"], "outputs": ["associated events"], "method": "Gaussian-mixture association", "software_or_model": "GaMMA", "parameters": [], "qc_and_rejection_rules": [], "intermediate_result": None, "analyst_intervention": None, "dependencies": "station geometry and travel-time structure", "evidence": [e(paper, "workflow architecture and Hawaii application", "Association stage.")]}, {"stage_id": "ST3", "order": 3, "name": "location and catalog QC", "category": "location", "purpose": "Create event records and compare against reference catalog", "inputs": ["associated picks", "velocity/location model"], "outputs": ["event records in application database"], "method": "regional event location and catalog comparison/QC", "software_or_model": None, "parameters": [], "qc_and_rejection_rules": ["evaluation guidance distinguishes MATCH, MISSED and NEW events"], "intermediate_result": "No local Hawaii event table", "analyst_intervention": None, "dependencies": "application-specific data and reference snapshot", "evidence": [e(evaluation, "catalog-QC guidance", "Evaluation procedure, not a released catalog.")] }],
            "final_output": "Method workflow and qualitative Hawaii comparison; no locally scored event catalog.",
            "evidence": [e(paper, "workflow architecture", "End-to-end method."), e(evaluation, "article–catalog alignment decision", "No catalog substitution.")],
        },
        "additional_information": {"related_products": [{"product_id": "DP1", "name": "catalog evaluation guidance", "type": "evaluation_method", "file_path": evaluation, "catalog_relation": "methodological context, not event data", "scientific_use": "define MATCH/MISSED/NEW and snapshot requirements", "count_or_scope": "no event rows", "evidence": [e(evaluation, "catalog fields and QC guidance", "Evaluation concepts.")]}], "scientific_findings": ["The paper reports qualitative improvement over HVO in Hawaii, but the exact event table and numerator/denominator are not locally available."], "benchmark_context": "Future reproduction target; do not substitute any independent Kīlauea catalog as QuakeFlow output.", "evidence": [e(evaluation, "benchmark role and limitations", "Current benchmark decision.")]},
        "extraction_quality": {"status": "verified", "extraction_confidence": "high", "completed_sections": ["article", "catalog", "construction_workflow", "additional_information"], "missing_core_fields": ["dedicated Hawaii event/pick release", "exact Hawaii time/space window", "station/waveform manifest"], "warnings": ["Intentionally marked not_a_catalog; code DOI and HVO comparison must not be treated as a catalog release."], "needs_human_review": False},
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
