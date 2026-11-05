# Generic velocity models for the checker

Global models only, so the checker stays case-agnostic. They give a range of plausible 1-D models for any region; none is assumed correct for a given case.

| File | Model | Content | Reference |
|---|---|---|---|
| `crust1.npz` | CRUST1.0 | 1°×1° global crust: top elevation (km), Vp, Vs of 9 layers (water, ice, 3 sediment, 3 crust, uppermost mantle) | Laske, G., Masters, G., Ma, Z., Pasyanos, M. (2013), Update on CRUST1.0, EGU General Assembly, EGU2013-2658 |
| `litho1.npz` | LITHO1.0 | 40,962 nodes: top depth (km below sea level), Vp, Vs of water, 2 sediment, 3 crust, lid and asthenosphere layers | Pasyanos, M. E., Masters, T. G., Laske, G., Ma, Z. (2014), LITHO1.0, J. Geophys. Res. 119, 2153–2173, doi:10.1002/2013JB010626 |
| built in (`velocity.py`) | ak135, iasp91, PREM | crust and uppermost mantle of the global 1-D models | Kennett, Engdahl & Buland (1995); Kennett & Engdahl (1991); Dziewonski & Anderson (1981) |

`sources.json` records the archive URLs, sizes and SHA-256. The archives themselves are kept outside git at `/ai4earthafs/liufeng/ScienceDiscovery/SeismoAgentBench/velocity_models/`; rebuild the `.npz` files with `python seismo_checker/support/build_velocity_models.py --crust1 <crust1.0.tar.gz> --litho1 <litho1.0.tar.gz>`.

`catalog_checker/velocity.py` turns them into 1-D models for a region: the CRUST1.0 cell under each station and the event centroid, or the nearest LITHO1.0 node, averaged in slowness against depth below each column's own surface; offshore columns (> 0.2 km of water) are left out when any land column exists.
