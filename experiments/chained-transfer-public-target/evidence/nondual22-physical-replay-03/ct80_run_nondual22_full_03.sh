#!/usr/bin/env bash
set -u
export PATH="$HOME/.cargo/bin:$HOME/.elan/bin:$PATH"
export RUSTUP_TOOLCHAIN=1.99.1
layout=/workspace/scratch/ct80-nondual22-layout-03
out=/workspace/scratch/ct80-nondual22-full-03
[[ ! -e $out && ! -e ${out}-build-cache ]] || exit 2
[[ $(git rev-parse HEAD) == b4e3543018ddc5ed70a34ee17280f23b8848484c ]] || exit 2
[[ -z $(git status --porcelain) ]] || exit 2
bash scripts/checkpoint.sh gate > /workspace/scratch/ct80-nondual22-immediate-gate-03.txt 2>&1
status=$?
printf '%s\n' "$status" > /workspace/scratch/ct80-nondual22-immediate-gate-03.exit
[[ $status == 0 ]] || exit "$status"
timeout 6000 bash "$layout/cryptanalysis/experiments/chained-transfer-public-target/ci_nondual_preflight/check.sh" "$layout/crypto" "$out"
status=$?
printf '%s\n' "$status" > /workspace/scratch/ct80-nondual22-full-caller-03.exit
exit "$status"
