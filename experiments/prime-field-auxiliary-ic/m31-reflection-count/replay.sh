#!/bin/sh
# Run via "lake env sh /absolute/path/to/replay.sh" in the mathlib project.
set -eu
src=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
export LEAN_PATH="$out:${LEAN_PATH:-}"
lean -R "$src" -o "$out/QuotientOrders.olean" "$src/QuotientOrders.lean"
lean -R "$src/.." -o "$out/M31FixtureObstruction.olean" "$src/../M31FixtureObstruction.lean"
lean -R "$src" -o "$out/Correlation.olean" "$src/Correlation.lean"
lean -R "$src" -o "$out/MixedBuckets.olean" "$src/MixedBuckets.lean"
lean "$src/Shifted.lean"
lean -R "$src" -o "$out/FixtureHash.olean" "$src/FixtureHash.lean"
lean "$src/CoordinateLookup.lean"
