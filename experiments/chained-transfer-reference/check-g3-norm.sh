#!/usr/bin/env bash
# Thin original-engine replay. All arithmetic/proof checks are Rust/Lean/PCC.
set -euo pipefail
test "$#" -eq 2
study_dir=$(cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$study_dir" rev-parse --show-toplevel)
upstream_root=$(cd -- "$1" && pwd -P)
for tool in bash git grep awk timeout sha256sum cargo rustc rustfmt lean jq realpath cmp mkdir date tee python3 cat cp find wc basename; do
  command -v "$tool" >/dev/null || { echo "missing canonical-norm replay tool:$tool" >&2; exit 2; }
done
pin=$(cat "$study_dir/g3-norm-upstream-commit.txt")
[[ $pin =~ ^[0-9a-f]{40}$ ]] || { echo 'invalid G3 norm producer revision' >&2; exit 2; }
[[ $(git -C "$upstream_root" rev-parse HEAD) == "$pin" ]] || { echo 'G3 norm producer HEAD mismatch' >&2; exit 2; }
[[ $(realpath "$repo_root/../crypto") == "$upstream_root" ]] || { echo 'G3 norm Cargo dependency sibling mismatch' >&2; exit 2; }
protected=(experiments/chained-transfer-reference/g3-norm-checker experiments/chained-transfer-reference/check-g3-norm.sh experiments/chained-transfer-reference/g3-norm-upstream-commit.txt experiments/chained-transfer-reference/g3-norm-reference-01.sha256 experiments/chained-transfer-reference/G3_NORM_REPLAY_PROTOCOL.md experiments/chained-transfer-reference/G3_NORM_DERIVATION.md experiments/chained-transfer-reference/G3_NORM_PROOF_MAP.md experiments/chained-transfer-reference/evidence/g3-norm-primary-01 experiments/chained-transfer-reference/evidence/g3-norm-lean-bindings-01 .github/workflows/chained-transfer-reference.yml tools/lean tools/pcc pcc/keyring.json)
mapfile -t claim_paths < <(jq -r '.[].claim_path' "$study_dir/evidence/g3-norm-lean-bindings-01/claims.json")
[[ ${#claim_paths[@]} -eq 13 ]]
protected+=("${claim_paths[@]}")
assert_clean() {
  test -z "$(git -C "$repo_root" status --porcelain --untracked-files=all -- "${protected[@]}")" || { echo 'dirty protected G3 norm consumer input' >&2; return 2; }
  test -z "$(git -C "$upstream_root" status --porcelain --untracked-files=all -- isogeny_algos src/cryptanalysis/diem_quartic.rs src/cryptanalysis/plane_quartic_pic.rs src/hash/sha256.rs research/chained_jacobian_transfers_20261110/genus3-prime-descent tools/lean tools/pcc pcc/keyring.json)" || { echo 'dirty protected G3 norm producer input' >&2; return 2; }
}
assert_clean
out=$(realpath -m "$2")
build=$(realpath -m "${CARGO_TARGET_DIR:-${out}-build-cache}")
case "$out/" in "$repo_root/"*|"$upstream_root/"*|"$build/"*) echo 'G3 norm output overlaps source/cache' >&2; exit 2;; esac
case "$build/" in "$repo_root/"*|"$upstream_root/"*|"$out/"*) echo 'G3 norm cache overlaps source/output' >&2; exit 2;; esac
test ! -e "$out" || { echo 'G3 norm output already exists' >&2; exit 2; }
test ! -e "$build" || { echo 'G3 norm cache already exists' >&2; exit 2; }
cd "$repo_root"
reference=experiments/chained-transfer-reference/g3-norm-reference-01.sha256
sha256sum --check "$reference" >/dev/null
python3 - "$study_dir" "$repo_root" <<'PREFIX'
from pathlib import Path
import sys
study,repo=map(Path,sys.argv[1:])
old=(study/'evidence/g3-norm-primary-01/six-original-jobs.yml').read_bytes()
if len(old)!=20796 or not (repo/'.github/workflows/chained-transfer-reference.yml').read_bytes().startswith(old):
    raise SystemExit('changed complete old six-job prefix')
PREFIX
mkdir "$out"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out/start.txt"
finish() {
  status=$?
  trap - EXIT
  set +e
  cd "$repo_root"
  sha256sum --check "$reference" > "$out/final-inputs.log" 2>&1
  guard=$?
  printf '%s\n' "$guard" > "$out/guard.exit"
  assert_clean > "$out/final-cleanliness.log" 2>&1
  clean=$?
  printf '%s\n' "$clean" > "$out/cleanliness.exit"
  printf '%s\n' "$status" > "$out/original.exit"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$out/finish.txt"
  if [ "$status" -ne 0 ]; then exit "$status"; fi
  if [ "$guard" -ne 0 ]; then exit "$guard"; fi
  exit "$clean"
}
trap finish EXIT
sha256sum --check "$reference" > "$out/initial-inputs.log"
cp "$reference" "$out/original-reference.sha256"
rustc -Vv > "$out/rustc.txt"
cargo -V > "$out/cargo.txt"
lean --version > "$out/lean.txt"
git rev-parse HEAD > "$out/consumer-head.txt"
git -C "$upstream_root" rev-parse HEAD > "$out/producer-head.txt"
run_logged() {
  label=$1
  shift
  set +e
  "$@" 2>&1 | tee "$out/$label.log"
  codes=("${PIPESTATUS[@]}")
  set -e
  printf '%s %s\n' "${codes[0]}" "${codes[1]}" > "$out/$label.pipe-exits"
  test "${codes[0]}" -eq 0
  test "${codes[1]}" -eq 0
}
export CARGO_TARGET_DIR="$build"
export ELAN_TOOLCHAIN=leanprover/lean4:v4.35.0
manifest="$study_dir/g3-norm-checker/Cargo.toml"
run_logged fetch cargo fetch --locked --manifest-path "$manifest"
run_logged format rustfmt --edition 2021 --config skip_children=true --check "$study_dir/g3-norm-checker/src/lib.rs" "$study_dir/g3-norm-checker/src/main.rs" "$study_dir/g3-norm-checker/src/tests.rs"
run_logged clippy cargo clippy --all-targets --offline --locked --manifest-path "$manifest" -- -D warnings
cd "$upstream_root"
run_logged producer timeout 1500 bash research/chained_jacobian_transfers_20261110/genus3-prime-descent/check.sh "$out/producer"
[[ $(find "$out/producer" -maxdepth 1 -name '*.pipe-exits' | wc -l) -eq 20 ]]
awk '{if(NF!=2 || $1!=0 || $2!=0) exit 1}' "$out/producer/"*.pipe-exits
cd "$repo_root"
run_logged unit timeout 900 cargo test --release --offline --locked --manifest-path "$manifest" --lib -- --nocapture --test-threads=1
grep -Eq '^test result: ok\. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/unit.log"
for q in 5 7 11; do
  run_logged "cli-q$q" cargo run --release --offline --locked --manifest-path "$manifest" -- "$study_dir/g3-norm-checker/fixtures/q$q-request.json" "$out/q$q-output.json"
  cmp "$out/q$q-output.json" "$study_dir/g3-norm-checker/fixtures/q$q-output.json"
done
proof=experiments/chained-transfer-reference/g3-norm-checker/lean/CanonicalNorm.lean
run_logged lean-producer timeout 600 bash "$upstream_root/tools/lean/proof-gate.sh" --out "$out/proofs-producer" "$proof"
ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 run_logged lean-consumer timeout 600 bash tools/lean/proof-gate.sh --out "$out/proofs-consumer" "$proof"
for label in lean-producer lean-consumer; do
  awk '/^PASS[[:space:]]/ {n++;thms+=$2;trusted+=$4} END {if(n!=1 || thms!=13 || trusted!=0) exit 1}' "$out/$label.log"
done
[[ $(jq length "$study_dir/evidence/g3-norm-lean-bindings-01/claims.json") -eq 13 ]]
while IFS= read -r claim; do
  ELAN_TOOLCHAIN=leanprover/lean4:v4.34.1 run_logged "pcc-$(basename "$claim" .json)" python3 tools/pcc/pcc.py verify "$claim" --json
done < <(jq -r '.[].claim_path' "$study_dir/evidence/g3-norm-lean-bindings-01/claims.json")
[[ $(find "$out" -maxdepth 1 -name '*.pipe-exits' | wc -l) -eq 23 ]]
awk '{if(NF!=2 || $1!=0 || $2!=0) exit 1}' "$out/"*.pipe-exits
printf 'G3 norm replay complete:producer20pairs;consumer4tests/9CLIclasses/two13declarationgates/13exactbindings;23outerpairs/allinputguards\n'
