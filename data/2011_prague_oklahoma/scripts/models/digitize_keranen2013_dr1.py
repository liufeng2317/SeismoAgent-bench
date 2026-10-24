#!/usr/bin/env python3
"""Extract the Keranen et al. (2013) Prague 1-D model from Figure DR1 (vector PDF).

Figure DR1 (GSA DR 2013191, page 4) draws the best-fitting model as dashed
step polylines (Vp, Vs) and minimum/maximum models as solid lines. The PDF
content stream is parsed (q/Q, cm, d, m/l/S), the dashed polylines are mapped
to velocity/depth with the axis frame read from the same stream (velocity
ticks 1..7 at x 123.7144..396.7773, depth 0..15 at y 701.374..230.9775), and
the layer tops are the depths of the horizontal segments. The separate
Vp/Vs panel is used as a check: the extracted Vp/Vs values must map its
polyline onto the panel's 1.6/1.8 tick labels. Run with an isolated
interpreter (python -I) on the downloaded file; prints JSON rows.
"""
import json
import re
import sys

import numpy as np
import pypdf

X0, X1, Z0, Z1 = 123.7144, 396.7773, 701.374, 230.9775   # axis frame (page units)


def polylines(path):
    data = pypdf.PdfReader(path).pages[3].get_contents().get_data().decode("latin1")
    tokens = re.findall(r"\((?:[^()\\]|\\.)*\)|\[[^\]]*\]|/[^\s/\[\]()]+|[-+]?\d*\.?\d+|[A-Za-z\*']+", data)
    stack, ctm, dash, args, path, out = [], np.eye(3), False, [], [], []
    for t in tokens:
        if re.fullmatch(r"[-+]?\d*\.?\d+", t) or t[0] in "[(/":
            args.append(float(t) if t[0] not in "[(/" else t)
            continue
        if t == "q":
            stack.append((ctm.copy(), dash))
        elif t == "Q":
            ctm, dash = stack.pop()
        elif t == "cm":
            a, b, c, d, e, f = args[-6:]
            ctm = np.array([[a, b, 0], [c, d, 0], [e, f, 1.0]]) @ ctm
        elif t == "d":
            dash = args[-2].strip("[] ") != ""
        elif t == "m":
            path.append([tuple((np.array([*args[-2:], 1.0]) @ ctm)[:2])])
        elif t == "l":
            path[-1].append(tuple((np.array([*args[-2:], 1.0]) @ ctm)[:2]))
        elif t in ("S", "s"):
            out += [(dash, p) for p in path if len(p) > 2]
            path = []
        elif t in ("n", "f"):
            path = []
        args = []
    return out


def main():
    lines = polylines(sys.argv[1])
    v = lambda x: 1 + (x - X0) / ((X1 - X0) / 6)
    z = lambda y: (Z0 - y) / ((Z0 - Z1) / 15)
    dashed = sorted([p for dash, p in lines if dash], key=lambda p: -min(x for x, _ in p))   # Vp right of Vs
    assert len(dashed) == 2
    steps = []
    for p in dashed:
        pts = [(round(v(x), 3), round(z(y), 3)) for x, y in p]
        steps.append([(pts[i][1], pts[i][0]) for i in range(0, len(pts), 2)])   # (top, velocity) per layer
    vp, vs = steps
    assert [t for t, _ in vp] == [t for t, _ in vs]
    rows = [{"top_of_layer_km": max(0.0, round(t, 2)), "vp_km_s": a, "vs_km_s": b}
            for (t, a), (_, b) in zip(vp, vs)]
    # check against the Vp/Vs panel: linear tick scale from two layers, labels at 1.6 / 1.8
    ratio = [p for dash, p in lines if not dash and min(x for x, _ in p) > 400][0]
    xs = [ratio[i][0] for i in range(0, len(ratio), 2)]
    r = [row["vp_km_s"] / row["vs_km_s"] for row in rows]
    k = (xs[0] - xs[2]) / (r[0] - r[2])
    fit = [xs[2] + k * (x - r[2]) for x in r]
    print(json.dumps({"rows": rows, "vpvs": [round(x, 3) for x in r],
                      "vpvs_panel_max_misfit_pt": round(max(abs(a - b) for a, b in zip(fit, xs)), 2),
                      "vpvs_ticks_x": {"1.6": round(xs[2] + k * (1.6 - r[2]), 1), "1.8": round(xs[2] + k * (1.8 - r[2]), 1)}},
                     indent=2))


if __name__ == "__main__":
    main()
