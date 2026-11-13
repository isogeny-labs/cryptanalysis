#!/usr/bin/env bash
# Complete fixed-model F101 C0/T20 adapter. Existing five drivers/jobs/pins stay frozen.
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$study_dir" rev-parse --show-toplevel)
upstream_root=$(cd -- "${1:-$repo_root/../crypto}" && pwd)
for required_tool in bash git grep awk timeout sha256sum cargo rustfmt lean find sort xargs cmp mktemp date python3 cat wc tee; do
  command -v "$required_tool" >/dev/null || { echo "missing fp-chain replay tool:$required_tool" >&2; exit 2; }
done
pin=$(cat "$study_dir/fp-chain-upstream-commit.txt")
[[ $pin =~ ^[0-9a-f]{40}$ ]] || { echo 'invalid fp-chain source revision' >&2; exit 2; }
actual=$(git -C "$upstream_root" rev-parse HEAD)
[[ $actual == "$pin" ]] || { echo "fp-chain source HEAD mismatch:expected $pin,found $actual" >&2; exit 2; }
upstream_study=research/chained_jacobian_transfers_20261110
consumer_study=experiments/chained-transfer-reference
identity_names=(
  quartic-duplication-identity-03 two-primary-halving-identity-03
  isogeny-cycle-norm-identity-01 isogeny-cycle-first-identity-01
  isogeny-cycle-second-identity-01 unbalanced-direct-identity-01
  unbalanced-reciprocal-identity-01 even-kernel-cubic-identity-01
  t20-common-scale-identity-01 t20-normalization-identity-01
  t20-direct-linear-image-identity-02
)
protected_paths=(
  "$upstream_study/successor-preflight" "$upstream_study/algebra-certificates"
  "$upstream_study/lean" isogeny_algos src/cryptanalysis/jv_cover.rs
  src/cryptanalysis/identity_certificate.rs src/hash/sha256.rs tools/lean
  docs/identity-certificates/schoenhage-10mult.json
  "$upstream_study/evidence/kernel-full-03/kernel-certificate.json"
  "$upstream_study/evidence/t20-full-02/geometry-certificate.json"
)
for name in "${identity_names[@]}"; do protected_paths+=("$upstream_study/evidence/$name.json"); done
consumer_paths=(
  "$consumer_study/src" "$consumer_study/kernel-checker"
  "$consumer_study/norm-checker" "$consumer_study/check-prime-norms.sh"
  "$consumer_study/fp-chain-upstream-commit.txt"
  "$consumer_study/PRIME_NORM_REPLAY_PROTOCOL.md"
  "$consumer_study/PRIME_NORM_PULLBACK_DERIVATION.md"
  "$consumer_study/evidence/prime-norm-fibre-identity-01.json"
  suite/src/prime_hyperelliptic .github/workflows/chained-transfer-reference.yml
)

