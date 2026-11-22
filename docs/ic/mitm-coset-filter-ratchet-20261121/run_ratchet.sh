#!/bin/bash
# Frozen run script for PROTOCOL.md.  Run from the cryptanalysis repository root:
#   BENCHREC=benchmarks/records/<id>.json WATCH="<memory/wall watchdog>" \
#     bash docs/ic/mitm-coset-filter-ratchet-20261121/run_ratchet.sh [cell-id ...]
# Every arm is one process, run under `tools/benchrec.py run` (so the record names
# the command, host and wall time), and writes one raw JSON report.  WATCH defaults
# to `timeout 1200`; a kill or timeout is a resource limit, not a negative result.
set -u
REC=${BENCHREC:?set BENCHREC to the open bench.record/v1 file}
BIN=${CA_IC:-suite/target/release/ca-ic}
RAW=${RAW:-benchmarks/20261121-mitm-coset-filter-ratchet/raw}
WATCH=${WATCH:-timeout 1200}
SEED=20261121          # fresh: not the registry's phase seeds 123145648762 / 20261102 / 20261104
REPEATS=8
RHO=8                  # matched-rho runs, baseline arm only (the lead arm shares the instance)
mkdir -p "$RAW"
# id | instance flag | size | factor base | baseline oracle | lead oracle
CELLS=(
 "c2-19|--char2-degree|19|binary-subspace:dimension=6|mitm|mitm:coset_filter=1"
 "c2-21|--char2-degree|21|binary-subspace:dimension=7|mitm|mitm:coset_filter=1"
 "c2-23|--char2-degree|23|binary-subspace:dimension=7|mitm|mitm:coset_filter=1"
 "c2-25|--char2-degree|25|binary-subspace:dimension=8|mitm|mitm:coset_filter=1"
 "c2-27|--char2-degree|27|binary-subspace:dimension=9|mitm|mitm:coset_filter=1"
 "c2-29|--char2-degree|29|binary-subspace:dimension=9|mitm|mitm:coset_filter=1"
 "k-23|--koblitz-degree|23|koblitz-orbit:divisor=0;1|mitm-frobenius|mitm-frobenius:coset_filter=1"
 "k-31|--koblitz-degree|31|koblitz-orbit:divisor=0;1;2|mitm-frobenius|mitm-frobenius:coset_filter=1"
 "k-43|--koblitz-degree|43|koblitz-orbit:divisor=1|mitm-frobenius|mitm-frobenius:coset_filter=1"
 "ctl-prime16|--bits|16|prime-abscissa:size=40|mitm|mitm:coset_filter=1"
 "ctl-aa-c2-19|--char2-degree|19|binary-subspace:dimension=6|mitm|mitm"
)
want=("$@")
for cell in "${CELLS[@]}"; do
  IFS='|' read -r id flag deg fb base lead <<<"$cell"
  if [ ${#want[@]} -gt 0 ] && [[ ! " ${want[*]} " =~ " $id " ]]; then continue; fi
  for arm in baseline lead; do
    o=$base; rho=$RHO
    if [ $arm = lead ]; then o=$lead; rho=0; fi
    python3 tools/benchrec.py run "$REC" -- $WATCH "$BIN" bench "$flag" "$deg" \
      --factor-base "$fb" --oracle "$o" --repeats $REPEATS --seed $SEED \
      --max-trials 8000000 --max-cofactor 8 --solver-budget-seconds 300 \
      --rho-runs $rho --json --out "$RAW/$id-$arm.json"
    echo "$id $arm exit=$?"
  done
done
