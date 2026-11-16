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
trap 'status=$?; printf "%s\n" "$status" > "$out/original.exit"; date -u +%FT%TZ > "$out/finish.txt"' EXIT
date -u +%FT%TZ > "$out/start.txt"
cp "$0" "$out/original-command.sh"
phase(){
 local name=$1;shift
 "$@" > "$out/$name.txt" 2>&1
 local status=$?
 printf '%s\n' "$status" > "$out/$name.exit"
 [[ $status == 0 ]]
}
phase immediate-original-gate bash scripts/checkpoint.sh gate || exit 1
phase runtime-custody python3 "$pkg/runtime_custody.py" "$pkg" "$build" "$out" || exit 1
phase initial-prior-inputs sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
test=$(cat "$out/test-actual-path.txt")
phase native bash -c 'ulimit -v 2097152; exec timeout 900 "$1" --nocapture --test-threads=1' _ "$test" || exit 1
grep -Eq '^test result: ok\. 1 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out;' "$out/native.txt" || exit 1
phase final-runtime-bytes cmp "$test" "$out/actual-before-native-test.bin" || exit 1
phase final-prior-inputs sha256sum --check "$pkg/frozen-prior-inputs-01.sha256" || exit 1
exit 0
