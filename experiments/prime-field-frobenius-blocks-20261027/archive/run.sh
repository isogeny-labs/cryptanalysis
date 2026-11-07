#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python3 experiments/ideas/norm_trace_lift.py
python3 experiments/ideas/validate_cubic.py
python3 experiments/ideas/finite_domain_check.py
python3 experiments/ideas/validate_blocks.py
python3 experiments/ideas/lift_experiments.py
python3 experiments/ideas/benchmark_blocks.py
python3 experiments/ideas/audit_results.py
python3 summarize.py
