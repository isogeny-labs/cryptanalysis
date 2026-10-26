#!/usr/bin/env bash
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
# shellcheck source=toolchain.env
source "$here/toolchain.env"
cache=${ASSAY_CACHE:-"$here/.cache"}
saw_home=${ASSAY_SAW_HOME:-"$cache/saw-$ASSAY_SAW_VERSION"}
export PATH="$saw_home/bin:$PATH"
compiler=${CLANG:-clang-19}
"$compiler" --version | head -1 | grep -F "clang version $ASSAY_CLANG_VERSION"
saw --version 2>&1 | grep -F "$ASSAY_SAW_VERSION ("
cd "$root"
sha256sum --check "$here/sources.sha256"
mkdir -p "$here/build"
"$compiler" -std=c11 -O0 -g -Iinclude -emit-llvm -c \
    "$here/harness.c" -o "$here/build/native.bc"
cd "$here"
{
    "$compiler" --version
    saw --version
    sha256sum sources.sha256 harness.c Modarith.cry modarith.saw build/native.bc
    saw -v 3 modarith.saw
} 2>&1 | tee build/verify.txt
# Do not count arbitrary exceptions from `fails` as rejected mutants.
test "$(grep -c '^----------Counterexample----------$' build/verify.txt)" -eq 2
test "$(grep -c '^Invalid: ' build/verify.txt)" -eq 2
printf '%s\n' 'ASSAY COMPLETE: two C proofs, two modulo proofs and four solver-rejected mutants' | tee -a build/verify.txt
