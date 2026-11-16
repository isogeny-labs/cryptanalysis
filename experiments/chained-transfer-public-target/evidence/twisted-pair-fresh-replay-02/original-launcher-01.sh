#!/usr/bin/env bash
set -u
cd /workspace/cryptanalysis || exit 2
out=/workspace/scratch/ct81-twisted23-physical-01
[[ ! -e $out && $(git rev-parse HEAD) == 2b970797c67a5c401a5bbe0d16e6de464c93bb2d && -z $(git status --porcelain) ]] || exit 2
date -u +%FT%TZ > /workspace/scratch/ct81-twisted23-physical-01.start
bash scripts/checkpoint.sh gate > /workspace/scratch/ct81-twisted23-physical-01.immediate-gate.txt 2>&1
gate=$?
printf '%s\n' "$gate" > /workspace/scratch/ct81-twisted23-physical-01.immediate-gate.exit
[[ $gate == 0 ]] || exit "$gate"
timeout 3600 bash /workspace/scratch/ct81-twisted23-layout-01/cryptanalysis/experiments/chained-transfer-public-target/ci_twisted_pair/check.sh /workspace/scratch/ct81-twisted23-layout-01/crypto "$out"
status=$?
printf '%s\n' "$status" > /workspace/scratch/ct81-twisted23-physical-01.supervisor.exit
date -u +%FT%TZ > /workspace/scratch/ct81-twisted23-physical-01.finish
exit "$status"
