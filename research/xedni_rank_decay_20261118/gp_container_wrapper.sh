#!/bin/sh
# Frozen host shim for the rank-decay PARI image.  The image ID is immutable;
# network access is disabled and GP receives stdin/arguments unchanged.
set -eu

IMAGE_ID='sha256:923e7e41d2fe1716fc3f1a6e06486d469b608baa6d6b4b0fdbb6e43b132049cf'
DOCKER='/usr/local/bin/docker'

if [ "${1:-}" = '--xedni-image-id' ]; then
    printf '%s\n' "$IMAGE_ID"
    exit 0
fi

if [ ! -x "$DOCKER" ]; then
    printf '%s\n' "xedni gp wrapper: missing pinned runtime $DOCKER" >&2
    exit 127
fi

exec "$DOCKER" run --rm -i --network=none --entrypoint gp "$IMAGE_ID" "$@"
