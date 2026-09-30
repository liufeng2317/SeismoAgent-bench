# QuakeFlow (GJI, ggac355)

## Local files

- `paper/QUAKEFLOW_GJI_GGAC355__paper.pdf` — Zhu et al., *QuakeFlow: a scalable machine-learning-based earthquake monitoring workflow with cloud computing*, Geophysical Journal International, DOI [10.1093/gji/ggac355](https://doi.org/10.1093/gji/ggac355).
- `paper/QUAKEFLOW_GJI_GGAC355__evaluation.pdf` — the accompanying catalog-evaluation document supplied locally. Its catalog-evaluation material should be treated as methodological context until its bibliographic metadata is verified.
- [`parsed/paper/QUAKEFLOW_GJI_GGAC355__paper_reading.md`](parsed/paper/QUAKEFLOW_GJI_GGAC355__paper_reading.md) — separates the peer-reviewed workflow claims from the evaluation slides and records the Hawaii catalog-availability audit.

## Catalog availability audit

The GJI paper states that the waveform data and earthquake catalogues used in the study come from the Puerto Rico Seismic Network, USGS networks, and the Hawaiian Volcano Observatory Network. It archives the workflow/code (Zenodo [10.5281/zenodo.7023970](https://doi.org/10.5281/zenodo.7023970); source repository [AI4EPS/QuakeFlow](https://github.com/AI4EPS/QuakeFlow)), but does not cite a dedicated DOI or stable downloadable file for the Hawaii QuakeFlow-generated event catalog.

Therefore this reference is currently **paper/code-ready but catalog-missing**. The existing HVO/USGS, Shelly, Wei, Matoza, and Lengliné files in this case must not be relabeled as QuakeFlow output. A QuakeFlow catalog can be added later only when an original output file or a reproducible workflow run with frozen configuration and time/space window is available.

## Useful baseline links

- [GJI article](https://academic.oup.com/gji/article/232/1/684/6694250)
- [arXiv preprint](https://arxiv.org/abs/2208.14564)
- [QuakeFlow source repository](https://github.com/AI4EPS/QuakeFlow)
- [USGS ComCat catalogs](https://earthquake.usgs.gov/data/comcat/catalog/), including the HVO (`HV`) network
- Structured extraction: [`parsed/extraction/QUAKEFLOW_GJI_GGAC355__extraction.json`](parsed/extraction/QUAKEFLOW_GJI_GGAC355__extraction.json).
