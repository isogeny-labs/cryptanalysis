#!/usr/bin/env bash
# CT129 bounded native producer run; no authorization of paid compute.
set -euo pipefail
if [[ "${CT129_BENCH_ADMITTED:-no}" != "yes" ]]; then
  echo "CT129 requires explicit budget/host admission; no job launched" >&2
  exit 77
fi
if [[ $# != 1 || "$1" != /* || -e "$1" ]]; then
  echo "Usage: CT129_BENCH_ADMITTED=yes $0 /absolute/NEW/output/path" >&2
  exit 64
fi
base="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
out="$1"
mkdir -p "$out"
manifest="$base/Cargo.toml"
{
  date -u '+%FT%TZ'
  uname -a
  rustc -Vv
  cargo -V
  sha256sum "$base/src/bin/ct129-cold-bsgs.rs" "$base/ct129_check.py" "$manifest"
} > "$out/host.txt"
# Offline build; the actual solve process is separately bounded at 900s and 2GiB.
cargo build --release --offline --manifest-path "$manifest" --bin ct129-cold-bsgs \
  > "$out/build.stdout" 2> "$out/build.stderr"
bin="$base/target/release/ct129-cold-bsgs"
sha256sum "$bin" >> "$out/host.txt"
(
  ulimit -v 2097152
  timeout 900s "$bin" > "$out/native.json" 2> "$out/native.stderr"
)
python3 -S "$base/ct129_check.py" "$out/native.json" > "$out/producer-audit.json"
python3 -O -S "$base/ct129_check.py" "$out/native.json" > "$out/producer-audit-optimized.json"
cmp -s "$out/producer-audit.json" "$out/producer-audit-optimized.json" || {
  echo "Normal/-O producer audit disagreement" >&2; exit 101;
}
echo "CT129 source/target BSGS producer audit passed; PCC still unverified"
