#!/bin/bash
# factor-base size sweep at fixed instance (seeds of registry-ext): arms B0,B3,L2,M3n,L3; R=4, 24 targets
cd "$(dirname "$0")"
export AUDIT_ARMS=B0,B3,L2,M3n,L3
for spec in "24 492354324577 128 180 256 360 512" "28 614611668204 322 450 645 900 1290" "32 575604615030 812 1140 1625 2280 3250"; do
  set -- $spec; b=$1; seed=$2; shift 2
  for size in "$@"; do
    AUDIT_INST="{\"$b\":[$size,$seed]}" python3 audit.py run sweep/s$size-b$b 4 24 && python3 audit.py an sweep/s$size-b$b > /dev/null
  done
done
