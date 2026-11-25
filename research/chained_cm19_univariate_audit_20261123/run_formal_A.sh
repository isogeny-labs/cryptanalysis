#!/usr/bin/env bash
# Thin Init-only coefficient proof caller, separate from native audit status.
set -euo pipefail
source_commit=${1:?published source commit}
out=${2:?fresh absolute RAM output directory}
compiler_temp=${3:?fresh absolute RAM compiler temporary directory}
study_dir=$(cd "$(dirname "$0")" && pwd)
repo_dir=$(git -C "$study_dir" rev-parse --show-toplevel)
study_rel=research/chained_cm19_univariate_audit_20261123
export PATH="/home/agent/.cargo/bin:$PATH"
export RAYON_NUM_THREADS=1 CARGO_BUILD_JOBS=1 LEAN_NUM_THREADS=1
export CHECKPOINT_SKIP="Init-only closed coefficient proof build and axioms print, not an experiment; full GitHub source/input checkpoint/readback."
umask 077
mkdir "$out" "$compiler_temp"
export TMPDIR="$compiler_temp"
metadata="$study_dir/custody_metadata_A.py"
finish() {
 local status=$? guard_status=0
 trap - EXIT
 python3 "$metadata" finish "$out" "$status" > "$out/final-guards.stdout" 2> "$out/final-guards.stderr" || guard_status=$?
 if [[ "$status" -ne 0 ]]; then exit "$status"; fi
 exit "$guard_status"
}
trap finish EXIT
cd "$repo_dir"
python3 "$metadata" init "$source_commit" "$out" "$compiler_temp" > "$out/init.stdout" 2> "$out/init.stderr"
python3 "$metadata" pre "$out" > "$out/pre-call.stdout" 2> "$out/pre-call.stderr"
cd "$out/source/$study_rel/formal"
phase() {
 local name=$1 status=0
 shift
 printf '%q ' "$@" > "$out/$name.argv"
 printf '\n' >> "$out/$name.argv"
 ( ulimit -c 0; ulimit -v 2097152; timeout --signal=TERM --kill-after=5s 120s "$@" ) > "$out/$name.stdout" 2> "$out/$name.stderr" || status=$?
 python3 "$metadata" phase "$out" "$name" "$status"
 if [[ "$status" -ne 0 ]]; then return "$status"; fi
}
lean_tool=/home/agent/.elan/toolchains/leanprover--lean4---v4.35.0/bin/lean
phase lean-version "$lean_tool" --version
phase coefficient-leaves "$lean_tool" -o "$out/CoefficientLeavesA.olean" CoefficientLeavesA.lean
