# Matoza, Shearer & Okubo (2014) — paper reading and LP catalog audit

## Identity and scope

| Field | Extracted information | Evidence |
|---|---|---|
| Title | *High-precision relocation of long-period events beneath the summit region of Kīlauea Volcano, Hawaiʻi, from 1986 to 2009* | PDF title |
| DOI / journal | [10.1002/2014GL059819](https://doi.org/10.1002/2014GL059819), *Geophysical Research Letters* 41, 3413–3421 | Citation block |
| Article type | Research article constructing an automated LP classification and relative-relocation catalog | Abstract; §§2–3 |
| Study span | January 1986–March 2009 | Abstract; §2 |
| Initial population | 49,030 summit-region HVO events; 41,475 pass P-spectrum SNR checks | Abstract; Fig. 1 |
| LP selection | 12,290 events with station-averaged frequency index FI ≤ −1 | §2; Fig. 2 |
| Relocated subset | 5,327 LP events; final SSST-aligned subset 5,199 | Abstract; §3 |

The paper constructs a real catalog, but it is a historical LP-event product and
has no temporal overlap with the 2018 eruption benchmark. It is an auxiliary
source-type/control catalog, not a candidate primary reference for the 2018
summit sequence.

## Observation and processing

- Input waveforms come from the approximately 50-station HVO permanent network,
  resampled to 100 Hz; most early instruments are 1-Hz short-period vertical
  geophones. The study uses a summit box 19.35–19.45°N, −155.35–−155.15°W,
  depth ≤20 km.
- P spectra use 1.28-s noise/signal windows and 1–15 Hz SNR >3. FI is the
  log-amplitude ratio of 5–15 Hz to 1–5 Hz bands; FI ≤−1 defines LP events.
- Waveform cross-correlation is 1–10 Hz, P vertical-component windows, with
  event pairs within 2 km or 100 nearest neighbours. P-pair average correlation
  >0.45 and at least eight differential times with coefficient >0.75 (source
  distance <80 km) are required for relocation.
- Relative relocation uses cluster analysis plus the source-specific station
  term method and bootstrap uncertainties. Absolute cluster centroids remain
  tied to 1-D CUSP starting locations; unmodeled 3-D structure can produce much
  larger absolute errors.

## Benchmark interpretation

- **Quality tier:** Q1 relative geometry for the 5,199 relocated LP events;
  Q2/Q4 for LP classification completeness because FI distributions overlap
  and shallow LPs are underrepresented.
- **Role:** historical LP source-type auxiliary and a method precedent for
  waveform correlation/relocation; not a 2018 event truth set.
- **Limitations:** no 2018 rows, LP-only selection, 1-D velocity model, and
  relative rather than absolute location accuracy. Do not use it for the frozen
  2018 summit event count or magnitude completeness.
