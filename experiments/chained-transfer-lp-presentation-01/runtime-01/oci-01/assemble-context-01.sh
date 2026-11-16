#!/usr/bin/env bash
# File custody only: no Docker, AWS, compiler or science-tool invocation.
set -euo pipefail
[[ $# == 7 ]] || exit 2
repo=$(realpath -e "$1")
snapshot=$(realpath -e "$2")
capsule=$(realpath -e "$3")
pure=$(realpath -e "$4")
pure_archive=$(realpath -e "$5")
fixtures=$(realpath -e "$6")
out=$(realpath -m "$7")
component=experiments/chained-transfer-lp-presentation-01
recipe=$repo/$component/runtime-01/oci-01
[[ ! -e $out && $out != "$repo" && $out != "$repo/"* ]]
mkdir "$out" "$out/context" "$out/context/recipe" "$out/context/fixture-source"
cd "$repo"
cp "$0" "$out/entire-actual-assembly-command.sh"
date -u +%FT%TZ > "$out/start.txt"
finish(){ local code=$?;trap - EXIT;printf '%s\n' "$code" > "$out/original.exit";date -u +%FT%TZ > "$out/finish.txt";exit "$code"; }
trap finish EXIT
phase(){
 local name=$1 code;shift
 jq --null-input --args '$ARGS.positional' -- "$@" > "$out/$name.argv.json"
 set +e
 (ulimit -v 2097152;exec timeout --signal=TERM --kill-after=5s 120 "$@") > "$out/$name.stdout" 2> "$out/$name.stderr"
 code=$?;set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/all-actual-byte-phases.txt"
 return "$code"
}
check_file(){
 local sha=$1 bytes=$2 path=$3
 [[ -f $path && ! -L $path && $(wc -c < "$path") == "$bytes" ]]
 printf '%s  %s\n' "$sha" "$path" | sha256sum --check
}
phase original1605-guard sha256sum --check experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256
phase pure50-guard sha256sum --check "$component/historical-01/source-01.sha256"
phase population12-guard sha256sum --check "$component/population-01/source-01.sha256"
phase OCI-recipe-source-guard sha256sum --check "$component/runtime-01/oci-01/source-01.sha256"
check_file b441b4375616df79da9b879dd3d1fc04b8f31ae81b0d2c68c98833c3077fb7b8 39331840 "$snapshot/entire-guarded-file-snapshot.tar" > "$out/whole-snapshot-check.txt"
check_file 4972d58159bd44cfcb39daf29d8e3813c3c6ead85d928b281e022d1c15ec4de3 340729140 "$capsule/entire-original-artifact.zip" > "$out/whole-original-CI-check.txt"
check_file be85b978a90d873bcb91ac25f3faddc13f464a6052517ae19c422e67ed4ec181 53419171 "$pure_archive" > "$out/whole-pure-CI-check.txt"
phase all56-original-selected-members bash -c 'cd "$1" && exec sha256sum --check "$2"' _ \
 "$capsule/entire-original-members-used" "$repo/$component/runtime-01/selected-members-01.sha256"
phase all3-actual-pure-build-pins bash -c 'cd "$1" && exec sha256sum --check binary-pins.sha256' _ "$pure"
phase actual-pure-compiler-source jq --exit-status \
 '.source_revision=="2c44ee2ebb0be9b5fc0375818cc18924cef82c41" and .scope=="new pure source compilation; original baseline reuse separate"' "$pure/build-receipt.json"
for pair in 'extract_public 17e5d2c6f406482e9f0e2b43836f5ca81479d5f383f2da0475dd22a145c2940d' \
 'historical_certificates 08b6b61e8ab6db5cf77300ee052a990a822f4d82532a0b0785906a8d6c31e6f2' \
 'lp-post-character f8db15c1e3e6710e98f11991dba32efb8bd9e702e90e4093c02f8def594f08fc';do
 read -r name sha <<< "$pair"
 printf '%s  %s\n' "$sha" "$pure/$name" | sha256sum --check >> "$out/published-pure-binary-check.txt"
done
# Link immutable complete data to avoid duplicating the two whole archives and
# prepared-engine bytes. Only fresh recipe/metadata/fixture copies are writable.
for path in "$snapshot/entire-guarded-file-snapshot.tar" "$capsule" "$pure" "$pure_archive";do
 [[ $(stat --format=%d "$path") == "$(stat --format=%d "$out")" ]]
done
phase link-whole-original-capsule cp --archive --link "$capsule" "$out/context/baseline"
phase link-whole-pure-build cp --archive --link "$pure" "$out/context/pure-build"
phase link-whole-pure-CI ln "$pure_archive" "$out/context/entire-pure-CI-artifact.zip"
phase link-whole-guarded-source ln "$snapshot/entire-guarded-file-snapshot.tar" "$out/context/entire-guarded-file-snapshot.tar"
pins=$repo/$component/historical-whole-fixture-pins-01.json
mapfile -t names < <(jq --raw-output '.fixtures[].name' "$pins")
[[ ${#names[@]} == 6 ]]
for name in "${names[@]}";do
 [[ $name =~ ^[a-z0-9-]+\.(json|jsonl)\.xz$ && -f $fixtures/$name && ! -L $fixtures/$name ]]
 sha=$(jq --raw-output --arg name "$name" '.fixtures[]|select(.name==$name)|.sha256' "$pins")
 bytes=$(jq --raw-output --arg name "$name" '.fixtures[]|select(.name==$name)|.compressed_bytes' "$pins")
 check_file "$sha" "$bytes" "$fixtures/$name" >> "$out/all-whole-compressed-fixture-checks.txt"
 cp --preserve=mode,timestamps "$fixtures/$name" "$out/context/fixture-source/$name"
 cmp "$fixtures/$name" "$out/context/fixture-source/$name"
done
capture=$repo/experiments/chained-transfer-public-target/ci_original_relation/historical-passive-acceptance-01.json
check_file 1eef55e7fa9dd799e77967e9425e6cd3400dfb51f469dade0d6e99d4f97130a2 19686 "$capture" >> "$out/all-whole-compressed-fixture-checks.txt"
cp "$capture" "$out/context/fixture-source/historical-passive-acceptance-01.json"
cp "$recipe/Dockerfile" "$out/context/Dockerfile"
cp "$recipe/assemble-context-01.sh" "$out/context/recipe/assemble-context-01.sh"
cp "$recipe/source-01.sha256" "$out/context/recipe/OCI-source-01.sha256"
cp "$pins" "$out/context/recipe/historical-whole-fixture-pins-01.json"
cp "$repo/$component/runtime-01/manifest-01.json" "$repo/$component/runtime-01/selected-members-01.sha256" "$out/context/recipe/"
git rev-parse HEAD > "$out/actual-recipe-checkout-head.txt"
git status --porcelain --untracked-files=all > "$out/entire-actual-recipe-checkout-status.txt"
cp "$out/entire-actual-recipe-checkout-status.txt" "$out/context/recipe/entire-actual-recipe-checkout-status.txt"
jq --null-input --arg checkout "$(cat "$out/actual-recipe-checkout-head.txt")" \
 --arg dockerfile_sha "$(sha256sum "$out/context/Dockerfile" | cut -d ' ' -f1)" \
 '{actual_recipe_checkout_head:$checkout,actual_Dockerfile_sha256:$dockerfile_sha,
   pure_compiler_source:"2c44ee2ebb0be9b5fc0375818cc18924cef82c41",
   original_baseline_source:"b7b91903888ffa9dea85e643e5a86e828767e7c8",
   original_baseline_engine_source:"3d49af7f3d0a28e76b79e4825c9d2324e85853d2",
   original_guarded_snapshot_Root_source:"44a3db385da4c4fb044aaa2008bb7af54e5fc8a4",
   base_image:"debian:bookworm-slim@sha256:c67e92c8099ba22853ab4cfda7cfb494d253d6012ca82dee98ba8976772af018",
   scope:"complete packaging bytes only; actual recipe status/command retained separately; publication, clean runtime Git, checkpoint, built OCI/ABI and admitted Job/Pod remain separate"}' > "$out/context/build-info.json"
phase all-context-byte-inventory bash -euo pipefail -c \
 'cd "$1" && rg --files --hidden --no-ignore -0 | LC_ALL=C sort -z | xargs -0 sha256sum > "$2"' _ \
 "$out/context" "$out/entire-context-files.sha256"
phase all-context-byte-check bash -c 'cd "$1" && exec sha256sum --check "$2"' _ \
 "$out/context" "$out/entire-context-files.sha256"
[[ $(wc -l < "$out/entire-context-files.sha256") -ge 300 ]]
# Recheck the copied/linked destinations against the original external pins,
# separately from the freshly generated whole-context inventory.
check_file b441b4375616df79da9b879dd3d1fc04b8f31ae81b0d2c68c98833c3077fb7b8 39331840 "$out/context/entire-guarded-file-snapshot.tar" > "$out/final-whole-snapshot-check.txt"
check_file 4972d58159bd44cfcb39daf29d8e3813c3c6ead85d928b281e022d1c15ec4de3 340729140 "$out/context/baseline/entire-original-artifact.zip" > "$out/final-whole-original-CI-check.txt"
check_file be85b978a90d873bcb91ac25f3faddc13f464a6052517ae19c422e67ed4ec181 53419171 "$out/context/entire-pure-CI-artifact.zip" > "$out/final-whole-pure-CI-check.txt"
phase final-pure-native-pins bash -c 'cd "$1" && exec sha256sum --check binary-pins.sha256' _ "$out/context/pure-build"
phase final-original-selected-pins bash -c 'cd "$1" && exec sha256sum --check "$2"' _ \
 "$out/context/baseline/entire-original-members-used" "$repo/$component/runtime-01/selected-members-01.sha256"
for pair in 'original-rank-replayer c4b678fcee7305e8509e6598e286ae67e5bb91a4e0b629511734f2d22e6c99da' \
 'original-character-auditor f7bf2e8a1c2b225dae8f383941dbb4bda3668a5deaa5ad684fc770515109c586';do
 read -r name sha <<< "$pair"
 printf '%s  %s\n' "$sha" "$out/context/baseline/native/$name" | sha256sum --check >> "$out/final-original-native-check.txt"
done
for name in "${names[@]}";do
 sha=$(jq --raw-output --arg name "$name" '.fixtures[]|select(.name==$name)|.sha256' "$pins")
 bytes=$(jq --raw-output --arg name "$name" '.fixtures[]|select(.name==$name)|.compressed_bytes' "$pins")
 check_file "$sha" "$bytes" "$out/context/fixture-source/$name" >> "$out/final-whole-compressed-fixture-checks.txt"
done
check_file 1eef55e7fa9dd799e77967e9425e6cd3400dfb51f469dade0d6e99d4f97130a2 19686 "$out/context/fixture-source/historical-passive-acceptance-01.json" >> "$out/final-whole-compressed-fixture-checks.txt"
phase final-original1605-guard sha256sum --check experiments/chained-transfer-relation-diagnostics-02/reference-02.sha256
phase final-pure50-guard sha256sum --check "$component/historical-01/source-01.sha256"
phase final-population12-guard sha256sum --check "$component/population-01/source-01.sha256"
phase final-OCI-recipe-source-guard sha256sum --check "$component/runtime-01/oci-01/source-01.sha256"
printf '%s\n' 'No Docker/AWS/compiler/native science process invoked. All context files and whole original/pure CI archives retained. Recipe publication, runtime checkout/preparation, package/ABI qualification, actual image digest, paid admission and actual Job/Pod execution remain independent.' > "$out/scope.txt"
