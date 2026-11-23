#!/bin/bash
# usage: run_cells.sh OUTDIR "p arm seeds..." ...   arm = A | B ; one JSON per (p, arm, seed)
# Single-threaded, 6 GiB address-space limit (kill-on-OOM), shared host.
B=/home/user/wt/harvester-k3-scale/suite/target/release/examples/gaudry_cubic_bench
out=$1; shift; mkdir -p "$out"
ulimit -v 6291456
for cell in "$@"; do
  set -- $cell; p=$1; arm=$2; shift 2
  for s in "$@"; do
    f="$out/p${p}_${arm}_s${s}.json"; [ -s "$f" ] && continue
    if [ "$arm" = A ]; then h="--max-lp 2"; else h="--harvester cycles --max-lp 3"; fi
    t0=$(date +%s)
    RAYON_NUM_THREADS=1 $B --p $p --seed $s --groebner --lp-rule --sparse-la $h --json "$f.tmp" > "$f.log" 2>&1
    rc=$?; echo "$p $arm $s rc=$rc wall=$(( $(date +%s)-t0 ))s" >> "$out/progress.log"
    [ $rc -eq 0 ] && mv "$f.tmp" "$f"
  done
done
