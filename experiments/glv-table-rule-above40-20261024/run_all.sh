#!/bin/sh
# Frozen driver (PROTOCOL.md). Usage (from this directory):
#   run_all.sh p1 50:85,48:170,40:800
#   run_all.sh p2 42:650,44:450,46:300
# Needs build trees $BUILDS/b-<arm>/libcryptanalysis.so for main r64 r128 noesc r8 r32 (PROTOCOL.md).
set -e
part=$1; grid=$2; B=${BUILDS:-..}
ctl=""; for s in $(echo "$grid" | tr , ' '); do case $s in 40:*|42:*) ctl="$ctl,$s";; esac; done
ctl=${ctl#,}
for arm in main r64 r128 noesc; do
  extra=""; [ $arm = main ] && extra="--rho"
  CRYPTANALYSIS_LIB=$B/b-$arm/libcryptanalysis.so nice -n 10 python3 run.py --arm $arm --sizes $grid --out rows_${arm}_$part.jsonl $extra
done
if [ -n "$ctl" ]; then
  for arm in r8 r32; do
    CRYPTANALYSIS_LIB=$B/b-$arm/libcryptanalysis.so nice -n 10 python3 run.py --arm $arm --sizes $ctl --out rows_${arm}_$part.jsonl
  done
fi
