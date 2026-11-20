#!/bin/bash
# Lead (a): descent-algebraic m=4 balanced split, intermediates restricted to span(1..z^(l'-1)),
# l' sweep, with m=2 and m=3 descents on the same instance as controls.
# char2 n=17, binary-subspace dim 6, ic bench default seed, T targets each, sat-cdcl, 30 s budget.
# Usage: split_descent_sweep.sh <ca-ic binary> <out dir> [T]
set -u
B=$1; OUT=$2; T=${3:-30}; mkdir -p "$OUT"
run(){ tag=$1; shift; timeout 2400 "$B" bench --char2-degree 17 --factor-base binary-subspace:dimension=6 "$@" --repeats 1 --rho-runs 0 --max-trials $T --solver-budget-seconds 30 --json > "$OUT/$tag.json" 2> "$OUT/$tag.err"; echo "$tag rc=$?"; }
run m2 --oracle descent-algebraic:m=2 --solver sat-cdcl
run m3 --oracle descent-algebraic:m=3 --solver sat-cdcl
for l in 4 6 8 10 11 12 13; do run m4l$l --oracle descent-algebraic:m=4,inter_dim=$l --solver sat-cdcl; done
