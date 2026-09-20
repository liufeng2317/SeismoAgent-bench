# MATOZA2014_GL059819 — LP summit catalog summary

## Provenance and schema

- Source: Matoza et al. (2014), DOI [10.1002/2014GL059819](https://doi.org/10.1002/2014GL059819).
- Canonical file: `MATOZA2014_GL059819__catalog_lp_summit.txt`.
- Original archive: `raw/LPKSC.zip`; SHA-256 `0b6e452e2daf3bfdf2a14bcf2404cb2e3385dc26cc89b9358ae57e4798a0a140`.
- Canonical file SHA-256: `a7b948486279e37349834705aa103603d3a1738e2e2845c574bfd0f4012f29c5`.
- The archive README defines 17 fields: UTC time, CUSP ID, latitude,
  longitude, depth, magnitude, initial quality, cluster ID/size, horizontal and
  vertical relative errors, and relocation flag.

## Local audit

- 12,290 rows; CUSP IDs are unique; relocation flag `1`: 5,199, flag `0`:
  7,091, matching the archive README and article.
- Time range: 1986-01-02 11:52:25.510 to 2009-03-31 09:42:34.460 UTC.
- Latitude 19.31194–19.50323°, longitude −155.3645–−155.1515°; depth
  −0.505–21.472 km; native CUSP magnitude 0–4.56 (unassigned values are 0).
- Initial location quality codes: A 8,402; B 2,395; C 926; D 566; X 1.
- There are 13 nonzero cluster IDs; cluster sizes range from 10 to 4,323.
- The 2018-05-01–05-09 benchmark window contains **zero** rows. This is
  expected and is the reason this catalog remains auxiliary rather than a
  competing 2018 reference.

## Benchmark role

Use for historical LP/relative-relocation method comparison only. Preserve
relocation flag and error fields; do not merge the 1986–2009 LP population with
Shelly/Wei 2018 products.
