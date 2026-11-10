#!/usr/bin/env bash
# Audit this host's own cryptographic configuration (no network probes) and
# write JSON, HTML, Markdown, CycloneDX CBOM, CSV and SARIF reports.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m cryptoscan scan --no-network --format all --out "${1:-./cryptoscan-report}" "${@:2}"
