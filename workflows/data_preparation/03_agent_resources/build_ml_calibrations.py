#!/usr/bin/env python3
"""Build data/agent_resource/magnitude/calibrations.json from the parsed magnitude standards.

Sources (data/agent_resource/magnitude_standards/; MinerU Markdown in parsed/<name>__mineru.md):
- IASPEI standard ML: NMSOP-2 IS 3.3 eq. (1) and DS 3.1 eq. (2).
- Richter (1958) -logA0 table: DS 3.1 Table 1 (parsed table).
- Regional -logA0 functions: DS 3.1 Table 2, transcribed below. In the source PDF the formula column
  of the rows from NW Turkey (third formula) to South Australia is set one row above its region (the
  MinerU table shows the same offset). The assignment used here moves those formulas one row down;
  the evidence is recorded per entry and checked by the anchor test (``anchor``): a formula for
  amplitudes in mm on a WA record must give -logA0 = 3 at 100 km (or 2 at 17 km where the 10 mm at
  17 km definition is used), one for amplitudes in nm 3 - 2.682 = 0.318.
- China: GB 17740-2017 eq. (1) and Table A.1 (parsed table), amplitudes in micrometres on DD-1
  short-period simulated records, mean of the two horizontal maxima, epicentral distance.

Expressions use R (hypocentral km), D (epicentral km), T (period s) and ML (a first estimate, for
magnitude-dependent branches); log is log10. Station corrections S are network specific and not given.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STD = ROOT / "data/agent_resource/magnitude_standards"
OUT = ROOT / "data/agent_resource/magnitude/calibrations.json"


def sha(name: str) -> str:
    return hashlib.sha256((STD / name).read_bytes()).hexdigest()


def tables(md: Path) -> list[list[list[str]]]:
    text = md.read_text(encoding="utf-8")
    out = []
    for tb in re.findall(r"<table>.*?</table>", text, re.S):
        rows = [[html.unescape(re.sub("<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
                for r in re.findall(r"<tr>(.*?)</tr>", tb, re.S)]
        out.append(rows)
    return out


def richter_table() -> list[list[float]]:
    t = [t for t in tables(STD / "parsed/DS_3.1_rev1__mineru.md") if t and "Δ (km)" in t[0][0]][0]
    pts = []
    for row in t[1:]:
        for i in range(0, len(row) - 1, 2):
            if row[i] and row[i + 1]:
                pts.append([float(row[i]), float(row[i + 1])])
    return sorted(pts)


def gb_table() -> dict:
    t = [t for t in tables(STD / "parsed/GB+17740-2017__mineru.md") if t and "R" in t[0][1] and "11" in t[0][1]][0]
    cols = {f"R1{i}": [] for i in range(1, 6)}
    for row in t[1:]:
        d = row[0].replace(" ", "").replace("～", "~")
        dist = float(d.split("~")[-1])  # "0~5" -> 5 (the value holds for 0-5 km)
        for i, key in enumerate(cols):
            cols[key].append([dist, float(row[i + 1])])
    return cols


MM_100 = "-logA0(100 km) = 3.0 for amplitudes in mm on a WA record (Richter's definition)"
NM_100 = "-logA0(100 km) = 0.318 for amplitudes in nm (3.0 - 2.682)"
SHIFT = ("DS 3.1 Table 2 sets this formula one row above its region in the PDF (and in the MinerU table); "
         "assignment moved one row down, supported by the anchor test, the unit noted in the Reference column and the component")


def entries() -> list[dict]:
    ds, is33, gb = "DS_3.1_rev1.pdf", "IS_3.3_rev1.pdf", "GB+17740-2017.pdf"
    E = []

    def add(**kw):
        kw.setdefault("station_correction", None)
        kw.setdefault("verification", "transcribed from the source table; checked against the rendered page")
        E.append(kw)

    add(id="iaspei_standard", region="IASPEI standard (attenuation like southern California; recommended where no regional calibration exists)",
        expressions=[{"expr": "1.11*log(R) + 0.00189*R - 2.09", "valid": "R < 1000"}],
        amplitude={"unit": "nm", "instrument": "Wood-Anderson response, static magnification 1 (IS 3.3 Table 1)",
                   "measure": "half peak-to-peak", "components": "each horizontal separately"},
        distance="hypocentral R (km)", anchor={"R": 100, "value": 0.318, "rule": NM_100},
        source={"document": is33, "where": "eq. (1)"})
    add(id="richter_1958_table", region="Richter (1958) classical table (southern California)",
        table={"distance": "epicentral D (km)", "points": richter_table()},
        amplitude={"unit": "mm", "instrument": "classical Wood-Anderson record (oWA, magnification 2800)", "measure": "maximum trace amplitude",
                   "components": "horizontal"},
        distance="epicentral D (km)", anchor={"D": 100, "value": 3.0, "rule": MM_100},
        source={"document": ds, "where": "Table 1"}, verification="parsed table (MinerU), checked against the rendered page")
    add(id="hutton_boore_1987", region="Southern California",
        expressions=[{"expr": "1.110*log(R/100) + 0.00189*(R - 100) + 3.0", "valid": "10 <= R <= 700"}],
        amplitude={"unit": "mm", "instrument": "WA record (oWA)", "measure": "half peak-to-peak", "components": "horizontal"},
        distance="hypocentral R (km)", anchor={"R": 100, "value": 3.0, "rule": MM_100}, source={"document": ds, "where": "Table 2"})
    add(id="uhrhammer_2011_base", region="California (statewide; base term only)",
        expressions=[{"expr": "1.11*log(R) + 0.00189*R + 0.591", "valid": "8 <= R <= 500"}],
        amplitude={"unit": "mm", "instrument": "WA record, new response (nWA) with amplitude in mm", "measure": "half peak-to-peak",
                   "components": "horizontal"},
        distance="hypocentral R (km)", anchor={"R": 100, "value": 3.0, "rule": MM_100},
        station_correction="plus a sixth-order Chebyshev term TP(n)*T(n,z) and station corrections S (DS 3.1 Comment 1.4; Uhrhammer et al. 2011), not included",
        source={"document": ds, "where": "Table 2"})
    for key, name, expr in (("vidal_munguia_1999_baja", "Mexico, Baja California", "1.1319*log(R/100) + 0.0017*(R - 100) + 3.0"),
                            ("vidal_munguia_1999_imperial", "Mexico, Imperial Valley", "1.0134*log(R/100) + 0.0025*(R - 100) + 3.0")):
        add(id=key, region=name, expressions=[{"expr": expr, "valid": "0 < R <= 400"}],
            amplitude={"unit": "mm", "instrument": "WA (csmWA in DS 3.1)", "measure": "half peak-to-peak", "components": "horizontal"},
            distance="hypocentral R (km)", anchor={"R": 100, "value": 3.0, "rule": MM_100}, source={"document": ds, "where": "Table 2"})
    add(id="pechmann_2007_utah", region="US Intermountain Belt (Utah)", table_ref="richter_1958_table",
        amplitude={"unit": "mm", "instrument": "WA record (oWA)", "measure": "maximum trace amplitude", "components": "arithmetic mean of the two horizontals"},
        distance="epicentral D (km), D <= 600", anchor={"D": 100, "value": 3.0, "rule": MM_100},
        station_correction="station corrections S (Pechmann et al. 2007), not included",
        source={"document": ds, "where": "Table 2"})
    add(id="kim_1998_eastern_north_america", region="Eastern North America",
        expressions=[{"expr": "1.55*log(D) - 0.22", "valid": "100 <= D <= 800", "component": "horizontal"},
                     {"expr": "1.45*log(D) + 0.11", "valid": "100 <= D <= 800", "component": "vertical"}],
        amplitude={"unit": "mm", "instrument": "WA record (oWA)", "measure": "half peak-to-peak", "components": "horizontal or vertical (separate expressions)"},
        distance="epicentral D (km)", anchor={"D": 100, "value": 3.0, "rule": MM_100, "tolerance": 0.15},
        source={"document": ds, "where": "Table 2"})
    add(id="baumbach_2003_nw_turkey", region="NW Turkey",
        expressions=[{"expr": "log(R/17) + 0.00960*(R - 17) + 2", "valid": "5 <= R <= 62"},
                     {"expr": "log(R/62) + 0.00960*(R - 62) + 2.95", "valid": "62 <= R <= 110"}],
        amplitude={"unit": "mm", "instrument": "WA record (oWA)", "measure": "half peak-to-peak", "components": "horizontal"},
        distance="hypocentral R (km)", anchor={"R": 17, "value": 2.0, "rule": "ML 3 = 10 mm at 17 km (DS 3.1 Comment 1.2)"},
        station_correction="minus station corrections S (Baumbach et al. 2003), not included",
        source={"document": ds, "where": "Table 2"})
    add(id="kiratzi_papazachos_1984_greece", region="Greece",
        expressions=[{"expr": "1.58*log(R/100) + 3.0", "valid": "ML <= 3.7"}, {"expr": "2.00*log(R/100) + 3.0", "valid": "ML > 3.7"}],
        amplitude={"unit": "mm", "instrument": "WA record (oWA)", "measure": "half peak-to-peak", "components": "horizontal"},
        distance="hypocentral R (km); DS 3.1 range 100 <= D <= 800", anchor={"R": 100, "value": 3.0, "rule": MM_100},
        source={"document": ds, "where": "Table 2"},
        verification="the ML <= 3.7 branch is printed in the NW Turkey row; " + SHIFT)
    for key, region, expr, comp, rng, unit, ref in (
            ("muco_minga_1991_albania", "Albania", "1.6627*log(D) + 0.0008*D - 0.433", "horizontal", "10 <= D <= 600", "mm", "Muco & Minga (1991); oWA"),
            ("wahlstrom_strauch_1984_central_europe", "Central Europe", "0.83*log(R) + (0.0017/T)*(R - 100) + 1.41", "vertical", "100 <= D <= 650", "mm",
             "Wahlström & Strauch (1984); oWA; T = period of the maximum (s)"),
            ("stange_2006_sw_germany", "SW Germany (Baden-Württemberg)", "1.11*log(R) + 0.95*R/1000 + 0.69", "vertical", "10 < R < 1000", "mm", "Stange (2006); oWA"),
            ("alsaker_1991_norway", "Norway / Fennoscandia", "0.91*log(R) + 0.00087*R + 1.010", "vertical", "0 < R <= 1500", "mm",
             "Alsaker et al. (1991); new WA response yet amplitude in mm"),
            ("langston_1998_tanzania", "Tanzania", "0.776*log(R/17) + 0.000902*(R - 17) + 2.0", "horizontal", "0 < R <= 1000", "mm",
             "Langston et al. (1998); WA version uncertain in DS 3.1 (?oWA?); ML 3 = 10 mm at 17 km"),
            ("saunders_2011_south_africa", "South Africa", "1.075*log(R) + 0.00061*R - 1.89", "vertical", "0 < R < 1000", "nm",
             "Saunders et al. (2011) (spelt Sauder in DS 3.1); new WA response with amplitude in nm"),
            ("greenhalgh_singh_1986_south_australia", "South Australia", "1.10*log(D) + 0.0013*D + 0.7", "vertical", "40 < D < 700", "mm",
             "Greenhalgh & Singh (1986); oWA")):
        anchor = ({"R": 17, "value": 2.0, "rule": "ML 3 = 10 mm at 17 km (DS 3.1 Comment 1.2)"} if "R/17" in expr else
                  {("R" if "R" in expr else "D"): 100, "value": 0.318 if unit == "nm" else 3.0, "rule": NM_100 if unit == "nm" else MM_100,
                   **({"T": 1.0} if "T" in expr else {})})
        add(id=key, region=region, expressions=[{"expr": expr, "valid": rng}],
            amplitude={"unit": unit, "instrument": ref, "measure": "half peak-to-peak", "components": comp},
            distance="hypocentral R (km)" if "R" in expr else "epicentral D (km)", anchor=anchor,
            station_correction="plus station corrections S, not included" if key.startswith("saunders") else None,
            source={"document": ds, "where": "Table 2"}, verification=SHIFT)
    gbt = gb_table()
    regions = {"R11": "Heilongjiang, Jilin, Liaoning, Inner Mongolia, Beijing, Tianjin, Hebei, Shanxi, Shandong, Henan, Ningxia, Shaanxi",
               "R12": "Fujian, Guangdong, Guangxi, Hainan, Jiangsu, Shanghai, Zhejiang, Jiangxi, Hunan, Hubei, Anhui",
               "R13": "Yunnan, Sichuan, Chongqing, Guizhou", "R14": "Qinghai, Tibet, Gansu", "R15": "Xinjiang"}
    for key, pts in gbt.items():
        add(id=f"gb17740_2017_{key.lower()}", region=f"China, {regions[key]}", table={"distance": "epicentral D (km)", "points": pts},
            amplitude={"unit": "micrometre", "instrument": "DD-1 short-period seismograph simulation (GB 17740-2017 Annex B.1)",
                       "measure": "maximum S (or Lg) amplitude", "components": "mean of the N and E maxima, A = (AN + AE)/2"},
            distance="epicentral D (km)", formula="ML = lg(A) + R(D)",
            source={"document": gb, "where": "eq. (1), Table A.1"}, verification="parsed table (MinerU), checked against the rendered page")
    return E


def main() -> int:
    docs = sorted({e["source"]["document"] for e in entries()})
    lib = {"description": "Local-magnitude calibration functions -logA0 from standard compilations. ML = log10(A) + (-logA0) [+ station "
                          "correction], with A in the unit and on the instrument stated per entry. Expressions: R hypocentral km, D epicentral "
                          "km, T period s, ML a first estimate for magnitude-dependent branches; log = log10.",
           "sources": {d: {"sha256": sha(d)} for d in docs}, "entries": entries()}
    OUT.write_text(json.dumps(lib, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{OUT}: {len(lib['entries'])} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