consumer_paths+=(
  "$consumer_study/fp-chain-checker" "$consumer_study/check-fp-chain.sh"
  "$consumer_study/FP_CHAIN_ADAPTER_PROTOCOL.md"
  "$consumer_study/FP_CHAIN_ADAPTER_DERIVATION.md"
  "$consumer_study/FP_CHAIN_PROOF_COMPATIBILITY.md"
  "$consumer_study/evidence/fp-chain-primary-01/baseline.json"
  "$consumer_study/evidence/fp-chain-primary-01/five-original-jobs.yml"
  .github/workflows/pcc-gate.yml
  "experiments/chained-transfer-reference/PRIME_NORM_PULLBACK_DERIVATION.md"
  "experiments/chained-transfer-reference/PRIME_NORM_REPLAY_PROTOCOL.md"
  "experiments/chained-transfer-reference/check-prime-norms.sh"
  "experiments/chained-transfer-reference/evidence/prime-norm-fibre-identity-01.json"
  "experiments/chained-transfer-reference/kernel-checker/.gitignore"
  "experiments/chained-transfer-reference/kernel-checker/Cargo.lock"
  "experiments/chained-transfer-reference/kernel-checker/Cargo.toml"
  "experiments/chained-transfer-reference/kernel-checker/src/main.rs"
  "experiments/chained-transfer-reference/norm-checker/Cargo.lock"
  "experiments/chained-transfer-reference/norm-checker/Cargo.toml"
  "experiments/chained-transfer-reference/norm-checker/engine/Cargo.toml"
  "experiments/chained-transfer-reference/norm-checker/engine/src/lib.rs"
  "experiments/chained-transfer-reference/norm-checker/fixtures/t20-norms.json"
  "experiments/chained-transfer-reference/norm-checker/lean/PullbackFibres.lean"
  "experiments/chained-transfer-reference/norm-checker/lean/lean-toolchain"
  "experiments/chained-transfer-reference/norm-checker/src/lib.rs"
  "experiments/chained-transfer-reference/norm-checker/src/main.rs"
  "experiments/chained-transfer-reference/norm-checker/src/tests.rs"
  "experiments/chained-transfer-reference/prime-norm-upstream-commit.txt"
  "experiments/chained-transfer-reference/src/balanced.rs"
  "experiments/chained-transfer-reference/src/closed_fibres.rs"
  "experiments/chained-transfer-reference/src/cubic_transfer.rs"
  "experiments/chained-transfer-reference/src/direct_norms.rs"
  "experiments/chained-transfer-reference/src/full_class_fixtures.rs"
  "experiments/chained-transfer-reference/src/main.rs"
  "experiments/chained-transfer-reference/src/nonsplit.rs"
  "experiments/chained-transfer-reference/src/nonsplit_map.rs"
  "experiments/chained-transfer-reference/src/odd_kernels.rs"
  "experiments/chained-transfer-reference/src/prime_field_adjoint.rs"
  "experiments/chained-transfer-reference/src/prime_field_pipeline.rs"
  "experiments/chained-transfer-reference/src/prime_field_psi.rs"
  "experiments/chained-transfer-reference/src/prime_field_reverse.rs"
  "experiments/chained-transfer-reference/src/quartic_cover.rs"
  "experiments/chained-transfer-reference/src/quartic_lagrange.rs"
  "experiments/chained-transfer-reference/src/quartic_norm.rs"
  "experiments/chained-transfer-reference/src/quartic_pullback.rs"
  "experiments/chained-transfer-reference/src/quartic_pullback_points.rs"
  "experiments/chained-transfer-reference/src/seven.rs"
  "experiments/chained-transfer-reference/src/seven_chain.rs"
  "experiments/chained-transfer-reference/src/seven_glue.rs"
  "experiments/chained-transfer-reference/src/seven_successor.rs"
  "experiments/chained-transfer-reference/src/seven_successor_chain.rs"
  "experiments/chained-transfer-reference/src/seven_successor_torsion.rs"
  "experiments/chained-transfer-reference/src/seven_torsion.rs"
  "experiments/chained-transfer-reference/src/small_prime_oracle.rs"
  "experiments/chained-transfer-reference/src/t2_quartic_adapters.rs"
  "suite/src/prime_hyperelliptic/curve.rs"
  "suite/src/prime_hyperelliptic/fp2.rs"
  "suite/src/prime_hyperelliptic/fp_poly.rs"
  "suite/src/prime_hyperelliptic/mod.rs"
)
assert_clean() {
  local dirty
  dirty=$(git -C "$upstream_root" status --porcelain --untracked-files=all -- "${protected_paths[@]}")
  [[ -z $dirty ]] || { echo 'fp-chain source has modified or untracked protected inputs' >&2; return 2; }
  dirty=$(git -C "$repo_root" status --porcelain --untracked-files=all -- "${consumer_paths[@]}")
  [[ -z $dirty ]] || { echo 'fp-chain consumer has modified or untracked protected inputs' >&2; return 2; }
}
assert_clean || exit 2
# Baseline retention is a byte check, not an execution-proof claim.
python3 - "$repo_root" "$study_dir" <<'BASELINE'
from pathlib import Path
import json,hashlib,sys
repo,study=map(Path,sys.argv[1:]);baseline=json.loads((study/'evidence/fp-chain-primary-01/baseline.json').read_text())
for name,want in baseline['non_workflow_inputs'].items():
    if hashlib.sha256((repo/name).read_bytes()).hexdigest()!=want:
        raise SystemExit('changed frozen prior replay input:'+name)
