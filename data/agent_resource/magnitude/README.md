# Local magnitude (ML): formulas, units and a reference implementation

This folder gives the standard definition of the local magnitude with every unit stated, the mistakes that most often shift magnitudes by whole units, and a reference implementation you can use to check your own magnitude code. The source documents are in `../magnitude_standards/`: the IASPEI standard (IASPEI 2013 summary; NMSOP-2 IS 3.3), the compilation of regional calibration functions (NMSOP-2 DS 3.1, Table 2), worked exercises (NMSOP-2 EX 3.1), Hutton & Boore (1987), Uhrhammer et al. (2011) and the Chinese national standard GB 17740-2017.

## 1. The standard relation

IASPEI standard (IS 3.3 eq. 1; DS 3.1 eq. 2), for crustal earthquakes in regions with attenuation similar to southern California:

`ML = log10(A) + 1.11 log10(R) + 0.00189 R − 2.09`

- `A`: the largest amplitude in **nanometres (nm)** on a **horizontal** component whose response replicates a Wood-Anderson (WA) seismograph **with static magnification 1**. Amplitude means one half of the largest deflection from a peak to the adjacent trough ("half peak-to-peak"), not the full peak-to-trough deflection.
- Each horizontal component is a separate measurement; no vector sum, no measuring both components at the same time.
- `R`: **hypocentral** distance in km (typically < 1000 km), from the hypocentre to the station including the source depth and the station elevation.
- Event ML: commonly the median (or mean) of the station values.

The same relation for amplitudes read on a classical WA record (static magnification **2080**, trace amplitude in **millimetres**), Hutton & Boore (1987), expanded:

`ML = log10(A_mm) + 1.11 log10(R/100) + 0.00189 (R − 100) + 3.0 = log10(A_mm) + 1.11 log10(R) + 0.00189 R + 0.591`

