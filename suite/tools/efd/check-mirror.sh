#!/usr/bin/env bash
# Pass the sibling's Rust crate root: ../cryptanalysis/suite or ../crypto.
set -euo pipefail
here=$(cd "$(dirname "$0")/../.." && pwd)
other=${1:?usage: bash tools/efd/check-mirror.sh OTHER_CRATE_ROOT}
for name in mod.rs program.rs formats.rs checked.rs tests.rs catalogue.json; do
  cmp "$here/src/binary_ecc/efd/$name" "$other/src/binary_ecc/efd/$name"
done
for name in Cargo.toml src/lib.rs src/main.rs; do
  cmp "$here/tools/efd/$name" "$other/tools/efd/$name"
done
echo 'EFD library, tests, catalogue and importer match byte for byte'
