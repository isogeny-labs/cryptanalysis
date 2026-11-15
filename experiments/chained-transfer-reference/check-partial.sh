#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$study_dir" rev-parse --show-toplevel)
upstream_root=$(cd -- "${1:-$repo_root/../crypto-partial}" && pwd)
pin=$(cat "$study_dir/partial-upstream-commit.txt")
[[ $pin =~ ^[0-9a-f]{40}$ ]] || { echo 'invalid partial source revision' >&2; exit 2; }
actual=$(git -C "$upstream_root" rev-parse HEAD)
[[ $actual == "$pin" ]] || { echo "partial source HEAD mismatch:expected $pin,found $actual" >&2; exit 2; }
upstream_study=research/chained_jacobian_transfers_20261110
protected_paths=(
  "$upstream_study/successor-preflight" "$upstream_study/algebra-certificates"
  "$upstream_study/lean" "$upstream_study/evidence/quartic-duplication-identity-03.json"
  "$upstream_study/evidence/two-primary-halving-identity-03.json"
  "$upstream_study/evidence/isogeny-cycle-norm-identity-01.json"
  "$upstream_study/evidence/isogeny-cycle-first-identity-01.json"
  "$upstream_study/evidence/isogeny-cycle-second-identity-01.json"
  "$upstream_study/evidence/unbalanced-direct-identity-01.json"
  "$upstream_study/evidence/unbalanced-reciprocal-identity-01.json"
  isogeny_algos src/cryptanalysis/jv_cover.rs src/cryptanalysis/identity_certificate.rs
  src/hash/sha256.rs tools/lean
  docs/identity-certificates/schoenhage-10mult.json
)
assert_clean() {
  local dirty
  dirty=$(git -C "$upstream_root" status --porcelain --untracked-files=all -- "${protected_paths[@]}")
  [[ -z $dirty ]] || { echo 'partial source has modified or untracked protected inputs' >&2; exit 2; }
}
assert_clean
for required_tool in grep awk timeout sha256sum cargo lean; do
  command -v "$required_tool" >/dev/null || { echo "missing partial replay tool:$required_tool" >&2; exit 2; }
done
if [[ $# -ge 2 ]]; then
  run_dir=$2
  [[ ! -e $run_dir ]] || { echo 'partial output directory already exists' >&2; exit 2; }
  mkdir -- "$run_dir"
else
  run_dir=$(mktemp -d "${TMPDIR:-/tmp}/chained-partial.XXXXXXXX")
fi
run_dir=$(cd -- "$run_dir" && pwd)
cd -- "$upstream_root"
git ls-files -z -- "${protected_paths[@]}" | xargs -0 sha256sum > "$run_dir/source.sha256"
printf 'Pinned partial source %s\n' "$pin"
export CARGO_TERM_COLOR=never
export RUSTUP_TOOLCHAIN=1.99.1
cargo --version
lean --version
(
  cd "$upstream_study/successor-preflight"
  sha256sum --check reference.sha256
  sha256sum --check legacy.sha256
  cargo fmt -- --check
  cargo clippy --all-targets --offline --locked -- -D warnings
  timeout 15m cargo test --release --offline --locked -- --nocapture
) 2>&1 | tee "$run_dir/standalone.txt"
grep -Eq '^test result: ok\. 35 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/standalone.txt"
(
  cd "$upstream_study/algebra-certificates"
  sha256sum --check reference.sha256
  cargo fmt -- --check
  cargo fetch --locked
  cargo clippy --all-targets --offline --locked -- -D warnings
  timeout 15m cargo test --release --offline --locked -- --nocapture
  cargo run --release --offline --locked -- "$run_dir/duplication.json" "$run_dir/halving.json" "$run_dir/cycle-norm.json" "$run_dir/cycle-first.json" "$run_dir/cycle-second.json" "$run_dir/unbalanced-direct.json" "$run_dir/unbalanced-reciprocal.json"
  cmp "$run_dir/duplication.json" ../evidence/quartic-duplication-identity-03.json
  cmp "$run_dir/halving.json" ../evidence/two-primary-halving-identity-03.json
  cmp "$run_dir/cycle-norm.json" ../evidence/isogeny-cycle-norm-identity-01.json
  cmp "$run_dir/cycle-first.json" ../evidence/isogeny-cycle-first-identity-01.json
  cmp "$run_dir/cycle-second.json" ../evidence/isogeny-cycle-second-identity-01.json
  cmp "$run_dir/unbalanced-direct.json" ../evidence/unbalanced-direct-identity-01.json
  cmp "$run_dir/unbalanced-reciprocal.json" ../evidence/unbalanced-reciprocal-identity-01.json
) 2>&1 | tee "$run_dir/algebra.txt"
grep -Eq '^test result: ok\. 23 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$run_dir/algebra.txt"
grep -nE '^(theorem|lemma) ' "$upstream_study"/lean/*.lean > "$run_dir/written-declarations.txt"
[[ $(wc -l < "$run_dir/written-declarations.txt") -eq 177 ]]
timeout 10m bash tools/lean/proof-gate.sh --out "$run_dir/proofs" "$upstream_study"/lean/*.lean 2>&1 | tee "$run_dir/proof-gate.txt"
awk '/^PASS[[:space:]]/ {modules++;compiled+=$2;trusted+=$4} END {if(modules!=35 || compiled!=203 || trusted!=0) exit 1;printf "PASS partial proof modules:%d compiled-theorems:%d trusted-native:%d written-declarations:177\n",modules,compiled,trusted}' "$run_dir/proof-gate.txt" | tee "$run_dir/proof-summary.txt"
sha256sum --check "$run_dir/source.sha256" > "$run_dir/after.txt"
assert_clean
printf 'PASS partial integration:35standalone/23algebra/35proofmodules/177written/seven exact certificates;source unchanged;scientific standing unsigned\n'
