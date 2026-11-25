#!/usr/bin/env bash
# Thin caller for the fixed-certificate regression, never a search or benchmark.
set -euo pipefail
source_commit=${1:?published source commit}
out=${2:?fresh absolute RAM output directory}
compiler_temp=${3:?fresh absolute RAM compiler temporary directory}
study_dir=$(cd "$(dirname "$0")" && pwd)
repo_dir=$(git -C "$study_dir" rev-parse --show-toplevel)
study_rel=research/chained_cm19_univariate_audit_20261123
export PATH="/home/agent/.cargo/bin:$PATH"
export RAYON_NUM_THREADS=1 CARGO_BUILD_JOBS=1
export CHECKPOINT_SKIP="Fixed completed public-certificate unit verification and corruption regression; no experiment search, sampled/held-out workload or benchmark. Exact GitHub source/input readback precedes calls; see CHECKPOINT_CLASSIFICATION_A.md."
unset CLIPPY_ARGS RUSTC_WRAPPER RUSTC_WORKSPACE_WRAPPER RUSTFLAGS CARGO_ENCODED_RUSTFLAGS
umask 077
mkdir "$out" "$compiler_temp"
export TMPDIR="$compiler_temp"
metadata="$study_dir/custody_metadata_B.py"
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
copied="$out/source/$study_rel"
phase() {
 local name=$1 status=0
 shift
 printf '%q ' "$@" > "$out/$name.argv"
 printf '\n' >> "$out/$name.argv"
 ( ulimit -c 0; ulimit -v 2097152; timeout --signal=TERM --kill-after=5s 120s "$@" ) > "$out/$name.stdout" 2> "$out/$name.stderr" || status=$?
 python3 "$metadata" phase "$out" "$name" "$status"
 if [[ "$status" -ne 0 ]]; then return "$status"; fi
}
phase rustc-version rustup run 1.99.1 rustc --version
phase clippy-version rustup run 1.99.1 clippy-driver --version
phase rustfmt-version rustup run 1.99.1 rustfmt --version
phase format rustup run 1.99.1 rustfmt --edition 2021 --config skip_children=true --check "$copied/field_a.rs" "$copied/packet_a.rs" "$copied/ec_a.rs" "$copied/cm_b.rs" "$copied/geometry_a.rs" "$copied/verify_a.rs" "$copied/main_b.rs"
phase compile rustup run 1.99.1 rustc --edition=2021 --crate-name chained_cm19_univariate_b -Dwarnings -Copt-level=3 -Coverflow-checks=yes -Cdebug-assertions=yes -Cdebuginfo=0 -Ccodegen-units=1 "$copied/main_b.rs" -o "$out/native-built"
phase clippy rustup run 1.99.1 clippy-driver --edition=2021 --crate-name chained_cm19_univariate_b -Dwarnings --emit=metadata "$copied/main_b.rs" -o "$out/clippy.rmeta"
cp "$out/native-built" "$out/qualifier"
chmod 0555 "$out/qualifier"
python3 "$metadata" pre "$out" > "$out/pre-call.stdout" 2> "$out/pre-call.stderr"
phase unit-audit "$out/qualifier" "$copied/actual-map-certificate.bin"
