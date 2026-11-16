#!/usr/bin/env bash
# Compiler/byte custody only; execute no resulting scientific binary. This
# source can be used by admitted CI/image builds; it launches neither itself.
set -euo pipefail
[[ $# == 3 ]] || exit 2
repo=$(realpath -e "$1")
expected=$2
out=$(realpath -m "$3")
component=experiments/chained-transfer-lp-presentation-01
pkg=$repo/$component
[[ $expected =~ ^[0-9a-f]{40}$ && ! -e $out && $out != "$repo" && $out != "$repo/"* ]]
[[ $(git -C "$repo" rev-parse HEAD) == "$expected" ]]
[[ -z $(git -C "$repo" status --porcelain --untracked-files=all) ]]
mkdir "$out"
cd "$repo"
cp "$0" "$out/actual-build-command.sh"
export RUSTUP_TOOLCHAIN=1.99.1 CARGO_BUILD_JOBS=1 CARGO_INCREMENTAL=0
export CARGO_TARGET_DIR=$out/entire-compiler-target
phase() {
 local name=$1 code;shift
 jq --null-input --args '$ARGS.positional' -- "$@" > "$out/$name.argv.json"
 set +e
 (ulimit -v 2097152;exec timeout --signal=TERM --kill-after=5s 120 "$@") > "$out/$name.stdout" 2> "$out/$name.stderr"
 code=$?;set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/all-actual-build-phases.txt"
 return "$code"
}
finish() {
 local code=$?;trap - EXIT
 printf '%s\n' "$code" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$code"
}
trap finish EXIT
date -u +%FT%TZ > "$out/start.txt"
phase initial-50-source-guard sha256sum --check "$component/historical-01/source-01.sha256"
phase initial-population-source-guard sha256sum --check "$component/population-01/source-01.sha256"
phase actual-rustc rustc -vV
phase actual-cargo cargo -vV
for arm in historical post-character;do
 manifest=$pkg/$arm-01/Cargo.toml
 phase "$arm-fetch" cargo fetch --locked --manifest-path "$manifest"
 phase "$arm-entire-metadata" cargo metadata --locked --offline --manifest-path "$manifest" --format-version=1
 count=14;[[ $arm == historical ]] || count=15
 phase "$arm-exact-no-engine-closure" jq --exit-status --argjson count "$count" \
  '(["chained-transfer-lp-historical-01","chained-transfer-lp-finite-projection-01","serde","serde_core","serde_derive","serde_json","hex","proc-macro2","quote","syn","unicode-ident","itoa","ryu","memchr"] + (if $count==15 then ["chained-transfer-lp-post-character-01"] else [] end)) as $names | ([.packages[].name]|sort)==($names|sort) and (.packages|length)==$count' "$out/$arm-entire-metadata.stdout"
 if [[ $arm == historical ]];then
  phase historical-entire-compiler-output cargo build --release --locked --offline --manifest-path "$manifest" --bin extract_public --bin historical_certificates --message-format=json
 else
  phase post-character-entire-compiler-output cargo build --release --locked --offline --manifest-path "$manifest" --bin chained-transfer-lp-post-character-01 --message-format=json
 fi
done
for name in extract_public historical_certificates chained-transfer-lp-post-character-01;do
 arm=historical;destination=$name
 if [[ $name == chained-transfer-lp-post-character-01 ]];then arm=post-character;destination=lp-post-character;fi
 jq --exit-status --arg name "$name" --slurp \
  '[.[]|select(.reason=="compiler-artifact" and .target.name==$name and .executable!=null and .profile.test==false and .profile.opt_level=="3")]|length==1' \
  "$out/$arm-entire-compiler-output.stdout" > "$out/$destination.release-profile-check.txt"
 executable=$(jq --raw-output --arg name "$name" 'select(.reason=="compiler-artifact" and .target.name==$name and .executable!=null)|.executable' "$out/$arm-entire-compiler-output.stdout")
 [[ $executable == "$CARGO_TARGET_DIR/release/$name" && -f $executable && ! -L $executable ]]
 cp "$executable" "$out/$destination"
 cp "$CARGO_TARGET_DIR/release/$name.d" "$out/$destination.entire-dependency-closure.d"
 cmp "$executable" "$out/$destination"
 (cd "$out";sha256sum "$destination") >> "$out/binary-pins.sha256"
done
# Retain every first-party compilation source, not just a list of its names.
phase retain-entire-first-party-source git archive --format=tar --output="$out/entire-actual-first-party-source.tar" "$expected" -- \
 "$component/historical-01" "$component/matrix-01" "$component/post-character-01" \
 "$component/population-01" "$component/runtime-01" "$component/lean" \
 "$component/PROTOCOL_01.md" "$component/historical-whole-fixture-pins-01.json" \
 .github/workflows/chained-transfer-lp-historical-development-01.yml
cp ../crypto/src/hash/sha256.rs "$out/entire-original-pure-SHA-dependency.rs"
phase final-50-source-guard sha256sum --check "$component/historical-01/source-01.sha256"
phase final-population-source-guard sha256sum --check "$component/population-01/source-01.sha256"
[[ -z $(git status --porcelain --untracked-files=all) ]]
jq --null-input --arg source "$expected" --arg compiler 1.99.1 \
 '{source_revision:$source,compiler_toolchain:$compiler,
   scope:"new pure source compilation; original baseline reuse separate",
   scientific_binary_executed:false,source_built_OCI_qualification:false,
   original_baseline_cold_120s_qualification:false}' > "$out/build-receipt.json"
