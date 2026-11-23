#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cc -O3 -Wall -Wextra -Werror "$here/compare.c" $(pkg-config --cflags --libs flint) -o "$scratch/compare"
echo 'roots,block,planted,hits,product_setup_s,tree_setup_s,gcd_s,evaluation_s'
for depth in 12 15; do
    git -C "$here" show "b32a4dd87:experiments/prime-field-auxiliary-ic/snapshot/algebraic/structure_results/field31_s${depth}/structured_roots.json" |
        python3 -c 'import json,sys; xs=json.load(sys.stdin); assert len(xs)==len(set(xs)); print(*xs,sep="\n")' |
        "$scratch/compare" "$((1 << depth))"
done
