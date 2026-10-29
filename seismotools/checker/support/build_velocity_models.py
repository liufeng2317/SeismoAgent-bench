#!/usr/bin/env python3
"""Build the checker's compact global velocity models from the published archives.

Inputs (downloaded once, kept outside git; see runtime/velocity_models/SOURCES.md):
- crust1.0.tar.gz  (Laske et al., 2013), https://igppweb.ucsd.edu/~gabi/crust1/crust1.0.tar.gz
- litho1.0.tar.gz  (Pasyanos et al., 2014), https://igppweb.ucsd.edu/~gabi/litho1/litho1.0.tar.gz

Outputs (tracked):
- runtime/velocity_models/crust1.npz: top elevation (km, positive up), Vp, Vs (km/s) of the 9 CRUST1.0
  layers (water, ice, 3 sediment, 3 crust, upper mantle) on the 1°×1° grid, cell centres 89.5N…89.5S,
  179.5W…179.5E.
- runtime/velocity_models/litho1.npz: per LITHO1.0 node (geodetic latitude, longitude) the top depth
  (km below sea level), Vp and Vs (vertical, km/s) of WATER, SEDS1, SEDS2, CRUST1, CRUST2, CRUST3, LID
  and ASTHENO.
- runtime/velocity_models/sources.json: archive URLs, sizes and SHA-256 of the inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parents[1] / "runtime/velocity_models"
URLS = {"crust1": "https://igppweb.ucsd.edu/~gabi/crust1/crust1.0.tar.gz",
        "litho1": "https://igppweb.ucsd.edu/~gabi/litho1/litho1.0.tar.gz"}
LITHO_LAYERS = ["WATER", "SEDS1", "SEDS2", "CRUST1", "CRUST2", "CRUST3", "LID", "ASTHENO"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def crust1(archive: Path) -> dict:
    with tarfile.open(archive) as tar:
        def grid(name: str) -> np.ndarray:
            data = np.loadtxt(io.TextIOWrapper(tar.extractfile(name)))
            return data.reshape(180, 360, 9).transpose(2, 0, 1).astype(np.float32)  # (layer, lat, lon)
        return {"top_elev_km": grid("crust1.bnds"), "vp": grid("crust1.vp"), "vs": grid("crust1.vs"),
                "lat": np.arange(89.5, -90, -1.0, dtype=np.float32), "lon": np.arange(-179.5, 180, 1.0, dtype=np.float32)}


def litho1(archive: Path) -> dict:
    with tarfile.open(archive) as tar:
        coords = np.loadtxt(io.TextIOWrapper(tar.extractfile("LITHO1.0/litho_model/Icosahedron_Level7_LatLon_mod.txt")))
        n = len(coords)
        top = np.full((len(LITHO_LAYERS), n), np.nan, np.float32)
        vp, vs = top.copy(), top.copy()
        for i in range(n):
            text = tar.extractfile(f"LITHO1.0/litho_model/node{i + 1}.model").read().decode().splitlines()[1:]
            for line in text:
                parts = line.split()
                name = parts[-1]
                if not name.endswith("-TOP"):
                    continue
                layer = name[:-4]
                if layer in LITHO_LAYERS:
                    k = LITHO_LAYERS.index(layer)
                    top[k, i] = float(parts[0]) / 1000.0  # depth below sea level (km)
                    vp[k, i], vs[k, i] = float(parts[2]) / 1000.0, float(parts[3]) / 1000.0
    return {"lat": coords[:, 1].astype(np.float32), "lon": coords[:, 2].astype(np.float32),
            "top_depth_km": top, "vp": vp, "vs": vs, "layers": np.array(LITHO_LAYERS)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--crust1", type=Path, required=True, help="crust1.0.tar.gz")
    parser.add_argument("--litho1", type=Path, required=True, help="litho1.0.tar.gz")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "crust1.npz", **crust1(args.crust1))
    np.savez_compressed(OUT / "litho1.npz", **litho1(args.litho1))
    sources = {"built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "archives": {k: {"url": URLS[k], "file": p.name, "bytes": p.stat().st_size, "sha256": sha256(p)}
                            for k, p in (("crust1", args.crust1), ("litho1", args.litho1))}}
    (OUT / "sources.json").write_text(json.dumps(sources, indent=1) + "\n")
    print(json.dumps(sources, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
