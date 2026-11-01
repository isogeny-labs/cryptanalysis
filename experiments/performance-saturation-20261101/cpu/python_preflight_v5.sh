#!/bin/dash
# Minimal external trust-root verifier for every CPU baseline A/A v5 Python launch.
set -eu
unset PWD

manifest=/workspace/cryptanalysis/experiments/performance-saturation-20261101/cpu/python-bootstrap-closure-v5.sha256
expected_manifest_sha256=ac3b8f9bfcc19971758d7b5cdfdb314b00c91556101a8b0951dc93608b992ce6
observed_manifest=$(/usr/bin/sha256sum "$manifest")
case "$observed_manifest" in
    "$expected_manifest_sha256  $manifest") ;;
    *) echo "CPU v5 Python closure manifest identity mismatch" >&2; exit 125 ;;
esac
/usr/bin/sha256sum --strict --quiet --check "$manifest"
[ ! -e /opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python312.zip ] || {
    echo "CPU v5 Python zip import path unexpectedly exists" >&2
    exit 125
}

exec /opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3.12 \
    -S -B -P -X pycache_prefix=/dev/null \
    /workspace/cryptanalysis/experiments/performance-saturation-20261101/cpu/python_bootstrap_v5.py \
    "$@"
