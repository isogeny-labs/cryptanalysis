#!/usr/bin/env bash
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
export LEAN_PATH="$tmp"
lean -o "$tmp/XFilter.olean" "$root/experiments/prime-field-auxiliary-ic/m31-full-rust-comparison/XFilter.lean"
lean -o "$tmp/Bloom.olean" "$root/experiments/prime-field-auxiliary-ic/m31-full-rust-comparison/Bloom.lean"
lean "$root/experiments/prime-field-auxiliary-ic/m31-metal-four-sum/MetalScreen.lean"
