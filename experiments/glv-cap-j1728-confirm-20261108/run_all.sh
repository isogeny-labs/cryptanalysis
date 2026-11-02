#!/bin/sh
# Frozen driver (PROTOCOL.md). Two concurrent processes under nice:   run_all.sh p1     run_all.sh p2
# Needs $BUILDS/b-ref (commit 1ee4f47 unpatched), $BUILDS/b-main (commit 318b27bf unpatched), $BUILDS/b-cand (the candidate commit),
# $BUILDS/b-r8 (1ee4f47 + force-r.patch, -DCA_GLV_FORCE_R=8; positive control only) and CA_BINDINGS.
set -e
part=$1; B=${BUILDS:-..}; N=${GRID_N:-3000}; NJ0=${J0_N:-800}; I=${IDENT_N:-100}; RHO=${RHO_N:-60}; CTRL=${CTRL_N:-200}
prim=""; for b in 40 41 42 43; do prim="$prim,j1728:$b:$N"; done; prim=${prim#,}
j0=""; for b in 40 41 42 43; do j0="$j0,j0:$b:$NJ0"; done; j0=${j0#,}
idc="j0:40:$I,j0:41:$I,j0:42:$I,j0:43:$I,j1728:38:$I,j1728:39:$I"
idm="j1728:40:$I,j1728:41:$I,j1728:42:$I,j1728:43:$I"
run() { arm=$1; build=$2; cells=$3; shift 3; CRYPTANALYSIS_LIB=$B/b-$build/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm $arm --cells "$cells" "$@" --out rows_${arm}_$part.jsonl; }
if [ "$part" = p1 ]; then
  run ref ref "$prim" --rho $RHO
  run refid ref "$idc"
  run r8 r8 "j1728:42:$CTRL"
  run candj0 cand "$j0"
else
  run cand cand "$prim"
  run candid cand "$idc"
  run mainid main "$idm"
  run mainj0 main "$j0" --rho 40
fi
