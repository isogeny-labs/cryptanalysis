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
cargo --version
manifest="$study_dir/Cargo.toml"
cargo fmt --manifest-path "$manifest" -- --check
cargo clippy --manifest-path "$manifest" --locked --all-targets -- -D warnings
cargo test --release --manifest-path "$manifest" --locked -- --nocapture
