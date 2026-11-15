#!/usr/bin/env bash
# Thin source custody only. Arithmetic, controls and replay are native Rust.
set -euo pipefail
[[ $# == 3 ]] || exit 2
audit=$(cd -- "$(dirname -- "$0")" && pwd -P)
consumer=$(cd -- "$1" && pwd -P)
producer=$(cd -- "$2" && pwd -P)
out=$(realpath -m "$3")
[[ ! -e $out ]] || { echo 'fresh destination required' >&2; exit 2; }
case "$out/" in "$consumer/"*|"$producer/"*) exit 2;; esac
c=21afb40f425f89774fe3eaf77695f5f30342a186
p=3d49af7f3d0a28e76b79e4825c9d2324e85853d2
study=experiments/chained-transfer-public-target
reference=$study/ci_norm_sampling/reference-01.sha256
mkdir -p "$out/original-layout/cryptanalysis" "$out/original-layout/crypto"
git -C "$consumer" show "$c:$reference" > "$out/reference-01.sha256"
while read -r digest relative; do
  [[ $digest =~ ^[0-9a-f]{64}$ && $relative != *' '* && $relative != /* ]] || exit 2
  case "$relative" in
    ../crypto/*) repo=$producer; pin=$p; path=${relative#../crypto/}; destination=$out/original-layout/crypto/$path;;
    ../*|*../*) exit 2;;
    *) repo=$consumer; pin=$c; path=$relative; destination=$out/original-layout/cryptanalysis/$path;;
  esac
  mkdir -p "$(dirname "$destination")"
  git -C "$repo" show "$pin:$path" > "$destination"
  [[ $(sha256sum "$destination" | cut -d ' ' -f 1) == "$digest" ]] || exit 2
done < "$out/reference-01.sha256"
[[ $(wc -l < "$out/reference-01.sha256") == 784 ]] || exit 2
mkdir -p "$out/original-layout/cryptanalysis/$(dirname "$reference")"
cp "$out/reference-01.sha256" "$out/original-layout/cryptanalysis/$reference"
(cd "$out/original-layout/cryptanalysis" && sha256sum --check "$reference") > "$out/original-784-check.txt"
(cd "$out/original-layout" && find . -type f -print0 | sort -z | xargs -0 sha256sum) > "$out/original-785.sha256"
[[ $(wc -l < "$out/original-785.sha256") == 785 ]] || exit 2
cp -a "$out/original-layout" "$out/derived-layout"
cp -a "$audit/taps" "$out/derived-layout/n4-arithmetic-taps"
cp "$audit/controls.rs" "$out/derived-layout/arithmetic-controls.rs"
cp "$audit/scalar-insertions.json" "$out/derived-layout/scalar-insertions.json"
(cd "$out/derived-layout" && patch -p1 --batch --fuzz=0 < "$audit/literal-hooks.patch") > "$out/patch.txt"
(cd "$out/original-layout" && sha256sum --check "$out/original-785.sha256") > "$out/original-final-check.txt"
printf '%s\n' "$c" > "$out/consumer-pin.txt"
printf '%s\n' "$p" > "$out/producer-pin.txt"
echo 'Materialized and checked all785 original Git blobs; derivative hooks applied with zero fuzz.'
