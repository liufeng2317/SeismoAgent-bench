# Chamberlain et al. (2021) workflow files

From the authors' workflow repository calum-chamberlain/kaikoura-aftershocks,
release 0.2 (Zenodo 10.5281/zenodo.5047794; commit ec0ae1f),
`Scripts/Workflow/`, downloaded 2026-10-23 from raw.githubusercontent.com:

- `vzmodel.txt` (SHA-256 119c00887b212cc7011a6dd842a8b2e2c053d6fb05d2a5da361b25e59cabc50d): the average 1-D model the paper uses for
  GrowClust ("an average 1D velocity model extracted from the NZ3D velocity
  model (between 72–110 km in X and −100–80 km in Y ...)"). Columns: depth
  below sea level (km), Vp, Vs (km/s), one row per NZ3D depth node.
- `make_1d_vmodel.py`: the extraction script (mean Vp/Vs per depth node of
  NZ3D 2.2, Zenodo 3779523, over that X/Y box) — provenance only, not run here.
- `Kaik_1d.vmodel`: a P-only model also in the repository; not the
  documented GrowClust model and not used.

Registered as `chamberlain2021_nz3d_avg_1d` in `data/models/velocity_models.json`.
