#!/usr/bin/env bash
set -euo pipefail

# Verify the byte-identical upstream source snapshot before suite builds.
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
vendor="$root/suite/vendor/crypto-analysis-core"
test -f "$vendor/Cargo.toml"
test -f "$vendor/src/lib.rs"
cd "$vendor"
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum --check UPSTREAM.sha256
else
  shasum -a 256 --check UPSTREAM.sha256
fi
