#!/usr/bin/env bash
# envcrypt setup for this repo: installs tools and syncs .env <-> .env.enc
#
#   ./setup.sh            install tools, then sync .env and .env.enc
#   ./setup.sh --load     print `export` lines for the decrypted secrets
#                         (use: source <(./setup.sh --load))
#
# Secrets live encrypted in .env.enc (safe to commit). ENVC_KEY must be set
# in your environment (see ~/.zshrc). The plaintext .env stays gitignored.
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
    echo "error: python3 is required" >&2
    exit 1
fi

if ! python3 -c "import Crypto" >/dev/null 2>&1; then
    echo "-> installing pycryptodome"
    python3 -m pip install --user --quiet pycryptodome
fi

if [ -z "${ENVC_KEY:-}" ]; then
    echo "error: ENVC_KEY is not set. Add it to your shell profile:" >&2
    echo "    export ENVC_KEY=<your key>" >&2
    exit 1
fi

ENVCRYPT="./envcrypt"
chmod +x "$ENVCRYPT"

if [ "${1:-}" = "--load" ]; then
    if [ ! -f .env.enc ]; then
        echo "error: .env.enc not found; run ./setup.sh first" >&2
        exit 1
    fi
    exec "$ENVCRYPT" export .env.enc
fi

if [ ! -f .env ] && [ ! -f .env.enc ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "-> created .env from .env.example; fill in secrets, then re-run ./setup.sh"
    else
        echo "-> no .env or .env.enc; nothing to do"
    fi
elif [ -f .env.enc ] && [ ! -f .env ]; then
    "$ENVCRYPT" decrypt .env.enc > .env
    echo "-> decrypted .env.enc -> .env"
elif [ -f .env ] && [ ! -f .env.enc ]; then
    "$ENVCRYPT" encrypt .env
    echo "-> encrypted .env -> .env.enc (commit this file)"
elif [ -f .env ] && [ -f .env.enc ]; then
    if diff -q <("$ENVCRYPT" decrypt .env.enc) .env >/dev/null; then
        echo "-> .env and .env.enc are in sync"
    else
        echo "warning: .env and .env.enc differ" >&2
        echo "  keep .env:      ./envcrypt encrypt .env" >&2
        echo "  keep .env.enc:  ./envcrypt decrypt .env.enc > .env" >&2
        exit 1
    fi
fi
