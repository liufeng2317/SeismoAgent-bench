#!/usr/bin/env bash
# Known-answer test: VELEST's own example (Calaveras, central California) must reproduce the reference
# hypocenters and station corrections shipped with the source (differences of one unit in the last digit allowed).
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL="$(cd "$HERE/../.." && pwd)"
UP="$TOOL/runtime/build/upstream"
[ -x "$TOOL/runtime/bin/velest" ] && [ -d "$UP" ] || { echo "build first: python seismotools/support/build_native.py --tool velest"; exit 2; }
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
cp "$UP"/velest.cmn "$UP"/ca1d11.mod "$UP"/ca1vel.sta "$UP"/calarea7.cnv "$W"/
(cd "$W" && "$TOOL/runtime/bin/velest" > run.log 2>&1)
python3 - "$UP" "$W" <<'PY'
import sys, re
up, w = sys.argv[1:]
def nums(path):
    return [float(x) for x in re.findall(r"-?\d+\.\d+", open(path).read())]
for ref, new in (("VELMOD11area7.CNV", "VELMOD11area7.CNV"), ("mod11area7sta.OUT", "mod11area7sta.OUT")):
    a, b = nums(f"{up}/{ref}"), nums(f"{w}/{new}")
    bad = [(x, y) for x, y in zip(a, b) if abs(x - y) > 0.011]
    assert len(a) == len(b) and not bad, (ref, len(a), len(b), bad[:5])
    print(f"ok {ref}: {len(a)} values agree within 0.01")
print("PASS")
PY
