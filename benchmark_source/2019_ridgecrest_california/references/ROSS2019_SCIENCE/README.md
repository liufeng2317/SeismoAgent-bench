# Ross et al. (2019) — Ridgecrest QTM catalog

- DOI: [10.1126/science.aaz0109](https://doi.org/10.1126/science.aaz0109)
- Official data page: [SCEDC QTM Ridgecrest catalog](https://scedc.caltech.edu/data/qtm-ridgecrest.html)
- Paper: `paper/ROSS2019_SCIENCE__paper.pdf`
- Paper reading: [`parsed/paper/ROSS2019_SCIENCE__paper_reading.md`](parsed/paper/ROSS2019_SCIENCE__paper_reading.md)
- Catalog archive: `../../data/catalogs/ROSS2019_SCIENCE/raw/ROSS2019_SCIENCE__catalog_qtm.tar.gz`
- Catalog summary: [`../../data/catalogs/ROSS2019_SCIENCE/README.md`](../../data/catalogs/ROSS2019_SCIENCE/README.md)
- Supplementary Materials DC1: downloaded from CaltechAUTHORS and read directly; see the original-source audit below.

The SCEDC release is the article-associated QTM/GrowClust-format catalog. It
contains both initial-only and successfully relocated rows; use `nbranch > 1`
for the relocated subset. SCEDC warns that the Mw 7.1 mainshock depth is poorly
constrained and recommends the SCSN hypocenter for that event.
- Structured extraction: [`parsed/extraction/ROSS2019_SCIENCE__extraction.json`](parsed/extraction/ROSS2019_SCIENCE__extraction.json).

## Original-source audit — 2026-09-25

- `supplement/ROSS2019_SCIENCE__supplement_DC1.pdf`: 7,657,987 bytes; SHA-256 `a88f3b53ec14e6ef1a3ec5d52530fbfb67a48b6922a810eaa854d5df26267a46`. Source: https://authors.library.caltech.edu/records/3x9hs-fzr27.

Official MD5 `50a84ce87d19cbbf47985eddc1720b04` matches the downloaded 35-page PDF. Physical PDF page 2 contains catalog methods; subevent-inversion station counts on page 3 and the elastic layers in Table S1 belong to other analyses and must not be assigned to the QTM input. Exact station IDs and continuous coverage remain unresolved.

Large original PDFs/ZIPs remain local and ignored by Git; this record tracks their source and checksums.
