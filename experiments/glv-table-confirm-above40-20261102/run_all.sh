#!/bin/sh
# Frozen driver (PROTOCOL.md). Usage (from this directory), two concurrent processes:
#   run_all.sh p1 j1728:42:1600,j1728:44:1130,j0:46:800
#   run_all.sh p2 j1728:46:800,j0:42:1600,j0:44:1130
# Needs build trees $BUILDS/b-<arm>/libcryptanalysis.so for main r64 r128 r32 r8 (PROTOCOL.md).
# Controls run only on the 42-bit cells of the part, with CTRL_R32 / CTRL_R8 curves; rho on RHO curves of main.
set -e
part=$1; cells=$2; B=${BUILDS:-..}
R32=${CTRL_R32:-100}; R8=${CTRL_R8:-200}; RHO=${RHO_N:-150}
sub() { # sub <n>: the 42-bit cells of $cells with n curves
  for c in $(echo "$cells" | tr , ' '); do case $c in *:42:*) echo "${c%:*}:$1";; esac; done | paste -sd, -
}
for arm in main r64 r128; do
  extra=""; [ $arm = main ] && extra="--rho $RHO"
  CRYPTANALYSIS_LIB=$B/b-$arm/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm $arm --cells "$cells" --out rows_${arm}_$part.jsonl $extra
done
c32=$(sub "$R32"); c8=$(sub "$R8")
[ -n "$c32" ] && CRYPTANALYSIS_LIB=$B/b-r32/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm r32 --cells "$c32" --out rows_r32_$part.jsonl
[ -n "$c8" ] && CRYPTANALYSIS_LIB=$B/b-r8/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm r8 --cells "$c8" --out rows_r8_$part.jsonl
true
