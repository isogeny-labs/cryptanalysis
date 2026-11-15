#!/usr/bin/env bash
# CT141: manual-only, bounded cold process + warmed primitive pricing. [pcc:unverified]
set -euo pipefail
base="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${1:-}" == '--self-test' ]]; then
  [[ "${CT141_BENCH_ADMITTED:-}" != yes ]] || { echo 'self-test must not have admission'; exit 65; }
  echo 'SELF-TEST: no native execution; admission remains disabled'
  exit 0
fi
[[ "${CT141_BENCH_ADMITTED:-}" == yes && "${CT126_BENCH_ADMITTED:-}" == yes ]] || {
  echo 'REFUSED: separate owner/budget admission and CT126_BENCH_ADMITTED=yes required' >&2
  exit 77
}
[[ "$#" == 1 && "$1" == /* ]] || { echo 'Usage: ct141_admitted_run.sh /absolute/new/output/dir' >&2; exit 64; }
out="$1"
[[ ! -e "$out" ]] || { echo 'REFUSED: output directory already exists' >&2; exit 65; }
[[ -d "$base/../fixed-jacobian-chain-reuse-01" ]] || { echo 'REFUSED: derivative was not materialized' >&2; exit 66; }
command -v prlimit >/dev/null && command -v timeout >/dev/null && command -v cargo >/dev/null
command -v /usr/bin/time >/dev/null || { echo 'GNU time required' >&2; exit 69; }
[[ "$(git -C "$base" hash-object src/main.rs)" == ac4146577f5019fc17674deb342eb5d9fc749715 ]] || {
  echo 'REFUSED: CT126 Rust source is not the pinned CT137 blob' >&2; exit 67;
}
[[ "$(git -C "$base" hash-object check_pair.py)" == 1caf31daadc71b30be45e8e8e46224c03c6650a2 ]] || {
  echo 'REFUSED: inherited auditor changed' >&2; exit 67;
}
mkdir -p "$out"
{
  date -u '+%FT%TZ'
  uname -a
  rustc -Vv
  cargo -V
  grep -m1 'model name' /proc/cpuinfo || true
  cat /sys/fs/cgroup/cpu.max 2>/dev/null || true
  cat /sys/fs/cgroup/memory.max 2>/dev/null || true
} > "$out/host.txt"
sha256sum "$base/src/main.rs" "$base/check_pair.py" "$base/Cargo.toml" "$base/reuse/Cargo.toml" \
  "$base/../fixed-jacobian-chain-evaluator-01/src/lib.rs" \
  "$base/../fixed-jacobian-chain-reuse-01/src/lib.rs" > "$out/source-sha256.txt"
# Build/link once per arm, outside the four cold-process timers.
timeout --signal=TERM --kill-after=10s 360s cargo build --release --manifest-path "$base/Cargo.toml" \
  > "$out/original-build.log" 2>&1
timeout --signal=TERM --kill-after=10s 360s cargo build --release --manifest-path "$base/reuse/Cargo.toml" \
  > "$out/reuse-build.log" 2>&1
original="$base/target/release/ct126-price"
reuse="$base/reuse/target/release/ct126-price-reuse"
[[ -x "$original" && -x "$reuse" ]] || { echo 'REFUSED: binaries not linked'; exit 68; }
sha256sum "$original" "$reuse" > "$out/binary-sha256.txt"
for pair in 'original:original-1' 'reuse:reuse-1' 'reuse:reuse-2' 'original:original-2'; do
  arm="${pair%%:*}"
  file="${pair#*:}"
  exe="$original"
  [[ "$arm" != reuse ]] || exe="$reuse"
  echo "$pair" >> "$out/sequence.txt"
  set +e
  /usr/bin/time -v -o "$out/$file.resources.txt" \
    timeout --signal=TERM --kill-after=10s 480s \
    prlimit --as=2147483648 -- "$exe" > "$out/$file.json" 2> "$out/$file.stderr"
  status=$?
  set -e
  printf '%s\n' "$status" > "$out/$file.exit-status.txt"
  sha256sum "$out/$file.json" "$out/$file.stderr" "$out/$file.resources.txt" \
    "$out/$file.exit-status.txt" >> "$out/outputs-sha256.txt"
  [[ "$status" == 0 ]] || { echo "ABORT: $file status=$status; preceding raw evidence retained" >&2; exit "$status"; }
  python3 -m json.tool "$out/$file.json" >/dev/null
done
python3 -S "$base/check_pair.py" --self-test > "$out/selftest-normal.json"
python3 -O -S "$base/check_pair.py" --self-test > "$out/selftest-optimized.json"
cmp "$out/selftest-normal.json" "$out/selftest-optimized.json"
mkdir "$out/audit-normal" "$out/audit-optimized"
for arm in original-1 reuse-1 reuse-2 original-2; do
  cp "$out/$arm.json" "$out/audit-normal/$arm.json"
  cp "$out/$arm.json" "$out/audit-optimized/$arm.json"
done
for name in sequence.txt host.txt; do
  cp "$out/$name" "$out/audit-normal/$name"
  cp "$out/$name" "$out/audit-optimized/$name"
done
python3 -S "$base/check_pair.py" "$out/audit-normal" > "$out/audit-normal.stdout.json"
python3 -O -S "$base/check_pair.py" "$out/audit-optimized" > "$out/audit-optimized.stdout.json"
cmp "$out/audit-normal/diagnostic.json" "$out/audit-optimized/diagnostic.json"
sha256sum "$out"/audit-{normal,optimized}/diagnostic.json "$out"/*stdout.json > "$out/audit-sha256.txt"
printf '%s\n' 'CT141 BOUNDED PRIMITIVE-PRICE DIAGNOSTIC COMPLETED [pcc:unverified]' > "$out/standing.txt"
