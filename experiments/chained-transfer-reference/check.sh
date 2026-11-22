#!/usr/bin/env bash
set -euo pipefail
study_dir=$(cd -- "$(dirname -- "$0")" && pwd)
repo_root=$(git -C "$study_dir" rev-parse --show-toplevel)
upstream_root=$(cd "$repo_root/../crypto" && pwd)
pin=$(cat "$study_dir/upstream-commit.txt")
[[ $pin =~ ^[0-9a-f]{40}$ ]] || { echo 'invalid source revision' >&2; exit 2; }
git -C "$upstream_root" cat-file -e "$pin^{commit}"
(cd "$upstream_root" && sha256sum --check "$study_dir/upstream.sha256")
(cd "$repo_root" && sha256sum --check "$study_dir/reference.sha256")
(cd "$upstream_root" && sha256sum --check "$study_dir/seven-reference.sha256")
(cd "$upstream_root" && sha256sum --check "$study_dir/seven-independent.sha256")
cargo --version
native_manifest="$upstream_root/research/chained_jacobian_transfers_20261110/native/Cargo.toml"
cargo fmt --manifest-path "$native_manifest" -- --check
cargo clippy --manifest-path "$native_manifest" --features small-prime --locked --offline --all-targets -- -D warnings
cargo test --release --manifest-path "$native_manifest" --features small-prime --locked --offline -- --nocapture
manifest="$study_dir/Cargo.toml"
cargo fmt --manifest-path "$study_dir/independent-walk/Cargo.toml" -- --check
cargo fmt --manifest-path "$manifest" -- --check
cargo clippy --manifest-path "$manifest" --locked --all-targets -- -D warnings
cargo test --release --manifest-path "$manifest" --locked -- --nocapture
