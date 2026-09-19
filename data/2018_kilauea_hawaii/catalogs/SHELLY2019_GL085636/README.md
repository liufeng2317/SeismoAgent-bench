# Shelly & Thelen (2019) Kīlauea phase-arrival and catalog products

- `source_ref`: `SHELLY2019_GL085636`

- Source: Shelly & Thelen (2019), DOI [10.1029/2019GL085636](https://doi.org/10.1029/2019GL085636).
- Combined USGS phase-arrival release: [10.5066/P13JCJ2I](https://doi.org/10.5066/P13JCJ2I), ScienceBase item `667b1415d34e6151c9d6bcfd`.
- Core phase-arrival file: `raw/Kilauea_2018_correlation_phase_arrivals.csv` (8,582,492 data rows plus header).
- Additional high-resolution event-location products from the same study are retained in `raw/` (`data_S1_*`, `data_S2_*`, metadata XML, and `loc_events.txt`).
- The separate `loc_events.txt` product is staged under `catalogs/LENGLINE2021_EPSL116653/`; the Shelly bundle retains only its phase-arrival and S1/S2 summit products.
- Article Data Set S1 and S2 are staged at the catalog root as `SHELLY2019_GL085636__catalog_S1.txt` (44,188 events) and `SHELLY2019_GL085636__catalog_S2.txt` (43,950 clustered events); the Figure SI PDF is under the corresponding reference supplement.
