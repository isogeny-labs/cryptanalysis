#!/usr/bin/env bash
# Thin native command card. Do not change parameters after inspecting outcomes.
set -euo pipefail
if [ "$#" -ne 2 ]; then
  echo 'usage: bash run.sh /path/to/aes-discover NEW-OUTPUT-DIRECTORY' >&2
  exit 2
fi
binary=$(realpath -- "$1")
output=$(realpath -m -- "$2")
study=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
root=$(git -C "$study" rev-parse --show-toplevel)
test -x "$binary"
mkdir -- "$output"
status=0
trap 'status=$?; printf "%s\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$status" > "$output/process-exit.tsv"' EXIT
sha256sum -- "$binary" > "$output/binary-sha256.txt"
find "$root/tools/aes-discover/src" "$root/tools/aes-discover/tests" -type f -print0 |
  sort -z | xargs -0 sha256sum > "$output/source-sha256.txt"
sha256sum "$root/tools/aes-discover/Cargo.toml" "$root/tools/aes-discover/Cargo.lock" \
  "$study/README.md" "$study/run.sh" > "$output/protocol-sha256.txt"
{
  date -u +%Y-%m-%dT%H:%M:%SZ
  uname -srm
  "$binary" --version
  openssl version
  git -C "$root" rev-parse HEAD
  git -C "$root" status --short
  if command -v rustc >/dev/null 2>&1; then rustc --version; fi
  if [ -r /proc/cpuinfo ]; then awk '/model name/ {print; exit}' /proc/cpuinfo; fi
} > "$output/environment.txt"
run() {
  local name=$1
  shift
  { printf '%s' "$name"; printf '\t%q' "$binary" "$@" --out "$output/$name.json"; printf '\n'; } >> "$output/commands.tsv"
  local rc=0
  "$binary" "$@" --out "$output/$name.json" > "$output/$name.stdout" 2> "$output/$name.stderr" || rc=$?
  printf '%s\t%s\t%s\n' "$name" "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$output/status.tsv"
  return "$rc"
}
family() {
  local name=$1 bits=$2 rounds=$3 oracle=$4 seed=$5 holdout=$6 final_mix=$7
  local mix_args=()
  if [ "$final_mix" = true ]; then mix_args+=(--final-mix); fi
  run "$name-discovery" discover --key-bits "$bits" --rounds "$rounds" "${mix_args[@]}" \
    --oracle "$oracle" --seed "$seed" --validation-seed "$holdout" --keys 2 --samples 256 \
    --candidates 16 --top 2 --validation-samples 4096 --validation-keys 8 --alpha 0.0005
  local spec_hash
  spec_hash=$(sha256sum "$output/$name-discovery.json" | cut -d ' ' -f1)
  run "$name-validation" validate --spec "$output/$name-discovery.json" --expect-sha256 "$spec_hash"
}
run tables tables
family aes128-r1 128 1 aes 610171 710171 false
family aes128-r2 128 2 aes 610172 710172 false
family aes128-r3 128 3 aes 610173 710173 false
family aes128-r4 128 4 aes 610174 710174 false
family aes128-r6 128 6 aes 610176 710176 false
family aes128-r7 128 7 aes 610177 710177 false
family aes128-r10 128 10 aes 610180 710180 false
family aes128-r3-mix 128 3 aes 610183 710183 true
family aes192-r12 192 12 aes 610192 710192 false
family aes256-r14 256 14 aes 610256 710256 false
family prp-r1 128 1 random 610301 710301 false
family prp-r10 128 10 random 610310 710310 false
for rounds in 1 2 3 4; do
  run "trail-r$rounds" trail --rounds "$rounds" --final-mix --beam 8 --branch 4
done
run integral128-r3 integral --key-bits 128 --rounds 3 --seed 810173 --keys 8 --structures 2
run integral128-r3-mix integral --key-bits 128 --rounds 3 --final-mix --seed 810183 --keys 8 --structures 2
run integral128-r4-mix integral --key-bits 128 --rounds 4 --final-mix --seed 810184 --keys 8 --structures 2
run integral192-r3-mix integral --key-bits 192 --rounds 3 --final-mix --seed 810193 --keys 8 --structures 2
run integral256-r3-mix integral --key-bits 256 --rounds 3 --final-mix --seed 810253 --keys 8 --structures 2
run quartets quartets --seed 910171 --trials 65536
run schedule schedule --seed 910172 --keys 8 --key-bit 0
run boomerang-r1 boomerang --rounds 1 --seed 910173 --samples 4096 \
  --alpha 01000000000000000000000000000000 --delta 01000000000000000000000000000000
for split in train validation test; do
  { printf 'dataset-%s' "$split"; printf '\t%q' "$binary" dataset --rounds 3 --seed 910174 --keys 2 --samples 64 --split "$split" --out "$output/dataset-$split.jsonl"; printf '\n'; } >> "$output/commands.tsv"
  rc=0
  "$binary" dataset --rounds 3 --seed 910174 --keys 2 --samples 64 --split "$split" \
    --out "$output/dataset-$split.jsonl" > "$output/dataset-$split.stdout" 2> "$output/dataset-$split.stderr" || rc=$?
  printf 'dataset-%s\t%s\t%s\n' "$split" "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$output/status.tsv"
  test "$rc" -eq 0
done
spec_hash=$(sha256sum "$output/aes128-r1-discovery.json" | cut -d ' ' -f1)
run replay-aes128-r1 validate --spec "$output/aes128-r1-discovery.json" --expect-sha256 "$spec_hash"
cmp "$output/aes128-r1-validation.json" "$output/replay-aes128-r1.json"
printf 'byte-identical validation replay\n' > "$output/replay-verdict.txt"
find "$output" -type f ! -name output-sha256.txt ! -name process-exit.tsv -print0 |
  sort -z | xargs -0 sha256sum > "$output/output-sha256.txt"
echo "Completed fixed AES laboratory card: $output"
