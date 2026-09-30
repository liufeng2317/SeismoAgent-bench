#!/usr/bin/env bash
# Add the six locally absent Liu-window stations with explicit sensor families.
set -uo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
status=0
bash "$SCRIPT_DIR/run_download.sh" \
  --stations CI.EDW2,CI.FUR,CI.HYS,CI.LDR,CI.SPG2 \
  --channels HH --locations=-- "$@" || status=$?
# APL acceleration channels are a separate input family, not synthetic HH components.
bash "$SCRIPT_DIR/run_download.sh" \
  --stations CI.APL --channels HN --locations=-- \
  --providers SCEDC_CLOUD,SCEDC,EARTHSCOPE "$@" || status=$?
exit "$status"
