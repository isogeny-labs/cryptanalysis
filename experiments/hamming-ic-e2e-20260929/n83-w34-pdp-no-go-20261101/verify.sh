#!/usr/bin/env bash
set -euo pipefail

study_dir=experiments/hamming-ic-e2e-20260929/n83-w34-pdp-no-go-20261101
sha256sum -c "$study_dir/inputs.sha256"
sha256sum -c "$study_dir/gate_spec.sha256"

build_dir=$(mktemp -d)
trap 'rm -rf -- "$build_dir"' EXIT
g++ -std=c++17 -O2 -Wall -Wextra -Werror \
  "$study_dir/n83_pdp_resource_gate.cpp" \
  -o "$build_dir/n83_pdp_resource_gate"
"$build_dir/n83_pdp_resource_gate" > "$build_dir/gate_output.json"
cmp "$study_dir/gate_output.json" "$build_dir/gate_output.json"
sha256sum -c "$study_dir/gate_output.sha256"
sha256sum -c "$study_dir/artifacts.sha256"
echo 'N83_W34_PDP_NO_GO_GATE_PASS'
