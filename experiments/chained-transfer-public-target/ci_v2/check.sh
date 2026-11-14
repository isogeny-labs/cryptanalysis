#!/usr/bin/env bash
# Orchestration only; every arithmetic/proof operation uses the original engines.
set -euo pipefail
[[ $# -eq 2 ]] || exit 2
for tool in bash git sha256sum cargo rustc rustfmt lean lake jq realpath cmp mkdir date tee python3 timeout grep cp; do
  command -v "$tool" >/dev/null || { echo "missing V2 replay tool:$tool" >&2; exit 2; }
done
ci=$(cd -- "$(dirname -- "$0")" && pwd -P)
study=$(dirname "$ci")
repo=$(git -C "$study" rev-parse --show-toplevel)
producer=$(cd -- "$1" && pwd -P)
[[ "$producer" == "$(dirname "$repo")/crypto" ]] || { echo 'producer must be physical Cargo sibling' >&2; exit 2; }
pin=$(cat "$study/upstream-commit.txt")
[[ "$pin" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ $(git -C "$producer" rev-parse HEAD) == "$pin" ]] || { echo 'wrong actual producer HEAD' >&2; exit 2; }
protected=(experiments/chained-transfer-public-target tools/lean tools/pcc pcc/keyring.json .github/workflows/chained-transfer-reference.yml .github/workflows/chained-transfer-public-target.yml .github/workflows/chained-transfer-completed-v2.yml .github/workflows/pcc-gate.yml)
mapfile -t claims < <(jq -r '.[].claim_path' "$study/evidence/prime-field-bindings-02/claims.json")
[[ ${#claims[@]} -eq 3 ]] || exit 2
protected+=("${claims[@]}")
assert_clean() {
  [[ -z $(git -C "$repo" status --porcelain --untracked-files=all -- "${protected[@]}") ]] || { echo 'dirty protected consumer input' >&2; return 2; }
  [[ -z $(git -C "$producer" status --porcelain --untracked-files=all -- isogeny_algos src/cryptanalysis/diem_quartic.rs src/cryptanalysis/plane_quartic_pic.rs src/hash/sha256.rs research/chained_jacobian_transfers_20261110/genus3-prime-descent research/quartic_n4_la_20261021 tools/lean tools/pcc pcc/keyring.json) ]] || { echo 'dirty protected producer input' >&2; return 2; }
}
assert_clean
out=$(realpath -m "$2")
build=$(realpath -m "${CARGO_TARGET_DIR:-${out}-build-cache}")
case "$out/" in "$repo/"*|"$producer/"*|"$build/"*) echo 'output overlaps source/cache' >&2; exit 2;; esac
case "$build/" in "$repo/"*|"$producer/"*|"$out/"*) echo 'cache overlaps source/output' >&2; exit 2;; esac
[[ ! -e "$out" && ! -e "$build" ]] || { echo 'output/cache must be fresh' >&2; exit 2; }
cd "$repo"
reference=experiments/chained-transfer-public-target/ci_v2/reference-01.sha256
sha256sum --check "$reference" >/dev/null || exit 2
cmp .github/workflows/chained-transfer-reference.yml "$study/evidence/primary-01/whole-parent-seven-jobs.yml" || exit 2
mkdir "$out"
export RUSTUP_TOOLCHAIN=1.99.1
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/start.txt"
finish() {
  status=$?
  trap - EXIT
  set +e
  cd "$repo"
  sha256sum --check "$reference" > "$out/final-inputs.log" 2>&1
  guard=$?
  cmp "$reference" "$out/original-reference.sha256" >> "$out/final-inputs.log" 2>&1 || guard=1
  [[ $(git rev-parse HEAD) == "$(cat "$out/consumer-head.txt")" ]] || guard=1
  [[ $(git -C "$producer" rev-parse HEAD) == "$pin" ]] || guard=1
  assert_clean > "$out/final-cleanliness.log" 2>&1
  clean=$?
  printf '%s\n' "$status" > "$out/original.exit"
  printf '%s\n' "$guard" > "$out/guard.exit"
  printf '%s\n' "$clean" > "$out/cleanliness.exit"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$out/finish.txt"
  [[ "$status" -eq 0 ]] || exit "$status"
  [[ "$guard" -eq 0 ]] || exit "$guard"
  exit "$clean"
}
trap finish EXIT
cp "$reference" "$out/original-reference.sha256"
git rev-parse HEAD > "$out/consumer-head.txt"
git -C "$producer" rev-parse HEAD > "$out/producer-head.txt"
rustc -Vv > "$out/rustc.txt"
python3 "$ci/replay_io.py" snapshot "$repo" "$producer" "$out"
run_expected() {
  expected=$1; label=$2; shift 2
  set +e
  "$@" 2>&1 | tee "$out/$label.log"
  codes=("${PIPESTATUS[@]}")
  set -e
  printf '%s %s\n' "${codes[0]}" "${codes[1]}" > "$out/$label.pipe-exits"
  printf '%s %s %s\n' "$label" "$expected" "${codes[0]}" >> "$out/phase-index.txt"
  [[ ${codes[0]} -eq "$expected" && ${codes[1]} -eq 0 ]]
}
export CARGO_TARGET_DIR="$build"
v2="$study/v2/Cargo.toml"
rho="$study/rho-accessor/Cargo.toml"
run_expected 0 fetch-v2 cargo fetch --locked --manifest-path "$v2"
run_expected 0 fetch-rho cargo fetch --locked --manifest-path "$rho"
run_expected 0 format rustfmt --edition 2021 --config skip_children=true --check "$study/v2/src/lib.rs" "$study/v2/src/tests.rs" "$study/rho-accessor/src/lib.rs" "$study/rho-accessor/src/main.rs"
run_expected 0 compile-v2 timeout 900 cargo test --release --offline --locked --manifest-path "$v2" --lib --no-run
run_expected 0 v2 bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$v2"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/v2.log"
run_expected 0 compile-rho timeout 900 cargo test --release --offline --locked --manifest-path "$rho" --lib --no-run
run_expected 0 rho bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$rho"
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/rho.log"
run_expected 0 build-rho cargo build --release --offline --locked --manifest-path "$rho"
bin="$build/release/chained-n4-rho-accessor"
native_cli() { (ulimit -v 2097152; exec timeout 900 "$bin" "$@"); }
run_expected 0 rho-five native_cli solve "$study/fixtures/public-five.json" "$out/rho-five.json"
run_expected 2 reject-scalar native_cli solve "$study/fixtures/negative/unknown-scalar.json" "$out/reject-scalar.json"
run_expected 2 reject-witness native_cli solve "$study/fixtures/negative/unknown-witness.json" "$out/reject-witness.json"
run_expected 0 output-bytes python3 "$ci/replay_io.py" outputs "$ci" "$out"
module=experiments/chained-transfer-public-target/prime-field/NoBaseFieldCurve.lean
run_expected 0 producer-proof env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash "$producer/tools/lean/proof-gate.sh" --out "$out/producer-proofs" "$repo/$module"
run_expected 0 consumer-proof env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-proofs" "$module"
for claim in "${claims[@]}"; do
  run_expected 0 "binding-$(basename "$claim" .json)" env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "$claim" --json
done
python3 "$ci/replay_io.py" phases "$ci" "$out"
echo 'Completed V2/rho replay complete: all7V2+5rho native records,5actualCLI answers/2actualrejections,bothoriginal3theorem gates/3exactbindings/all17phasepairs matched. Unsigned correctness only.'
