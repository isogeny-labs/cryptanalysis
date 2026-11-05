#!/usr/bin/env bash
# Runs on the rented pod from the repository root: CPU identity, then the
# descent phase profile and the n = 53 perfbench kernels with the AVX-512
# kernels on and off (KIC_SCAN_SIMD=0), interleaved, in the same binaries.
set -euo pipefail
OUT=experiments/descent-phases-vpclmul-20261105/data
mkdir -p "$OUT"
lscpu > "$OUT/lscpu.txt"
grep -m1 '^flags' /proc/cpuinfo | tr ' ' '\n' | grep -E 'avx512|pclmul|gfni' | tr '\n' ' ' > "$OUT/cpu-flags.txt"
nproc > "$OUT/nproc.txt"
cd suite
cargo build --release --example descent_phases --example perfbench 2>&1 | tail -3
BIN=target/release/examples
sha256sum "$BIN/descent_phases" "$BIN/perfbench" > "../$OUT/binaries.sha256"
CPU=$(( $(nproc) - 1 ))
: > "../$OUT/phases.jsonl"
for r in 1 2 3; do
  for mode in simd scalar; do
    if [ "$mode" = scalar ]; then export KIC_SCAN_SIMD=0; else unset KIC_SCAN_SIMD; fi
    taskset -c "$CPU" "$BIN/descent_phases" --walks 512 --targets 64 2>/dev/null \
      | sed "s/^{/{\"mode\":\"$mode\",\"round\":$r,/" >> "../$OUT/phases.jsonl"
  done
done
unset KIC_SCAN_SIMD
: > "../$OUT/perfbench.jsonl"
for r in 1 2 3; do
  for mode in simd scalar; do
    if [ "$mode" = scalar ]; then export KIC_SCAN_SIMD=0; else unset KIC_SCAN_SIMD; fi
    RAYON_NUM_THREADS=1 taskset -c "$CPU" "$BIN/perfbench" run \
      --filter field_ec/koblitz_n53_add_many_lazy_64x2k,relation/koblitz_descent_k0n53_m2_x4,relation/koblitz_collect_k0n53_w477_u1024 \
      --samples 5 2>/dev/null | sed "s/^{/{\"mode\":\"$mode\",\"round\":$r,/" >> "../$OUT/perfbench.jsonl"
  done
done
echo done
