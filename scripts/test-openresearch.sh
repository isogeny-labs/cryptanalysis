#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
entry="$repo_root/scripts/openresearch.sh"
test_dir="$(mktemp -d)"
trap 'rm -rf -- "$test_dir"' EXIT

bash -n "$entry"
bash "$entry" --help >/dev/null
mkdir -p "$test_dir/path with spaces"
cat > "$test_dir/path with spaces/orx" <<'FAKE'
#!/bin/bash
if [[ "$1" == --version ]]; then echo 'orx 0.2.27'; exit 0; fi
printf '%s\n' "$PWD" "$@" > "$ORX_TEST_CALL"
FAKE
chmod +x "$test_dir/path with spaces/orx"
export OPENRESEARCH_BIN="$test_dir/path with spaces/orx"
export ORX_TEST_CALL="$test_dir/call"
(
  cd /tmp
  bash "$entry" discover keyword 'isogeny with spaces'
)
printf '%s\n' "$repo_root" discover keyword 'isogeny with spaces' > "$test_dir/expected"
cmp "$test_dir/call" "$test_dir/expected"
bash "$entry" setup >/dev/null
printf '%s\n' "$repo_root" telemetry off > "$test_dir/expected"
cmp "$test_dir/call" "$test_dir/expected"

sed 's/orx 0.2.27/orx 0.0.0/' "$OPENRESEARCH_BIN" > "$test_dir/old-orx"
chmod +x "$test_dir/old-orx"
if OPENRESEARCH_BIN="$test_dir/old-orx" bash "$entry" setup > "$test_dir/version-log" 2>&1; then
  echo 'FAIL: incompatible CLI accepted' >&2; exit 1
fi
grep -q 'Existing CLI left in place' "$test_dir/version-log"

# An untrusted installer must never execute. Hide the real orx from PATH so
# setup takes the download path, while preserving only the utilities it needs.
mkdir "$test_dir/bin"
for utility in dirname mktemp rm sha256sum sh; do
  utility_path="$(command -v "$utility")"
  ln -s "$utility_path" "$test_dir/bin/$utility"
done
cat > "$test_dir/bin/curl" <<'CURL'
#!/bin/bash
while [[ $# -gt 0 ]]; do
  if [[ "$1" == -o ]]; then
    printf 'touch "$INSTALLER_MARKER"\n' > "$2"
    exit 0
  fi
  shift
done
exit 2
CURL
chmod +x "$test_dir/bin/curl"
export INSTALLER_MARKER="$test_dir/executed"
if env -u OPENRESEARCH_BIN PATH="$test_dir/bin" OPENRESEARCH_PREFIX="$test_dir/absent" \
  /bin/bash "$entry" setup > "$test_dir/checksum-log" 2>&1; then
  echo 'FAIL: modified installer accepted' >&2; exit 1
fi
grep -q 'checksum mismatch' "$test_dir/checksum-log"
test ! -e "$INSTALLER_MARKER"
echo 'OpenResearch integration checks passed.'
