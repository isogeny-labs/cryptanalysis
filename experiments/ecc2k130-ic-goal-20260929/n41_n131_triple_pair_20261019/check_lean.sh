#!/bin/sh
set -eu
case_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
prior_dir="$case_dir/../n41_n131_all_aligned_20261019"
proof_tmp=$(mktemp -d "${TMPDIR:-/tmp}/triple-pair-lean.XXXXXX")
trap 'rm -rf "$proof_tmp"' EXIT
(cd "$prior_dir" && lean -o "$proof_tmp/AllAlignedOrder.olean" AllAlignedOrder.lean)
(cd "$case_dir" && LEAN_PATH="$proof_tmp" lean TriplePairOrder.lean)
