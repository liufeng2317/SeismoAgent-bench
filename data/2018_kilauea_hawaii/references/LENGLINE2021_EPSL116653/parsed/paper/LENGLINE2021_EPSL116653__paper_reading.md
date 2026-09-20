# Lengliné, Duputel & Okubo (2021) — paper reading and dike catalog audit

## Identity and role

| Field | Extracted information | Evidence |
|---|---|---|
| Title | *Tracking dike propagation leading to the 2018 Kīlauea eruption* | PDF title |
| Authors / journal | Olivier Lengliné, Zacharie Duputel, P. G. Okubo; *Earth and Planetary Science Letters* | PDF title block |
| DOI | [10.1016/j.epsl.2020.116653](https://doi.org/10.1016/j.epsl.2020.116653) | Article metadata |
| Article type | Research article that builds a template-matched, dike-intrusion event product and uses it to infer migration, not a general island-wide catalog | Abstract; §§2–4 |
| Local product | `catalogs/LENGLINE2021_EPSL116653/raw/loc_events.txt` | Local supplementary/event table |

This is a genuine event-detection/location paper, but its catalog has a narrow
East Rift Zone role. It should be retained as a dike-propagation auxiliary, not
merged into the Shelly summit or Wei island-wide truth populations.

## Scope and observation conditions

- Study interval: 2018-04-29 00:00 UTC through 2018-05-04 21:00 UTC for the
  initial HVO templates and continuous search (PDF §2). The local file extends
  to `2018-05-04T23:58:59.520Z` when its relative-day coordinate is converted.
- Initial templates: 280 HVO catalog events, restricted to depth shallower than
  5 km to emphasize Middle East Rift Zone dike-related sources.
- Main detection channels: three components at JOKA plus the vertical component
  of KUPD or KLUD, selected according to template P-pick availability. This is
  a focused, sparse network condition rather than the full HVO network.
- Waveforms are HVO data accessible through IRIS. Templates are 5.12 s windows
  starting 1 s before P, filtered 2–20 Hz.

## Catalog-construction workflow

```text
HVO templates (280 shallow events)
    -> 2–20 Hz template matching on four selected channels
    -> daily threshold from reversed-template noise distribution
       (false-detection probability 10^-1 per day per template)
    -> 6,327 detections
    -> S/P differential-time cross-correlation and JOKA-distance inversion
    -> kurtosis P picking + pairwise differential-time grid-search location
    -> native x/y event-coordinate release and dike-migration interpretation
```

- The detection threshold is set to an expected 0.1 false detections per day
  per template; the paper estimates 168 expected false detections over the
  280-template, six-day search (PDF §2).
- JOKA distance inversion uses P/S differential times, P/S correlation >0.6,
  and differential travel time <0.15 s. The localization stage uses 2–20 Hz
  kurtosis P picks, an assumed 3-km depth, a dike-aligned prior, and an L1
  differential-time likelihood (PDF §§3.1–3.2).
- The paper estimates roughly 3–4 km depth near JOKA and follows the dike tip
  from Puʻu ʻŌʻō toward the first Lower East Rift Zone fissures. These are
  modeling assumptions/interpretations, not depth fields in the released table.

## Reported products and limitations

| Item | Article/local value |
|---|---:|
| HVO shallow templates | 280 |
| Detected events | 6,327 |
| Native table rows | 6,327 |
| Native fields | Relative time in days since 2018-04-29; x and y in metres relative to (19.3864°N, −155.1050°E) |
| Depth / magnitude / stable event ID | Not provided in the local three-column release |

The method is template-dependent and especially sensitive to proximity to JOKA;
the authors explicitly discuss missing templates, local sensitivity, and
seismicity gaps as possible detection biases (PDF §5.1). It therefore measures
dike-related recovery and migration timing, not uniform catalog completeness.

## Benchmark interpretation

- **Quality tier:** Q2 dike-event detection/migration auxiliary; Q4 for absolute
  hypocenter or magnitude evaluation because the released table lacks those
  fields.
- **Best use:** event-rate/migration chronology, spatial progression along the
  MERZ, and a domain-shift auxiliary to summit-focused catalogs.
- **Unsuitable use:** direct event-by-event location error against Shelly S1/S2,
  magnitude/b-value scoring, or a whole-island detection denominator.
- **Independence:** Medium: template waveforms and initial events come from HVO,
  but the focused four-channel matching and dike-specific localization differ
  from the Shelly workflow.

## Local provenance

- Paper: `paper/LENGLINE2021_EPSL116653__paper.pdf`
- Parsed paper: `parsed/LENGLINE2021_EPSL116653__paper__mineru.md`
- Supplement/event table: `catalogs/LENGLINE2021_EPSL116653/raw/loc_events.txt`
- Supporting text/PDF: `references/LENGLINE2021_EPSL116653/supplement/`
