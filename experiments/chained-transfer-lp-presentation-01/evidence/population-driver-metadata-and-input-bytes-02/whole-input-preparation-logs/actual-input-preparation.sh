#!/usr/bin/env bash
# Complete original file copying/decompression/SHA checks only, no math.
set -euo pipefail
[[ $# == 3 ]] || exit 2
source_dir=$(realpath -e "$1")
capture=$(realpath -e "$2")
out=$(realpath -m "$3")
pkg=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
[[ ! -e $out ]]
mkdir "$out"
cp "$pkg/historical-whole-fixture-pins-01.json" "$out/entire-original-input-pins.json"
cp "$0" "$out/actual-input-preparation.sh"
phase() {
 local name=$1 code;shift
 set +e
 (ulimit -v 2097152;exec timeout --signal=TERM --kill-after=5s 120 "$@") > "$out/$name.stdout" 2> "$out/$name.stderr"
 code=$?;set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/all-actual-byte-phases.txt"
 return "$code"
}
finish() { local code=$?;trap - EXIT;printf '%s\n' "$code" > "$out/original.exit";exit "$code"; }
trap finish EXIT
mapfile -t names < <(jq --raw-output '.fixtures[].name' "$out/entire-original-input-pins.json")
[[ ${#names[@]} == 6 ]]
for name in "${names[@]}";do
 [[ $name =~ ^[a-z0-9-]+\.(json|jsonl)\.xz$ && -f $source_dir/$name && ! -L $source_dir/$name ]]
 phase "copy-$name" cp "$source_dir/$name" "$out/$name"
 phase "decode-$name" bash -c 'exec xz --decompress --stdout -- "$1" > "$2"' _ "$out/$name" "$out/${name%.xz}"
done
phase copy-entire-original-passive-acceptance cp "$capture" "$out/historical-passive-acceptance-01.json"
jq --raw-output '.fixtures[]|"\(.sha256)  \(.name)\n\(.decoded_sha256)  \(.name|sub("\\.xz$";""))"' \
 "$out/entire-original-input-pins.json" > "$out/all-entire-original-files.sha256"
jq --raw-output '.passive_acceptance.sha256+"  historical-passive-acceptance-01.json"' \
 "$out/entire-original-input-pins.json" >> "$out/all-entire-original-files.sha256"
phase all-entire-input-SHA-pins bash -c 'cd "$1" && exec sha256sum --check all-entire-original-files.sha256' _ "$out"
for name in "${names[@]}";do
 compressed=$(jq --raw-output --arg name "$name" '.fixtures[]|select(.name==$name)|.compressed_bytes' "$out/entire-original-input-pins.json")
 decoded=$(jq --raw-output --arg name "$name" '.fixtures[]|select(.name==$name)|.decoded_bytes' "$out/entire-original-input-pins.json")
 [[ $(wc -c < "$out/$name") == "$compressed" && $(wc -c < "$out/${name%.xz}") == "$decoded" ]]
done
[[ $(wc -c < "$out/historical-passive-acceptance-01.json") == 19686 ]]
