#!/usr/bin/env bash
# Compile mutated copies of the real header. The production tree is untouched.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../.." && pwd)
# shellcheck source=toolchain.env
source "$here/toolchain.env"
cache=${ASSAY_CACHE:-"$here/.cache"}
saw_home=${ASSAY_SAW_HOME:-"$cache/saw-$ASSAY_SAW_VERSION"}
export PATH="$saw_home/bin:$PATH"
compiler=${CLANG:-clang-19}
cd "$here"
mkdir -p build/mutation-include/cryptanalysis
cp "$root/include/cryptanalysis/ca_types.h" build/mutation-include/cryptanalysis/
for kind in add sub; do
    if [[ "$kind" == add ]]; then
        edit='s/s -= m;/s += m;/'
        count=1
    else
        edit='s/a + (m - b)/a + (m + b)/'
        count=2
    fi
    sed "$edit" "$root/include/cryptanalysis/ca_modarith.h" > build/mutation-include/cryptanalysis/ca_modarith.h
    if cmp -s "$root/include/cryptanalysis/ca_modarith.h" build/mutation-include/cryptanalysis/ca_modarith.h; then
        echo 'Mutation did not change the input' >&2; exit 1
    fi
    "$compiler" -std=c11 -O0 -g -Ibuild/mutation-include -emit-llvm -c harness.c -o build/mutant.bc
    # The temporary script lives in build; use absolute paths for both inputs.
    sed -e "s@build/native.bc@$here/build/mutant.bc@" \
        -e "s@\"Modarith.cry\"@\"$here/Modarith.cry\"@" modarith.saw > build/mutant.saw
    if saw -v 3 build/mutant.saw > "build/mutation-$kind.txt" 2>&1; then
        echo "Wrong production $kind passed" >&2; exit 1
    fi
    test "$(grep -c '^----------Counterexample----------$' "build/mutation-$kind.txt")" -eq "$count"
    printf 'SOURCE MUTANT REJECTED: %s\n' "$kind"
done
