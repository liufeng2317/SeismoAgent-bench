# Matoza, Okubo & Shearer (2021) — paper reading and island-wide catalog audit

## Identity and scientific role

| Field | Extracted information | Evidence |
|---|---|---|
| Title | *Comprehensive High-Precision Relocation of Seismicity on the Island of Hawaiʻi 1986–2018* | PDF title |
| DOI / journal | [10.1029/2020EA001253](https://doi.org/10.1029/2020EA001253), *Earth and Space Science* 7, e2020EA001253 | Citation block |
| Article type | Research article constructing a systematic island-wide starting and GrowClust-relocated catalog | Abstract; §§2–4 |
| Full population | 347,445 article-reported events (local release has 347,446 rows) | Abstract/§2 vs local README audit |
| Relocated population | 275,009 article-reported (79%); local v2 README reports 299,966 for the revised release | Article conclusion vs 2025 local release README |
| Study span | 1986-01-01–2018-12-31 | §2.1; local file |

This is a genuine high-precision relocation paper and the most useful island-wide
location auxiliary for Kīlauea. It is not an independent detection catalog:
waveform triggers and phase association are inherited from HVO, and relocation
is relative within clusters.

## Observation and catalog construction

- Starting hypocenters and event-based waveforms come from HVO CUSP (1986–2009,
  144 channels) and AQMS (2009–2018, 565 channels), merged to a common EFS format
  and resampled at 100 Hz. The paper does not give one fixed station count;
  channel inventory changes substantially over the 32-year span.
- Events are paired with at least 100 nearest neighbours or all events within
  2 km (about 770 million pairs). Waveforms are filtered 1–10 Hz and P/S
  cross-correlated on available stations/components.
- Pair retention requires average P/S correlation `r > 0.45`, at least eight
  differential-time measurements with `r > 0.65`, and source-station distance
  <80 km. GrowClust performs cluster-relative relocation with bootstrap/error
  controls using a 1-D Klein (1981) velocity model; no reassociation is done.
- The paper reports an approximate local magnitude of completeness 1.5, but many
  automated triggers have unassigned magnitudes. Relative locations improve
  precision while cluster centroids retain starting-catalog/3-D-structure bias.

## Local release audit

The 2025 revised archive README defines 26 fields: relocated time/ID/lat/lon/depth,
magnitude, qID/cID/nbranch, pair/differential-time counts, RMS residuals,
location errors, starting lat/lon/depth, and polygon number. The `nbranch > 1`
rule identifies successful relocation.

- Local file: 347,446 rows, 299,966 with `nbranch > 1`, 47,480 retained at
  starting locations; full time 1986-01-01 to 2018-12-31 UTC.
- Relocated native ranges: lat 18.5633–21.1791°, lon −156.49609 to −154.37070°,
  depth −0.003–202.48 km; magnitudes −0.77–9.0. The local release's counts and
  fields supersede older article counts for file auditing, but both values are
  retained because the article and revised release differ.
- 2018-05-01–05-09 UTC: 2,999 rows total, 2,579 successfully relocated.
  The archive README maps columns 8–10 to relocated (`latR/lonR/depR`) and
  columns 23–25 to starting (`latC/lonC/depC`) coordinates. Under the common
  summit mask, the relocated-coordinate selection is 1,130 rows (984 with
  `nbranch > 1`); the starting-coordinate selection is 1,190 rows (1,044 with
  `nbranch > 1`). The detailed time/lat/lon/depth/magnitude ranges are recorded
  in the paired catalog summary.

## Benchmark interpretation

- **Quality tier:** Q1 relative island-wide geometry; Q2 detection/absolute
  location cross-check; metric-specific, not universal absolute truth.
- **Best use:** broader-island and flank comparison to Shelly/Wei, relative
  relocation geometry, and sensitivity to changing HVO instrument generations.
- **Limitations:** inherited HVO event triggers/association, 1-D velocity model,
  variable channel coverage, cluster-centroid absolute bias, and release-version
  discrepancy (article 347,445/275,009 vs local revised 347,446/299,966).
- **Frozen-role decision:** use the local `nbranch > 1` flag explicitly; do not
  replace Shelly's dense summit reference or call the 1,044 common-mask rows a
  standalone 2018 ground truth.
