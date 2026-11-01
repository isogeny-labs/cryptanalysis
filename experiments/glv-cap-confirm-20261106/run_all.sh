#!/bin/sh
# Frozen driver (PROTOCOL.md). Two concurrent processes under nice:
#   run_all.sh p1 j1728      run_all.sh p2 j0
# Needs $BUILDS/b-main/libcryptanalysis.so (main 1ee4f47) and $BUILDS/b-cand/libcryptanalysis.so (candidate commit), CA_BINDINGS.
set -e
part=$1; fam=$2; B=${BUILDS:-..}; N=${GRID_N:-1600}; I=${IDENT_N:-80}; RHO=${RHO_N:-60}
cells=""; for b in 40 41 42 43; do cells="$cells,$fam:$b:$N"; done; cells=${cells#,}
idc="$fam:38:$I,$fam:39:$I"
CRYPTANALYSIS_LIB=$B/b-main/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm main --cells "$cells" --rho $RHO --out rows_main_$part.jsonl
CRYPTANALYSIS_LIB=$B/b-cand/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm cand --cells "$cells" --out rows_cand_$part.jsonl
CRYPTANALYSIS_LIB=$B/b-main/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm mainid --cells "$idc" --out rows_mainid_$part.jsonl
CRYPTANALYSIS_LIB=$B/b-cand/libcryptanalysis.so nice -n 10 python3 run.py $RUNARGS --arm candid --cells "$idc" --out rows_candid_$part.jsonl
