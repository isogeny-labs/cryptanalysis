#!/bin/bash
# lower sizes to bracket the baseline's S-optimum (amendment 2, after the first size sweep showed the baseline optimum below 2^(b/3))
cd "$(dirname "$0")"
export AUDIT_ARMS=B0,B3,L2,M3n,L3
for spec in "24 492354324577 45 64 90" "28 614611668204 114 160 226" "32 575604615030 287 405 570"; do
  set -- $spec; b=$1; seed=$2; shift 2
  for size in "$@"; do
    AUDIT_INST="{\"$b\":[$size,$seed]}" python3 audit.py run sweep/s$size-b$b 4 24 && python3 audit.py an sweep/s$size-b$b > /dev/null
  done
done
