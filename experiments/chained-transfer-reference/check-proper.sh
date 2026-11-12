#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$study_dir" rev-parse --show-toplevel)
upstream_root=$(cd -- "${1:-$repo_root/../crypto}" && pwd)
pin=$(cat "$study_dir/proper-upstream-commit.txt")
[[ $pin =~ ^[0-9a-f]{40}$ ]] || { echo 'invalid proper source revision' >&2; exit 2; }
actual=$(git -C "$upstream_root" rev-parse HEAD)
[[ $actual == "$pin" ]] || { echo "proper source HEAD mismatch:expected $pin,found $actual" >&2; exit 2; }
upstream_study=research/chained_jacobian_transfers_20261110
identity_names=(
  quartic-duplication-identity-03 two-primary-halving-identity-03
  isogeny-cycle-norm-identity-01 isogeny-cycle-first-identity-01
  isogeny-cycle-second-identity-01 unbalanced-direct-identity-01
  unbalanced-reciprocal-identity-01 even-kernel-cubic-identity-01
  t20-common-scale-identity-01 t20-normalization-identity-01
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
assert_clean() {
  local dirty
  dirty=$(git -C "$upstream_root" status --porcelain --untracked-files=all -- "${protected_paths[@]}")
  [[ -z $dirty ]] || { echo 'proper source has modified or untracked protected inputs' >&2; exit 2; }
}
assert_clean
for required_tool in bash git grep awk timeout sha256sum cargo lean find sort xargs cmp mktemp date python3 cat wc tee; do
  command -v "$required_tool" >/dev/null || { echo "missing proper replay tool:$required_tool" >&2; exit 2; }
done
# Both the Cargo dependency and the frozen Cantor #[path] use this sibling.
dependency_root=$(cd -- "$study_dir/../../../crypto" && pwd)
[[ $dependency_root == "$upstream_root" ]] || { echo 'checker source layout does not match pinned upstream' >&2; exit 2; }
if [[ $# -ge 2 ]]; then
  run_dir=$2
  [[ ! -e $run_dir ]] || { echo 'proper output directory already exists' >&2; exit 2; }
  mkdir -- "$run_dir"
else
  run_dir=$(mktemp -d "${TMPDIR:-/tmp}/chained-proper.XXXXXXXX")
fi
run_dir=$(cd -- "$run_dir" && pwd)
build_root=$(mktemp -d "${TMPDIR:-/tmp}/chained-proper-build.XXXXXXXX")
printf '%s\n' "$build_root" > "$run_dir/build-cache-path.txt"
cd -- "$upstream_root"
git ls-files -z -- "${protected_paths[@]}" | xargs -0 sha256sum > "$run_dir/source.sha256"
consumer_study=experiments/chained-transfer-reference
(
  cd -- "$repo_root"
  {
    git ls-files -z -- "$consumer_study/src" "$consumer_study/independent-walk" "$consumer_study/*.sha256" "$consumer_study/*upstream*" "$consumer_study/check*.sh" "$consumer_study/*PROTOCOL*.md" .github/workflows/chained-transfer-reference.yml
    printf '%s\0' "$consumer_study/check-proper.sh" "$consumer_study/proper-upstream-commit.txt" "$consumer_study/PROPER_T20_REPLAY_PROTOCOL.md" "$consumer_study/PROPER_T20_BUILD_CACHE_NOTES.md" .github/workflows/chained-transfer-reference.yml
    find "$consumer_study/kernel-checker" -type f ! -path '*/target/*' -print0
  } | sort -zu | xargs -0 sha256sum
) > "$run_dir/consumer.sha256"
printf 'Pinned proper source %s\n' "$pin"
export CARGO_TERM_COLOR=never
export RUSTUP_TOOLCHAIN=1.99.1
cargo --version
lean --version
export CHAINED_EVEN_KERNEL_CERTIFICATE_OUT="$run_dir/kernel.json"
export CHAINED_T20_GEOMETRY_OUT="$run_dir/geometry.json"
(
  cd "$upstream_study/successor-preflight"
  export CARGO_TARGET_DIR="$build_root/successor"
  sha256sum --check reference.sha256
  sha256sum --check legacy.sha256
  cargo fmt -- --check
  cargo clippy --all-targets --offline --locked -- -D warnings
  timeout 15m cargo test --release --offline --locked -- --nocapture
  cmp "$run_dir/kernel.json" ../evidence/kernel-full-03/kernel-certificate.json
  cmp "$run_dir/geometry.json" ../evidence/t20-full-02/geometry-certificate.json
) 2>&1 | tee "$run_dir/standalone.txt"
grep -Eq '^test result: ok\. 41 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/standalone.txt"
(
  cd "$upstream_study/algebra-certificates"
  export CARGO_TARGET_DIR="$build_root/algebra"
  sha256sum --check reference.sha256
  cargo fmt -- --check
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  timeout 15m cargo test --release --offline --locked -- --nocapture
  outputs=()
  for i in "${!identity_names[@]}"; do outputs+=("$run_dir/identity-$i.json"); done
  cargo run --release --offline --locked -- "${outputs[@]}"
  for i in "${!identity_names[@]}"; do cmp "${outputs[i]}" "../evidence/${identity_names[i]}.json"; done
) 2>&1 | tee "$run_dir/algebra.txt"
grep -Eq '^test result: ok\. 23 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/algebra.txt"
grep -nE '^(theorem|lemma) ' "$upstream_study"/lean/*.lean > "$run_dir/written-declarations.txt"
[[ $(wc -l < "$run_dir/written-declarations.txt") -eq 198 ]]
timeout 10m bash tools/lean/proof-gate.sh --out "$run_dir/proofs" "$upstream_study"/lean/*.lean 2>&1 | tee "$run_dir/proof-gate.txt"
awk '/^PASS[[:space:]]/ {modules++;compiled+=$2;trusted+=$4} END {if(modules!=39 || compiled!=224 || trusted!=0) exit 1;printf "PASS proper proof modules:%d compiled-theorems:%d trusted-native:%d written-declarations:198\n",modules,compiled,trusted}' "$run_dir/proof-gate.txt" | tee "$run_dir/proof-summary.txt"
(
  cd -- "$study_dir/kernel-checker"
  # Same isolated run,source,toolchain and dependency fingerprint as native.
  export CARGO_TARGET_DIR="$build_root/successor"
  cargo fmt -- --check
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  timeout 5m cargo test --release --offline --locked -- --nocapture
  timeout 5m cargo run --release --offline --locked -- "$run_dir/kernel.json"
) 2>&1 | tee "$run_dir/checker.txt"
grep -Eq '^test result: ok\. 4 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/checker.txt"
sha256sum --check "$run_dir/source.sha256" > "$run_dir/after.txt"
(cd -- "$repo_root" && sha256sum --check "$run_dir/consumer.sha256") > "$run_dir/consumer-after.txt"
assert_clean
printf 'PASS proper integration:41standalone/23algebra/tenexactidentitycertificates/bothnativeJSONcmp/39proofmodules224compiled198written0trusted/fourindependentcheckertests+CLI;allupstream+consumerinputsunchanged;unsigned\n'
