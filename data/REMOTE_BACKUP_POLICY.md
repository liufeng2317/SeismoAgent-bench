# Remote data backup policy

The GitHub repository contains the small and medium-sized canonical catalog
products needed to inspect and reproduce the benchmark setup. Source papers,
supplements, raw archives, MinerU bundles, and machine-scale phase-arrival
tables remain local or are retrieved from their authoritative release pages.

## Stored in GitHub

- canonical research catalogs smaller than GitHub's 100 MB single-file limit;
- official full and benchmark operational snapshots;
- catalog README files, schemas, and provenance metadata;
- small auxiliary tables required to understand a reference product.

## Not stored in ordinary Git

- `.env`, API keys, proxy credentials, and runtime logs;
- source PDFs and publisher supplements;
- MinerU ZIPs, duplicated PDFs, model caches, and extracted images;
- raw correlation-phase tables and waveform archives;
- any single file larger than 100 MB.

Files excluded from GitHub remain recoverable through the links and provenance
records in `REFERENCES_MANIFEST.md` and the catalog README files. If Git LFS or
a research data repository is enabled later, the excluded files can be added as
a separate data release without changing the source/catalog identifiers.
