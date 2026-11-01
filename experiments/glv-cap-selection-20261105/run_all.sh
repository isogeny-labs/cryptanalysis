#!/bin/sh
# Frozen driver (PROTOCOL.md). Usage (from this directory), two concurrent processes under nice:
#   run_all.sh p1 j1728      run_all.sh p2 j0
# Needs build trees $BUILDS/b-<arm>/libcryptanalysis.so for main r64 r128 r32 r8 and CA_BINDINGS (bindings/python).
set -e
part=$1; fam=$2; B=${BUILDS:-..}; N=${GRID_N:-700}; I=${IDENT_N:-40}; P=${POS_N:-100}
cells=""; for b in 38 39 40 41 42; do cells="$cells,$fam:$b:$N"; done; cells=${cells#,}
for arm in main r64 r128; do
  CRYPTANALYSIS_LIB=$B/b-$arm/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm $arm --cells "$cells" --out rows_${arm}_$part.jsonl
done
CRYPTANALYSIS_LIB=$B/b-r32/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm r32 --cells "$fam:38:$I,$fam:42:$I" --out rows_r32_$part.jsonl
CRYPTANALYSIS_LIB=$B/b-r8/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm r8 --cells "$fam:42:$P" --out rows_r8_$part.jsonl
