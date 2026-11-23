#!/usr/bin/env bash
# Portable regression only. Local original execution receipts remain distinct.
set -euo pipefail
out=${1:?fresh output directory}
study_dir=$(cd "$(dirname "$0")" && pwd)
repo_dir=$(git -C "$study_dir" rev-parse --show-toplevel)
study_rel=research/chained_cm19_univariate_audit_20261123
export RAYON_NUM_THREADS=1 CARGO_BUILD_JOBS=1
export LEAN_NUM_THREADS=1 LEAN_STACK_SIZE_KB=16384 LEAN_MAIN_USE_THREAD=0 MIMALLOC_ARENA_RESERVE=65536
export CHECKPOINT_SKIP="Ordinary fixed completed-certificate and Core coefficient regression, no experiment or timing comparison; exact source/input checksums verified before calls."
unset RUSTC_WRAPPER RUSTC_WORKSPACE_WRAPPER RUSTFLAGS CARGO_ENCODED_RUSTFLAGS CLIPPY_ARGS LEAN_SYSROOT LEAN_PATH LEAN_OPTS
umask 077
mkdir "$out" "$out/temp"
export TMPDIR="$out/temp"
metadata="$study_dir/ci_custody_metadata_C.py"
finish() {
 local status=$? guard_status=0
 trap - EXIT
 python3 "$metadata" finish "$out" "$status" > "$out/final-guards.stdout" 2> "$out/final-guards.stderr" || guard_status=$?
 if [[ "$status" -ne 0 ]]; then exit "$status"; fi
 exit "$guard_status"
}
trap finish EXIT
cd "$repo_dir"
python3 "$metadata" prepare "$out" > "$out/init.stdout" 2> "$out/init.stderr"
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
phase rustfmt-version rustup run 1.99.1 rustfmt --version
phase clippy-version rustup run 1.99.1 clippy-driver --version
phase format rustup run 1.99.1 rustfmt --edition 2021 --config skip_children=true --check "$copied/field_a.rs" "$copied/packet_a.rs" "$copied/ec_a.rs" "$copied/cm_b.rs" "$copied/geometry_a.rs" "$copied/verify_a.rs" "$copied/main_b.rs"
phase compile rustup run 1.99.1 rustc --edition=2021 --crate-name chained_cm19_univariate_ci -Dwarnings -Copt-level=3 -Coverflow-checks=yes -Cdebug-assertions=yes -Cdebuginfo=0 -Ccodegen-units=1 "$copied/main_b.rs" -o "$out/native-built"
phase clippy rustup run 1.99.1 clippy-driver --edition=2021 --crate-name chained_cm19_univariate_ci -Dwarnings --emit=metadata "$copied/main_b.rs" -o "$out/clippy.rmeta"
cp "$out/native-built" "$out/qualifier"
chmod 0555 "$out/qualifier"
python3 "$metadata" pre "$out" > "$out/pre-call.stdout" 2> "$out/pre-call.stderr"
phase packet-regression "$out/qualifier" "$copied/actual-map-certificate.bin"
phase lean-version "$LEAN_TOOLCHAIN_DIR/bin/lean" -j1 --version
cd "$copied/formal"
phase coefficient-regression "$LEAN_TOOLCHAIN_DIR/bin/lean" -j1 -DwarningAsError=true -o "$out/CoefficientLeavesA.olean" CoefficientLeavesA.lean
