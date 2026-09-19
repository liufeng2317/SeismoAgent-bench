# Lanza et al. (2019) QuakeML relocation catalog

- `source_ref`: `LANZA2019_GL082780`
- DOI: [10.1029/2019GL082780](https://doi.org/10.1029/2019GL082780)
- Product: AGU/Wiley Data Set S1, relocated hypocenters and P/S arrival picks
  in QuakeML format.
- Core file: `raw/grl59060-sup-0003-ds01.xml`
- SHA-256: `c87a16de4fb28be7cd873b03e93b3d410c6e2237d7ed443affbe798670fbd478`
- Local event objects: 2,655 (2,012 with HypoDD origins and 643 SIMUL-only)
- Local picks: 110,810 P + 72,149 S = 182,959 pick elements
- Station codes represented in picks: 81

The XML was downloaded as part of the paper's supporting-information bundle and
is staged here separately from the narrative SI (`references/LANZA2019_GL082780/supplement/`).
The original filename is preserved under `raw/`; the source is not rewritten or
silently normalized. The article reports 2,013 final clustered HypoDD events,
whereas this local XML contains 2,012 HypoDD origin objects; see the catalog
summary for the discrepancy and for the frozen-window masks.

