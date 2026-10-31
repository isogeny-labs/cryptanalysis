#!/bin/sh
# Frozen driver (PROTOCOL.md). From this directory, two concurrent processes under nice -n 10:
#   ./run_all.sh p1 j1728:40:4000,j0:38:4000,j1728:34:4000,j0:36:4000,j1728:32:1000
#   ./run_all.sh p2 j0:40:4000,j1728:38:4000,j1728:36:4000,j0:34:4000,j0:32:1000
# Needs build trees $BUILDS/b-<arm>/libcryptanalysis.so for main cand capid r8 (PROTOCOL.md).
# Controls: capid (identity) on curves 0..CTRL_ID-1 of every cell; r8 (positive) on curves 0..CTRL_R8-1 of the 34- and 40-bit cells;
# the negation-map rho on main's rows for curves 0..RHO_N-1 of every cell.
set -e
part=$1; cells=$2; B=${BUILDS:-..}
ID=${CTRL_ID:-100}; R8=${CTRL_R8:-300}; RHO=${RHO_N:-150}
for arm in main cand; do
  extra=""; [ $arm = main ] && extra="--rho $RHO"
  CRYPTANALYSIS_LIB=$B/b-$arm/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm $arm --cells "$cells" --out rows_${arm}_$part.jsonl $extra
done
cid=$(for c in $(echo "$cells" | tr , ' '); do n=${c##*:}; [ "$n" -gt "$ID" ] && n=$ID; echo "${c%:*}:$n"; done | paste -sd, -)
c8=$(for c in $(echo "$cells" | tr , ' '); do case $c in *:34:*|*:40:*) echo "${c%:*}:$R8";; esac; done | paste -sd, -)
CRYPTANALYSIS_LIB=$B/b-capid/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm capid --cells "$cid" --out rows_capid_$part.jsonl
[ -n "$c8" ] && CRYPTANALYSIS_LIB=$B/b-r8/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm r8 --cells "$c8" --out rows_r8_$part.jsonl
true
