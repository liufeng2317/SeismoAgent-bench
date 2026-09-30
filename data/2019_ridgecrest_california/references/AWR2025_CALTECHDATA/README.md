# AWR2025_CALTECHDATA

Atterholt, Wilding & Ross (2025), *The evolution of fault orientation in the 2019 Ridgecrest earthquake sequence with a new long-term catalogue of seismicity and moment tensors*, *Geophysical Journal International* 240, 1579–1592. DOI: [10.1093/gji/ggaf001](https://doi.org/10.1093/gji/ggaf001).

- Paper: `paper/AWR2025_CALTECHDATA__paper.pdf`
- Paper reading: [`parsed/paper/AWR2025_CALTECHDATA__paper_reading.md`](parsed/paper/AWR2025_CALTECHDATA__paper_reading.md)
- Local catalogs: [`../../data/catalogs/AWR2025_CALTECHDATA/`](../../data/catalogs/AWR2025_CALTECHDATA)
- Catalog summary: [`../../data/catalogs/AWR2025_CALTECHDATA/README.md`](../../data/catalogs/AWR2025_CALTECHDATA/README.md)
- Current local provenance: [CaltechDATA 10.22002/5af05-cah73](https://doi.org/10.22002/5af05-cah73)
- Article data-availability DOI: [10.22002/f40da-hww21](https://doi.org/10.22002/f40da-hww21)

The local Version 2 release covers April 2019–May 2023 and includes hypocenter
and moment-tensor CSVs. The article reports 214,467/4,892 final products,
whereas local Version 2 contains 222,864/4,890 rows; both values are retained
as an explicit release-version discrepancy.
- Structured extraction: [`parsed/extraction/AWR2025_CALTECHDATA__extraction.json`](parsed/extraction/AWR2025_CALTECHDATA__extraction.json).

## Original-source audit — 2026-09-25

- `supplement/AWR2025_CALTECHDATA__supplement.zip`: 27,425,957 bytes; SHA-256 `65e9c3b2424177b009ce24640c4754bbfafac1a09f28994c39f80343640e776c`. Source: https://doi.org/10.1093/gji/ggaf001.
- `supplement/AWR2025_CALTECHDATA__supplement_figures.pdf`: 3,568,815 bytes; SHA-256 `bdb2fdf664ff2d9080453f6e4a912b33aceae2f92de6c489cd0106a01fc617a8`. Source: ZIP member Atterholt_Wilding_Ross_GJI_SI_Rev.pdf.

The publisher supporting-information link supplied the ZIP (no temporary signed URL stored). Its nested `AWR_Catalogs.zip` contains hypocenter and moment-tensor CSVs, not a station list. Only the supplementary PDF was extracted; existing Version 2 catalogs were not replaced. PDF page 2, Fig. S1, directly confirms networks CI, GS, NN, PB and ZY but provides no station labels or station-day table. Article-release byte equivalence with local Version 2 remains unverified.

Large original PDFs/ZIPs remain local and ignored by Git; this record tracks their source and checksums.

## Velocity-model acquisition

Hutton (2010) PDF archived at `supplement/HUTTON2010__paper.pdf`, Table 5 providing a documented SCSN HK implementation. UCVM modified HK and HypoSVI Julia example files downloaded as supporting candidates; none is confirmed as the actual AWR smoothed model or station terms.

File sources, fixed repository revisions, sizes and hashes: [model acquisition manifest](../../data/models/acquisition_manifest.json). Model roles and numeric status: [velocity models](../../data/models/velocity_models.json). Manual follow-up links are maintained in the [case analysis](../../analysis/RIDGE2019_analysis.md).
