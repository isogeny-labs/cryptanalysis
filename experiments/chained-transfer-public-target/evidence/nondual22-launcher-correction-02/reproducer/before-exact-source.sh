#!/usr/bin/env bash
set -euo pipefail
repo=$(cd -- "$(dirname -- "$0")" && pwd -P)
cd "$repo"
cp "$0" "$1"