old=(study/'evidence/fp-chain-primary-01/five-original-jobs.yml').read_bytes()
if not (repo/'.github/workflows/chained-transfer-reference.yml').read_bytes().startswith(old):
    raise SystemExit('changed complete five-job prefix')
BASELINE
dependency_root=$(cd -- "$study_dir/../../../crypto" && pwd)
[[ $dependency_root == "$upstream_root" ]] || { echo 'fp-chain dependency layout mismatch' >&2; exit 2; }
if [[ $# -ge 2 ]]; then
  run_dir=$2
  [[ ! -e $run_dir ]] || { echo 'fp-chain output directory already exists' >&2; exit 2; }
  mkdir -- "$run_dir"
else
  run_dir=$(mktemp -d "${TMPDIR:-/tmp}/chained-fp-chain.XXXXXXXX")
fi
run_dir=$(cd -- "$run_dir" && pwd)
build_root=$(mktemp -d "${TMPDIR:-/tmp}/chained-fp-chain-build.XXXXXXXX")
printf '%s\n' "$build_root" > "$run_dir/build-cache-path.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$run_dir/start.txt"
cd -- "$upstream_root"
git ls-files -z -- "${protected_paths[@]}" | xargs -0 sha256sum > "$run_dir/source.sha256"
(cd -- "$repo_root" && git ls-files -z -- "${consumer_paths[@]}" | xargs -0 sha256sum) > "$run_dir/consumer.sha256"
finish() {
  local original=$? source_guard consumer_guard cleanliness result
  trap - EXIT
  set +e
  (cd -- "$upstream_root" && sha256sum --check "$run_dir/source.sha256") > "$run_dir/after.txt" 2>&1
  source_guard=$?
  (cd -- "$repo_root" && sha256sum --check "$run_dir/consumer.sha256") > "$run_dir/consumer-after.txt" 2>&1
  consumer_guard=$?
  assert_clean > "$run_dir/cleanliness.txt" 2>&1
  cleanliness=$?
  printf '%s\n' "$original" > "$run_dir/original.exit"
  printf '%s %s %s\n' "$source_guard" "$consumer_guard" "$cleanliness" > "$run_dir/guard-exits.txt"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$run_dir/finish.txt"
  result=$original
  if [[ $result -eq 0 && ( $source_guard -ne 0 || $consumer_guard -ne 0 || $cleanliness -ne 0 ) ]]; then result=1; fi
  printf '%s\n' "$result" > "$run_dir/driver.exit"
  exit "$result"
}
trap finish EXIT
export CARGO_TERM_COLOR=never RUSTUP_TOOLCHAIN=1.99.1
export study_dir repo_root upstream_root upstream_study run_dir build_root
identity_names_joined="${identity_names[*]}"
export identity_names_joined
{
  printf 'Pinned fp-chain source %s\n' "$pin"
  cargo --version
  rustfmt --version
  lean --version
  sha256sum "$upstream_root/tools/lean/lean-toolchain" "$study_dir/norm-checker/Cargo.lock" "$study_dir/kernel-checker/Cargo.lock" "$study_dir/fp-chain-checker/Cargo.lock" "$study_dir/fp-chain-checker/lean/lean-toolchain"
} | tee "$run_dir/toolchains.txt"

native_phase() {
  cd "$upstream_root/$upstream_study/successor-preflight"
  export CARGO_TARGET_DIR="$build_root/successor"
  export CHAINED_EVEN_KERNEL_CERTIFICATE_OUT="$run_dir/kernel.json"
  export CHAINED_T20_GEOMETRY_OUT="$run_dir/geometry.json"
  sha256sum --check reference.sha256
  sha256sum --check legacy.sha256
  cargo fmt -- --check
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  cargo test --release --offline --locked -- --nocapture
  cmp "$run_dir/kernel.json" ../evidence/kernel-full-03/kernel-certificate.json
  cmp "$run_dir/geometry.json" ../evidence/t20-full-02/geometry-certificate.json
}
algebra_phase() {
  cd "$upstream_root/$upstream_study/algebra-certificates"
  export CARGO_TARGET_DIR="$build_root/algebra"
  sha256sum --check reference.sha256
  cargo fmt -- --check
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  cargo test --release --offline --locked -- --nocapture
  local names outputs i
  read -r -a names <<< "$identity_names_joined"
  outputs=()
  for i in "${!names[@]}"; do outputs+=("$run_dir/identity-$i.json"); done
  cargo run --release --offline --locked -- "${outputs[@]}"
  for i in "${!names[@]}"; do cmp "${outputs[i]}" "../evidence/${names[i]}.json"; done
}
proof_phase() {
  cd "$upstream_root"
  grep -nE '^(theorem|lemma) ' "$upstream_study"/lean/*.lean > "$run_dir/written-declarations.txt"
  [[ $(wc -l < "$run_dir/written-declarations.txt") -eq 212 ]]
  bash tools/lean/proof-gate.sh --out "$run_dir/proofs" "$upstream_study"/lean/*.lean
}
kernel_phase() {
  cd "$study_dir/kernel-checker"
  export CARGO_TARGET_DIR="$build_root/successor"
  cargo fmt -- --check
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  cargo test --release --offline --locked -- --nocapture
}
kernel_cli_phase() {
  cd "$study_dir/kernel-checker"
  export CARGO_TARGET_DIR="$build_root/successor"
  cargo run --release --offline --locked -- "$run_dir/kernel.json"
}
norm_phase() {
  cd "$study_dir/norm-checker"
  export CARGO_TARGET_DIR="$build_root/successor"
  # Imported source is frozen: do not recursively format #[path] dependencies.
  rustfmt --edition 2021 --check --config skip_children=true src/lib.rs src/main.rs src/tests.rs engine/src/lib.rs
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  cargo test --release --offline --locked -- --nocapture
}
norm_cli_phase() {
  cd "$study_dir/norm-checker"
  export CARGO_TARGET_DIR="$build_root/successor"
  cargo run --release --offline --locked -- fixtures/t20-norms.json "$run_dir/consumer-fibre-identity.json"
  cmp "$run_dir/consumer-fibre-identity.json" ../evidence/prime-norm-fibre-identity-01.json
}
consumer_proof_phase() {
  cd "$repo_root"
  bash "$upstream_root/tools/lean/proof-gate.sh" --out "$run_dir/consumer-proofs" "$study_dir/norm-checker/lean/PullbackFibres.lean"
}
chain_phase() {
  cd "$study_dir/fp-chain-checker"
  export CARGO_TARGET_DIR="$build_root/successor"
  rustfmt --edition 2021 --check --config skip_children=true src/lib.rs src/main.rs src/tests.rs elliptic-engine/src/lib.rs
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  cargo test --release --offline --locked -- --nocapture
}
chain_cli_phase() {
  cd "$study_dir/fp-chain-checker"
  export CARGO_TARGET_DIR="$build_root/successor"
  cargo run --release --offline --locked -- fixtures/c0-t20.json
}
chain_proof_phase() {
  cd "$repo_root"
  # Both compilation and the unchanged audit must use the explicit source pin.
  export ELAN_TOOLCHAIN
  ELAN_TOOLCHAIN=$(cat "$study_dir/fp-chain-checker/lean/lean-toolchain")
  grep -nE '^(theorem|lemma) ' "$study_dir/fp-chain-checker/lean/ChainAdapter.lean" > "$run_dir/chain-written-declarations.txt"
  [[ $(wc -l < "$run_dir/chain-written-declarations.txt") -eq 11 ]]
  bash "$upstream_root/tools/lean/proof-gate.sh" --out "$run_dir/chain-proofs" "$study_dir/fp-chain-checker/lean/ChainAdapter.lean"
}
export -f chain_phase chain_cli_phase chain_proof_phase native_phase algebra_phase proof_phase kernel_phase kernel_cli_phase norm_phase norm_cli_phase consumer_proof_phase
run_phase() {
  local name=$1 limit=$2 function=$3 pipeline
  date -u +%Y-%m-%dT%H:%M:%SZ > "$run_dir/$name.start"
  set +e
  timeout "$limit" bash -euo pipefail -c "$function" 2>&1 | tee "$run_dir/$name.txt"
  pipeline=("${PIPESTATUS[@]}")
  set -e
  printf '%s %s\n' "${pipeline[0]}" "${pipeline[1]}" > "$run_dir/$name.exits"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$run_dir/$name.finish"
  [[ ${pipeline[0]} -eq 0 && ${pipeline[1]} -eq 0 ]]
}
run_phase native 15m native_phase
grep -Eq '^test result: ok\. 43 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/native.txt"
run_phase algebra 15m algebra_phase
grep -Eq '^test result: ok\. 24 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/algebra.txt"
run_phase proofs 10m proof_phase
awk '/^PASS[[:space:]]/ {modules++;compiled+=$2;trusted+=$4} END {if(modules!=40 || compiled!=238 || trusted!=0) exit 1;printf "PASS prime-norm upstream proofs:40modules/238compiled/212written/0trusted\n"}' "$run_dir/proofs.txt" | tee "$run_dir/proof-summary.txt"
run_phase kernel 5m kernel_phase
grep -Eq '^test result: ok\. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/kernel.txt"
run_phase kernel-cli 5m kernel_cli_phase
run_phase norm 15m norm_phase
grep -Eq '^test result: ok\. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/norm.txt"
run_phase norm-cli 5m norm_cli_phase
run_phase consumer-proofs 10m consumer_proof_phase
awk '/^PASS[[:space:]]/ {modules++;compiled+=$2;trusted+=$4} END {if(modules!=1 || compiled!=11 || trusted!=0) exit 1;printf "PASS independent consumer proofs:1module/11compiled/11written/0trusted\n"}' "$run_dir/consumer-proofs.txt" | tee "$run_dir/consumer-proof-summary.txt"
run_phase chain 15m chain_phase
grep -Eq '^test result: ok\. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/chain.txt"
run_phase chain-cli 5m chain_cli_phase
run_phase chain-proofs 10m chain_proof_phase
awk '/^PASS[[:space:]]/ {modules++;compiled+=$2;trusted+=$4} END {if(modules!=1 || compiled!=11 || trusted!=0) exit 1;printf "PASS chain consumer proofs:1module/11compiled/11written/0trusted\n"}' "$run_dir/chain-proofs.txt" | tee "$run_dir/chain-proof-summary.txt"
find "$build_root" -path '*/.fingerprint/*/lib-isogeny_algos.json' -type f -print -exec sha256sum {} \; > "$run_dir/dependency-fingerprints.txt"
printf 'PASS fp-chain integration:43native/24algebra/elevenexactidentities/botholdnativeJSONcmp/40upstreammodules238compiled212written0trusted/oldkernel4+CLI/newnorm4+CLI/consumer11Lean/newchain4+boundedCLI/newchain11Lean/old50+fivejobprefixretained/whole-inputguards;unsigned\n'