They are the same scale: `A_mm = 2080 × A_nm × 10⁻⁶`, so `log10(A_mm) = log10(A_nm) − 2.682`. Check: 1 mm on a WA record at R = 100 km is ML 3.0 in both forms (Richter's definition).

Regions whose attenuation differs from southern California, or vertical-component measurements, use `ML = log10(A) + C(R) + D` with a calibrated `C(R)` and `D` (IS 3.3 eq. 2). DS 3.1 Table 2 lists published regional calibration functions; the Chinese standard GB 17740-2017 gives the calibration function used in China. §5 describes the machine-readable library built from these sources. Before using one, check in the source: amplitude unit (mm on a WA record, or nm), WA magnification assumed (2800 in pre-1990 work, "oWA"; 2080 in later work, "nWA"), component (horizontal or vertical), distance type (epicentral Δ or hypocentral R) and the valid distance range. Where no regional calibration exists, IASPEI recommends the standard relation.

## 2. The Wood-Anderson response

IASPEI standard WA displacement response (IS 3.3 Table 1, after Uhrhammer & Collins, 1990): zeros `0, 0`; poles `−5.49779 ± 5.60886i` rad/s (free period 0.8 s, damping 0.7); normalised to 1 at 4 Hz with `A0 = 1.0028`; static magnification 1 for the nm form, 2080 for the classical record.

This displacement response has **two zeros** and applies to **displacement** input. A WA response with **one zero** applies to **velocity** input and returns the same WA displacement record. ObsPy's built-in `obspy.signal.invsim.WOODANDERSON` is of the second kind (one zero, poles `−6.283 ± 4.7124i`, damping 0.8, sensitivity 2080): use it on velocity (`remove_response(output="VEL")`) or on the raw record through the instrument response, not on displacement. Applied to a displacement record it loses a factor 2πf: amplitudes come out about 10–30 times too small near 2–5 Hz, magnitudes 1.1–1.5 units too low.

## 3. Unit chain and the mistakes that shift every magnitude

`counts → (remove instrument response) → ground displacement in m → (WA response, magnification 1) → m → × 10⁹ → nm → standard relation`

or, for the classical form, `… → WA response with magnification 2080 → m → × 10³ → mm → Hutton & Boore form`.

| Mistake | Effect on ML |
|---|---|
| WA record amplitude in mm used with the −2.09 constant (or nm with +0.591) | −2.68 (or +2.68) |
| One-zero (velocity-input) WA response applied to displacement | about −1.1 to −1.5, frequency dependent |
| Amplitude in m or µm instead of nm (or mm) | ±3 or ±6 |
| Full peak-to-peak instead of half peak-to-peak | +0.30 |
| Magnification 2800 where the formula assumes 2080 (or the reverse) | ±0.13 |
| Epicentral instead of hypocentral distance | small far away, up to several tenths at short distance |
| Instrument response not removed (counts), or sensitivity applied twice | arbitrary, often several units |
| Velocity or acceleration record treated as displacement | frequency dependent, often more than one unit |
| Vector sum of the horizontals instead of one value per component | about +0.15 |
| Clipped records of large events, or a window that ends before the S-wave maximum | large events too small |
| Keeping only records above a signal-to-noise threshold | small events 0.1–0.25 too large: the scale is compressed |
| A window far beyond the S train in a busy sequence | small events too large where other events arrive in the window |

A pipeline with one of the first five mistakes gives magnitudes that are offset by an almost constant amount: compare a few events against an independent computation before trusting the scale.

## 4. Reference implementation

`ml_reference.py` (Python, ObsPy):

```bash
python ml_reference.py selftest
python ml_reference.py recompute --catalog catalog.csv --picks picks.csv \
    --stations <StationXML file or folder> --waveforms <folder of NET.STA.LOC.CHA__start__end.mseed> \
    --events 30 --output-dir ml_check/
```

- `selftest` checks the two forms of the relation against each other (1 mm at 100 km = ML 3.0), the size of the mm/nm mistake, the WA response at 0.5, 4 and 20 Hz and the half peak-to-peak measurement.
- `recompute` samples events evenly by number of picks, removes the instrument response to displacement, applies the IASPEI WA response, reads the half peak-to-peak amplitude of each horizontal component between 1 s before the first pick and the end of the S train, and reports per-station and per-event standard ML with the median difference "catalog − reference" (`summary.json`, `event_ml.csv`, `station_ml.csv`).
- The functions `ml_iaspei`, `ml_hutton_boore_mm`, `wa_trace_nm` and `half_peak_to_peak` can be imported and used directly.

How to read the difference: an offset that is nearly constant across events (small spread) and close to one of the values in §3 points to a units or response mistake in the magnitude code; an offset of a few tenths can be a legitimate regional calibration; a difference that grows with magnitude points to clipping, saturation or a window that misses the maximum.

## 5. Regional calibration library

`calibrations.json` holds −log A₀ functions from standard compilations, one entry per region or branch: the IASPEI standard, Richter's (1958) table, the regional functions of NMSOP-2 DS 3.1 Table 2 (southern California, California, Mexico, the US Intermountain Belt, eastern North America, NW Turkey, Greece, Albania, central Europe, SW Germany, Norway/Fennoscandia, Tanzania, South Africa, South Australia) and the five regional tables of GB 17740-2017 (China). Each entry states:

- `expressions` (Python, `log` = log10; `R` hypocentral km, `D` epicentral km, `T` period s, `ML` a first estimate for magnitude-dependent branches) with their validity, or a `table` of distance and −log A₀;
- `amplitude`: unit (mm on a WA record, nm, or µm), instrument (old or new WA response, DD-1 short-period simulation), what is measured and how components are combined;
- `distance`, `station_correction` (station terms are network specific and are **not** included; the magnitudes then carry the average station term only), `source` and `verification`;
- `anchor`: the value Richter's definition requires in the entry's own units (3.0 at 100 km for mm, 0.318 for nm, 2.0 at 17 km where ML 3 is defined as 10 mm at 17 km); `selftest` checks every entry against it.

`ML = log10(A) + minus_log_a0(entry_id, R=..., D=..., T=..., ML=..., component=...)`, with `A` exactly as the entry defines it. Choosing an entry: use the region where the earthquakes and stations are; where no entry covers it, IASPEI recommends the standard relation. Check the amplitude convention before anything else (§3): a regional function applied to amplitudes in the wrong unit or from the wrong instrument shifts every magnitude by the same mistake as in the standard relation. The reference implementation simulates the WA response only; the GB 17740 tables need a DD-1 simulation (GB 17740-2017 Annex B.1).

Note on DS 3.1 Table 2: in the source PDF the formula column from the Greek branch for ML ≤ 3.7 (printed in the last NW Turkey row) down to South Australia is printed one row above its region. The library assigns each formula to the row below, which every anchor test and the amplitude units stated in the table confirm; the entries concerned say so in `verification`. Consult the original publication where a value matters.
