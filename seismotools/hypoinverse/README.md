# HypoInverse

HypoInverse (Klein 2002, USGS Open-File Report 02-171, version 1.40 of 2014)
is the linearised (Geiger) earthquake locator used by the USGS/ANSS regional
networks — the locations in ComCat for most U.S. networks come from it. It
iterates on travel-time residuals with distance and residual weighting, so it
is a natural counterpart to NonLinLoc's probabilistic grid search.

```text
hypoinverse/
├── source/upstream/      # hyp1.40 Fortran source (USGS) — see source/README.md
├── runtime/bin/hyp1.40   # built locally with gfortran (not committed)
├── interface/            # run.py and its contract (interface/README.md)
├── examples/smoke/       # synthetic known-answer run
└── metadata.json
```

```bash
python seismotools/support/build_native.py --tool hypoinverse
python seismotools/hypoinverse/interface/run.py --arrivals arrivals.csv --stations stations.csv \
  --velocity-model model.txt --output-dir OUT [--config config.json]
```

Inputs and outputs match the NonLinLoc catalog locator
(`seismotools/nonlinloc/interface/locate.py`). Limits to know: layer models
cannot hold low-velocity zones (`lvz_policy`), arrival times are rounded to
0.01 s. Since interface version 2 the models are CRE (stations at their
elevations, model depth 0 at `reference_elevation_km`, as in NonLinLoc);
`model_type` CRH restores version 1, which ignores station elevations. Use the project Python
environment.

Validation (`support/tools_usage_validation/validate_hypoinverse.py`): the
gfortran build reproduces the upstream `testone` summary and archive exactly;
synthetic known hypocentres in both hemispheres within 0.03 km (epicentre),
0.12 km (depth) and 0.013 s; on 50 real events it agrees with NonLinLoc
to 0.24 km (median epicentre) and 0.44 km (median |Δdepth|), with a
lower RMS (0.06 s) from HypoInverse's distance and residual weighting.
Manual: https://pubs.usgs.gov/publication/ofr02171 (also `doc/hyp1.40.pdf` in
the archive).
