#!/usr/bin/env bash
# CT126: same-host ABBA evidence collection; does not authorize paid compute.
set -euo pipefail
test "${CT126_BENCH_ADMITTED:-}" = "yes" || { echo "Explicit budget/host admission required" >&2; exit 77; }
test "$#" -eq 1 || { echo "Usage: run_pair.sh /absolute/new/output/dir" >&2; exit 64; }
out="$1"; test ! -e "$out" || { echo "Refuse overwrite existing results" >&2; exit 65; }
mkdir -p "$out"
base="$(cd "$(dirname "$0")" && pwd)"
test -d "$base/../fixed-jacobian-chain-reuse-01" || { echo "Generate/validate CT125 derivative first" >&2; exit 66; }
{ uname -a; rustc -Vv; cargo -V; date -u '+%FT%TZ'; } > "$out/host.txt"
for pair in "original:original-1" "reuse:reuse-1" "reuse:reuse-2" "original:original-2"; do
  arm="${pair%%:*}"; file="${pair#*:}"
  manifest="$base/Cargo.toml"; test "$arm" != "reuse" || manifest="$base/reuse/Cargo.toml"
  echo "$arm:$file" >> "$out/sequence.txt"
  timeout 900s cargo run --release --manifest-path "$manifest" --bin "ct126-price$(test "$arm" != "reuse" || echo -reuse)" \
    > "$out/$file.json" 2> "$out/$file.stderr"
  python3 -m json.tool "$out/$file.json" >/dev/null
done
python3 "$base/check_pair.py" "$out"
