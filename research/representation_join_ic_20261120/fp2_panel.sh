#!/bin/bash
# fp2 representation panel: mitm (table baseline) vs fp2-weil (Gaudry n=2) vs rep-join, paired by seed.
# Usage: fp2_panel.sh <ca-ic binary> <out dir>
set -u
B=$1; OUT=$2; mkdir -p "$OUT"
for k in 16 20 24 28; do
  for o in mitm fp2-weil "rep-join:m=3" "rep-join:m=4" "rep-join:m=3,filter_bits=4"; do
    t=$(echo "$o" | tr ':=,' '___')
    timeout 1800 "$B" bench --fp2-bits $k --factor-base fp2-subfield --oracle "$o" --repeats 6 --rho-runs 8 --seed 20261120 --json > "$OUT/k${k}_$t.json" 2> "$OUT/k${k}_$t.err"
    echo "k=$k $o rc=$?"
  done
done
