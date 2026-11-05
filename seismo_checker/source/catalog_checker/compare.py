"""Compare two checker reports of the same stage: a current product and a candidate that replaces it.

Judging one catalog on its own is hard; deciding which of two catalogs built from the same data is
better is easier, because most of what differs between correct catalogs (velocity structure,
station geometry, data quality) is shared by both. The comparison uses the judged (product) checks
only. Each check has a direction (lower, closer to zero, higher, or inside its range) and a noise
tolerance; a change smaller than the tolerance counts as no change. Checks that are known not to
rank the kind of change being compared are listed but not counted, with the reason.

The rule, fixed before any comparison is made:
- ``better``: at least one counted check improves (or its flag clears), none worsens (or flags);
- ``worse``: at least one worsens, none improves;
- ``mixed``: some improve and some worsen; the comparison alone does not decide;
- ``no_difference``: nothing changes beyond the tolerances.
A ``better`` that comes only from share checks while the candidate drops more than
``removed_share_max`` of the events is downgraded to ``uncertain``: removing events lowers shares
whether or not the removed events were wrong. Flags that remain in the candidate are listed: a
candidate that still fails is not shown to be right by being less wrong.
"""

from __future__ import annotations

import math

# direction of each judged check: "lower", "abs" (closer to zero), "higher", "range" (inside its expected range)
DIRECTION = {
    "silent_stations": "lower", "station_day_gaps": "lower", "duplicate_picks": "lower", "s_to_p_ratio": "range",
    "associated_share": "higher", "association_busy_hours": "higher", "duplicate_events": "lower",
    "events_with_few_picks": "lower", "isolated_events": "lower", "wadati_origin_spread": "lower",
    "depth_single_value": "lower", "depth_at_edges": "lower", "depth_layers": "lower", "sp_depth_offset": "abs",
    "pick_onset_offset": "abs", "processing_time_shift": "abs", "relocated_share": "higher", "relocation_shift": "abs",
    "relocation_large_moves": "lower", "relocation_thinning": "range", "magnitude_range": "range",
    "magnitude_detection": "range", "magnitude_recompute": "abs", "largest_events_magnitude": "abs",
}
# smallest change that counts, by unit (shares also by their binomial scatter)
TOLERANCE = {"share": 0.01, "ratio": 0.05, "km": 0.3, "s": 0.05, "magnitude": 0.15, "log10 mm": 0.15}
# kinds of change a check cannot rank, with the reason
NOT_RANKING = {
    "velocity_model": {"depth_layers": "thin depth slices also form at the interfaces of a correct layered velocity model, "
                                       "so a layered model can raise this share while being closer to the truth"},
    "event_selection": {},
}
CHANGES = ("velocity_model", "location_method", "picks", "association", "event_selection", "relocation", "magnitude", "other")
COMPARE_DEFAULTS = {"removed_share_max": 0.05}


def _tolerance(unit: str, a: float, b: float, n: int) -> float:
    tol = TOLERANCE.get(unit, 0.0)
    if unit == "share" and n > 0:
        p = min(max((a + b) / 2.0, 0.0), 1.0)
        tol = max(tol, 2.0 * math.sqrt(2.0 * p * (1.0 - p) / n))
    return tol


def _score(direction: str, value: float) -> float:
    """A number that is smaller when the check is better."""
    if direction == "higher":
        return -value
    if direction == "abs":
        return abs(value)
    return value


def compare_reports(before: dict, after: dict, change: str = "other", config: dict | None = None) -> dict:
    c = {**COMPARE_DEFAULTS, **(config or {})}
    excluded = NOT_RANKING.get(change, {})
    a_checks = {k["id"]: k for k in before["checks"]}
    b_checks = {k["id"]: k for k in after["checks"]}
    rows, improved, worsened, not_counted = [], [], [], []
    for cid in [k for k in a_checks if k in b_checks]:
        a, b = a_checks[cid], b_checks[cid]
        if a["kind"] != "product" or b["kind"] != "product":
            continue
        row = {"id": cid, "dimension": a["dimension"], "unit": a["unit"], "before": a["measured"], "after": b["measured"],
               "flag_before": a["flag"], "flag_after": b["flag"], "n_before": a["n"], "n_after": b["n"]}
        direction = DIRECTION.get(cid, "range")
        if a["measured"] is None or b["measured"] is None:
            row["change"] = "not_comparable"
        else:
            tol = _tolerance(a["unit"], a["measured"], b["measured"], min(a["n"], b["n"]))
            delta = _score(direction, b["measured"]) - _score(direction, a["measured"])
            row.update({"direction": direction, "tolerance": round(tol, 4)})
            if a["flag"] and not b["flag"]:
                row["change"] = "flag_cleared"
            elif b["flag"] and not a["flag"]:
                row["change"] = "flag_raised"
            elif direction == "range":
                row["change"] = "same"
            elif delta < -tol:
                row["change"] = "improved"
            elif delta > tol:
                row["change"] = "worsened"
            else:
                row["change"] = "same"
        if cid in excluded and row["change"] not in ("same", "not_comparable"):
            row["not_counted"] = excluded[cid]
            not_counted.append(cid)
        elif row["change"] in ("improved", "flag_cleared"):
            improved.append(cid)
        elif row["change"] in ("worsened", "flag_raised"):
            worsened.append(cid)
        rows.append(row)
    ev_a, ev_b = before["counts"]["events"], after["counts"]["events"]
    removed = (ev_a - ev_b) / ev_a if ev_a else 0.0
    if improved and not worsened:
        verdict = "better"
        shares_only = all(next(r for r in rows if r["id"] == k)["unit"] == "share" for k in improved)
        if shares_only and removed > c["removed_share_max"]:
            verdict = "uncertain"
    elif worsened and not improved:
        verdict = "worse"
    elif improved and worsened:
        verdict = "mixed"
    else:
        verdict = "no_difference"
    remaining = [f["flag_id"] for f in after["flags"]]
    context = []
    for cid in [k for k in a_checks if k in b_checks]:
        a, b = a_checks[cid], b_checks[cid]
        if "report_only" in (a["kind"], b["kind"]) and a["measured"] is not None and b["measured"] is not None:
            context.append({"id": cid, "unit": a["unit"], "before": a["measured"], "after": b["measured"]})
    notes = []
    if verdict == "uncertain":
        notes.append(f"the candidate drops {removed:.1%} of the events and its improvements are all shares, which removing events lowers by itself")
    if verdict == "mixed":
        notes.append("the checks disagree; decide with an experiment that separates the explanations, not by counting checks")
    if remaining:
        notes.append(f"{len(remaining)} flag(s) remain in the candidate; a candidate that still fails is not shown to be right by being less wrong")
    if before.get("stage") != after.get("stage"):
        notes.append(f"the reports are of different stages ({before.get('stage')} and {after.get('stage')}); only shared checks are compared")
    return {"change": change, "verdict": verdict, "improved": improved, "worsened": worsened, "not_counted": not_counted,
            "flags_before": [f["flag_id"] for f in before["flags"]], "flags_after": remaining,
            "events": {"before": ev_a, "after": ev_b, "removed_share": round(removed, 4)},
            "checks": rows, "reported_only_context": context, "notes": notes,
            "rule": __doc__.split("The rule, fixed before any comparison is made:")[1].strip()}
