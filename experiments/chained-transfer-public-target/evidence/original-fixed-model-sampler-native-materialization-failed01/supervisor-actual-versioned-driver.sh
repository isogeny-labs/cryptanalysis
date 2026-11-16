#!/usr/bin/env bash
set -u
[[ $# == 3 ]] || exit 2
expected=$1
out=$(realpath -m "$2")
build=$(realpath -m "$3")
pkg=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$pkg" rev-parse --show-toplevel)
cd "$repo" || exit 2
[[ ! -e $out && $(git rev-parse HEAD) == "$expected" && -z $(git status --porcelain) ]] || exit 2
mkdir "$out"
trap 'status=$?;printf "%s\n" "$status" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$pkg/run-native-01.sh" "$out/original-command.sh"
phase(){ local name=$1 want=$2;shift 2;"$@" > "$out/$name.txt" 2>&1;local status=$?;printf '%s\n' "$status" > "$out/$name.exit";printf '%s %s %s\n' "$name" "$want" "$status" >> "$out/phases.txt";[[ $status == "$want" ]]; }
phase immediate-original-gate 0 bash scripts/checkpoint.sh gate || exit 1
phase runtime-custody 0 python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
phase initial-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
test=$(cat "$out/chain-actual-path.txt")
auditor=$(cat "$out/auditor-actual-path.txt")
phase native 0 bash -c 'ulimit -v 2097152;exec timeout 900 "$1" --nocapture --test-threads=1' _ "$test" || exit 1
phase freeze-whole 0 timeout 120 "$auditor" --freeze "$out/native.txt" "$out/all-whole-expected.json" || exit 1
phase compare-whole 0 timeout 120 "$auditor" --compare "$out/all-whole-expected.json" "$out/native.txt" "$out/all-whole-compared.json" || exit 1
for tag in N4_ORIGINAL_FIXED_SAMPLER_SETUP N4_ORIGINAL_FIXED_SAMPLER_PROVENANCE N4_ORIGINAL_FIXED_SAMPLER_INPUT N4_ORIGINAL_FIXED_SAMPLER_SCALARS N4_ORIGINAL_FIXED_SAMPLER_ATTEMPT N4_ORIGINAL_FIXED_SAMPLER_CASE N4_ORIGINAL_FIXED_SAMPLER_TARGET N4_ORIGINAL_FIXED_SAMPLER_SCOPE;do
 # Preserve the complete omission input losslessly, with a checked producer
 # pipeline and whole XZ integrity check before the unchanged Rust auditor.
 omitted=$out/$tag-entire-actual-records-omitted.txt.xz
 phase "$tag-materialize-whole-XZ" 0 bash -o pipefail -c 'sed "/$1 /d" "$2" | xz -c > "$3"' _ "$tag" "$out/native.txt" "$omitted" || exit 1
 phase "$tag-whole-XZ-CRC" 0 xz --test "$omitted" || exit 1
 phase "$tag-omission" 101 bash -c 'exec timeout 120 "$1" --compare "$2" <(xz -dc "$3") "$4"' _ "$auditor" "$out/all-whole-expected.json" "$omitted" "$out/$tag-must-not-accept.json" || exit 1
 [[ ! -e $out/$tag-must-not-accept.json ]] || exit 1
done
phase final-test-bytes 0 cmp "$test" "$out/actual-before-native-chain.bin" || exit 1
phase final-auditor-bytes 0 cmp "$auditor" "$out/actual-before-native-auditor.bin" || exit 1
phase final-prior 0 sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
exit 0
