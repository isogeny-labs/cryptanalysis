#!/usr/bin/env bash
# Source-bound synthetic unit development only, after original checkpoint.
set -euo pipefail
[[ $# == 2 ]] || exit 2
component=$(cd -- "$(dirname -- "$0")" && pwd -P)
repo=$(git -C "$component" rev-parse --show-toplevel)
out=$(realpath -m "$1")
checkpoint=$(realpath -m "$2")
[[ ! -e $out && -d $checkpoint ]] || exit 2
[[ $(cat "$checkpoint/source-head.txt") == "$(git -C "$repo" rev-parse HEAD)" ]] || exit 2
[[ $(cat "$checkpoint/original-gate.exit") == 0 && $(cat "$checkpoint/original-final-status.exit") == 0 ]] || exit 2
[[ $(git -C "$repo/../crypto" rev-parse HEAD) == 2d46258afc20188b8593b3a0693183d1282e0aaf ]] || exit 2
case "$out/" in "$repo/"*|"$(realpath "$repo/../crypto")/"*) exit 2;; esac
mkdir "$out"
cd "$repo"
export CARGO_TARGET_DIR=${out}-build-cache CARGO_BUILD_JOBS=1 CARGO_INCREMENTAL=0 RUSTUP_TOOLCHAIN=1.99.1
export LP_HISTORICAL_DEVELOPMENT_OUT=$out/all14-entire-native-fixtures
reference=$component/source-01.sha256
cp "$reference" "$out/entire-source-reference.sha256"
cp "$0" "$out/actual-command.sh"
cp -r "$component" "$out/entire-historical-source"
cp -r "$component/../matrix-01" "$out/entire-unchanged-matrix-source"
cp "$repo/../crypto/src/hash/sha256.rs" "$out/original-SHA-module.rs"
git rev-parse HEAD > "$out/actual-source-head.txt"
rustc --version --verbose > "$out/actual-rustc.txt"
uname -a > "$out/host.txt"
bounded() (ulimit -v 2097152; exec timeout 120 "$@")
phase() {
 local name=$1 code;shift
 set +e
 "$@" > "$out/$name.stdout" 2> "$out/$name.stderr"
 code=$?
 set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s\n' "$name" "$code" >> "$out/actual-phases.txt"
 if [[ $code != 0 ]]; then cat "$out/$name.stdout" "$out/$name.stderr";fi
 return "$code"
}
finish() {
 local code=$?;trap - EXIT;set +e
 sha256sum --check "$reference" > "$out/final-entire-source-guard.txt" 2>&1
 local guard=$?
 cmp "$reference" "$out/entire-source-reference.sha256" || guard=1
 printf '%s\n' "$guard" > "$out/final-entire-source-guard.exit"
 [[ $code != 0 || $guard == 0 ]] || code=$guard
 printf '%s\n' "$code" > "$out/original.exit"
 date -u +%FT%TZ > "$out/finish.txt"
 exit "$code"
}
trap finish EXIT
phase initial-entire-source-guard sha256sum --check "$reference"
phase fetch-locked timeout 120 cargo fetch --locked --manifest-path "$component/Cargo.toml"
phase no-field-engine-metadata bounded cargo metadata --locked --offline --manifest-path "$component/Cargo.toml" --format-version=1
phase exact-dependency-names jq --exit-status '([.packages[].name] - ["chained-transfer-lp-historical-01","chained-transfer-lp-finite-projection-01","serde","serde_core","serde_derive","serde_json","hex","proc-macro2","quote","syn","unicode-ident","itoa","ryu","memchr"]) == []' "$out/no-field-engine-metadata.stdout"
phase compile-all-targets bounded cargo test --release --locked --offline --manifest-path "$component/Cargo.toml" --all-targets --no-run --message-format=json
mapfile -t executables < <(jq --raw-output 'select(.reason=="compiler-artifact" and .profile.test==true and .executable!=null) | .executable' "$out/compile-all-targets.stdout")
[[ ${#executables[@]} == 4 ]] || exit 2
for index in "${!executables[@]}";do
 executable=${executables[$index]}
 cp "$executable" "$out/actual-native-$index.bin"
 printf '%s\n' "$executable" > "$out/actual-native-$index.path"
 sha256sum "$executable" "$out/actual-native-$index.bin" > "$out/actual-native-$index.before.sha256"
 phase "native-tests-$index" bounded "$out/actual-native-$index.bin" --nocapture --test-threads=1
 cmp "$executable" "$out/actual-native-$index.bin"
 sha256sum "$executable" "$out/actual-native-$index.bin" > "$out/actual-native-$index.after.sha256"
done
phase strict-all-target-Clippy bounded cargo clippy --release --locked --offline --manifest-path "$component/Cargo.toml" --all-targets -- -D warnings
phase compile-native-entrypoints bounded cargo build --release --locked --offline --manifest-path "$component/Cargo.toml" --bins
for name in extract_public historical_certificates;do
 cp "$CARGO_TARGET_DIR/release/$name" "$out/actual-$name.bin"
 cp "$CARGO_TARGET_DIR/release/$name.d" "$out/actual-$name-dependency-closure.d"
 sha256sum "$out/actual-$name.bin" > "$out/actual-$name.sha256"
done
git status --porcelain --untracked-files=all > "$out/final-source-status.txt"
test ! -s "$out/final-source-status.txt"
printf '%s\n' 'Complete native synthetic unit execution; full historical population and whole feedback/replay/character controls remain pending.' > "$out/scope.txt"
