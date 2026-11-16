#!/usr/bin/env bash
# Original arithmetic/proof engines; this shell only orchestrates their replay.
set -euo pipefail
[[ $# -eq 2 ]] || exit 2
for tool in bash git sha256sum cargo rustc rustfmt lean lake jq realpath cmp mkdir date tee python3 xz cp timeout grep; do
  command -v "$tool" >/dev/null || { echo "missing public-target replay tool:$tool" >&2; exit 2; }
done
study=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$study" rev-parse --show-toplevel)
producer=$(cd -- "$1" && pwd -P)
[[ "$producer" == "$(dirname "$repo")/crypto" ]] || { echo 'producer must be the physical Cargo sibling' >&2; exit 2; }
pin=$(cat "$study/upstream-commit.txt")
[[ "$pin" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ $(git -C "$producer" rev-parse HEAD) == "$pin" ]] || { echo 'wrong actual producer HEAD' >&2; exit 2; }
protected=(experiments/chained-transfer-public-target tools/lean tools/pcc pcc/keyring.json .github/workflows/chained-transfer-reference.yml .github/workflows/chained-transfer-public-target.yml .github/workflows/pcc-gate.yml)
mapfile -t claims < <(jq -r '.[].claim_path' "$study/evidence/lean-bindings-01/claims.json" "$study/evidence/origin-lean-bindings-01/claims.json")
[[ ${#claims[@]} -eq 14 ]] || exit 2
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
reference=experiments/chained-transfer-public-target/reference-02.sha256
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
cargo -V > "$out/cargo.txt"
python3 "$study/replay_io.py" snapshot "$repo" "$producer" "$out"
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
export RUSTUP_TOOLCHAIN=1.99.1
export CARGO_TARGET_DIR="$build"
manifest="$study/native/Cargo.toml"
run_expected 0 fetch cargo fetch --locked --manifest-path "$manifest"
run_expected 0 format rustfmt --edition 2021 --config skip_children=true --check "$study/native/src/lib.rs" "$study/native/src/main.rs" "$study/native/src/tests.rs"
run_expected 0 compiler cargo check --offline --locked --all-targets --manifest-path "$manifest"
for name in common ghs ic solver; do
  run_expected 0 "original-$name" cmp "$study/native/original/$name.rs" "$producer/research/quartic_n4_la_20261021/$name.rs"
done
run_expected 0 compile-tests timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib --no-run
run_expected 0 unit bash -c 'ulimit -v 2097152; exec timeout 900 cargo test --release --offline --locked --manifest-path "$1" --lib -- --nocapture --test-threads=1' _ "$manifest"
grep -Eq '^test result: ok\. 3 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/unit.log"
run_expected 0 build-cli cargo build --release --offline --locked --manifest-path "$manifest"
bin="$build/release/chained-n4-public-target"
native_cli() { (ulimit -v 2097152; exec "$bin" "$@"); }
run_expected 0 describe native_cli describe "$out/describe.json"
run_expected 0 public-five native_cli solve "$study/fixtures/public-five.json" "$out/public-five.json"
for label in foreign-q schema field model noncanonical offcurve nonmember unknown-scalar unknown-witness empty six; do
  run_expected 2 "reject-$label" native_cli solve "$study/fixtures/negative/$label.json" "$out/reject-$label.json"
done
python3 "$study/replay_io.py" oversize "$study/fixtures/index.json" "$out/oversize.json"
run_expected 2 reject-oversize native_cli solve "$out/oversize.json" "$out/reject-oversize.json"
printf 'original output sentinel\n' > "$out/overwrite.json"
run_expected 2 reject-overwrite native_cli solve "$study/fixtures/public-five.json" "$out/overwrite.json"
run_expected 2 reject-extra-arg native_cli solve "$study/fixtures/public-five.json" "$out/reject-extra-arg.json" EXTRA
run_expected 0 output-bytes python3 "$study/replay_io.py" outputs "$study" "$out"
modules=("$study/native/lean/PublicTargetBridge.lean" "$study/formal/PublicOriginConvention.lean")
run_expected 0 producer-proof env ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0 bash "$producer/tools/lean/proof-gate.sh" --out "$out/producer-proofs" "${modules[@]}"
consumer_modules=(experiments/chained-transfer-public-target/native/lean/PublicTargetBridge.lean experiments/chained-transfer-public-target/formal/PublicOriginConvention.lean)
run_expected 0 consumer-proof env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 bash tools/lean/proof-gate.sh --out "$out/consumer-proofs" "${consumer_modules[@]}"
for claim in "${claims[@]}"; do
  run_expected 0 "binding-$(basename "$claim" .json)" env ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 python3 tools/pcc/pcc.py verify "$claim" --json
done
python3 "$study/replay_io.py" phases "$out"
echo 'Public-target N4 replay complete: all3unfiltered tests/5publicCLI targets/14actualrejections/bothoriginal9+5modulegates/14exactbindings;allphasepairs matched expected statuses. Unsigned correctness only.'
