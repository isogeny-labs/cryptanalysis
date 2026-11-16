#!/usr/bin/env bash
# Thin native development build/process controls only. No historical population,
# target, original field engine, online solver or performance experiment is run.
set -euo pipefail
test "$#" -eq 2
repo=$(git rev-parse --show-toplevel)
cd "$repo"
component=experiments/chained-transfer-lp-presentation-01/matrix-01
out=$1
target=$2
test ! -e "$out"
mkdir -p "$out"
cp "$component/run-development-01.sh" "$out/actual-command.sh"
export CARGO_TARGET_DIR="$target" CARGO_INCREMENTAL=0 CARGO_BUILD_JOBS=1
export RUSTUP_TOOLCHAIN=1.99.1
bounded() (ulimit -v 2097152; exec timeout 120 "$@")
phase() {
 local name=$1 expected=$2 code
 shift 2
 printf '%s %s\n' "$name" "$expected" >> "$out/planned-phases.txt"
 set +e
 "$@" > "$out/$name.log" 2>&1
 code=$?
 set -e
 printf '%s\n' "$code" > "$out/$name.exit"
 printf '%s %s %s\n' "$name" "$expected" "$code" >> "$out/actual-phases.txt"
 test "$code" -eq "$expected"
}
phase build 0 bounded cargo build --release --offline --manifest-path "$component/Cargo.toml" --bin development
binary="$target/release/development"
cp "$binary" "$out/actual-native-binary.bin"
cp "$target/release/development.d" "$out/actual-native-dependency-closure.d"
phase produce-all-synthetic-cases 0 bounded "$binary" --produce "$out/entire-produced-cases"
for whole in "$out"/entire-produced-cases/*.whole-case.json; do
 name=${whole##*/}
 name=${name%.whole-case.json}
 phase "positive-$name" 0 bounded "$binary" --replay "$whole" "$out/accepted-$name.json"
 test -f "$out/accepted-$name.json"
done
for whole in "$out"/entire-produced-cases/whole-negative-controls/*.whole-case.json; do
 name=${whole##*/}
 name=${name%.whole-case.json}
 phase "negative-$name" 1 bounded "$binary" --replay "$whole" "$out/forbidden-accepted-$name.json"
 test ! -e "$out/forbidden-accepted-$name.json"
done
printf '0\n' > "$out/original.exit"
