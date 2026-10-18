#!/usr/bin/env bash
set -u
cd /workspace/cryptanalysis
out=experiments/ideas_gpu_20261018/diagnostics/ingestion-zero
exe="$out/ingest-control-v2"
raw=experiments/ideas_gpu_20261018/remote/run-1
trial(){ name=$1; shift; printf '%q ' "$@" > "$out/$name.command.txt"; printf '\n' >> "$out/$name.command.txt"; "$@" > "$out/$name.stdout" 2> "$out/$name.stderr"; status=$?; printf '%s\n' "$status" > "$out/$name.exit"; }
trial actual "$exe" check "$raw/control.32" "$raw/control.64" 53180 46 8 512
trial extract-zero "$exe" zero-fixture "$raw/control.32" "$raw/control.64" "$out/valid-zero"
trial valid-zero "$exe" check "$out/valid-zero.32" "$out/valid-zero.64" 53180 46 0 0
trial tamper-seed "$exe" tamper-zero-seed "$out/valid-zero.64" "$out/tampered-zero"
trial reject-tampered-zero "$exe" check "$out/tampered-zero.32" "$out/tampered-zero.64" 53180 46 0 0
trial fixture-positive "$exe" fixture "$out/positive"
trial valid-positive "$exe" check "$out/positive.32" "$out/positive.64" 53180 60 8 10000
trial tamper-coordinate "$exe" tamper "$out/positive.64" "$out/tampered-positive.64"
trial reject-tampered-positive "$exe" check "$out/positive.32" "$out/tampered-positive.64" 53180 60 8 10000
