# Boolean execution pilot, 2026-10-18

Actual execution for audit items 3, 5 and 6. All three remain **partial** against the original requested scope. This is CPU correctness evidence and counted work, not an IC speedup or a security estimate.

Read [REPORT.md](REPORT.md), [REPORT.pdf](REPORT.pdf) and [execution-status.json](execution-status.json). Exact inputs and proofs of all toy root sets are retained; the scalar F5 timeouts are retained alongside completed M4RI results. The [primary-source record](sources/primary-sources.json) pins the published algorithms and describes what was implemented.

Run from the repository root. Every result directory is exclusive-create. Use a fresh output directory when repeating; retain the committed `runs/cpu-correctness-r1/inputs.json` as the order-independent frozen input.

```bash
export F4_F2_ECHELON=host OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python3 -m unittest discover -s experiments/ideas_boolean_20261018 -p test_controls.py -v

# Regenerate input and run original Python/native F5, Dinur parity and fixed-row replay.
python3 experiments/ideas_boolean_20261018/run.py --out experiments/ideas_boolean_20261018/runs/cpu-correctness-r2

python3 experiments/ideas_boolean_20261018/run_lptwy.py --inputs experiments/ideas_boolean_20261018/runs/cpu-correctness-r1/inputs.json --out experiments/ideas_boolean_20261018/runs/lptwy-correctness-r2
python3 experiments/ideas_boolean_20261018/run_lptwy_search.py --inputs experiments/ideas_boolean_20261018/runs/cpu-correctness-r1/inputs.json --binary experiments/ideas_boolean_20261018/runs/lptwy-correctness-r2/lptwy-decision --out experiments/ideas_boolean_20261018/runs/lptwy-search-r2

python3 experiments/ideas_boolean_20261018/run_native_orders.py --inputs experiments/ideas_boolean_20261018/runs/cpu-correctness-r1/inputs.json --out experiments/ideas_boolean_20261018/runs/native-orders-r2

bash experiments/ideas_boolean_20261018/build_m4ri.sh
export M4RI_PREFIX="$PWD/experiments/ideas_boolean_20261018/toolchain/m4ri"
python3 experiments/ideas_boolean_20261018/run_m4ri.py --inputs experiments/ideas_boolean_20261018/runs/cpu-correctness-r1/inputs.json --out experiments/ideas_boolean_20261018/runs/m4ri-correctness-r2
python3 experiments/ideas_boolean_20261018/run_m4ri_orders.py --inputs experiments/ideas_boolean_20261018/runs/cpu-correctness-r1/inputs.json --out experiments/ideas_boolean_20261018/runs/m4ri-orders-r2

# This renderer reads the retained r1 results only and performs no experiments.
python3 experiments/ideas_boolean_20261018/render_report.py
```

The native adapters copy source into their own run directory and pin both source digests. No existing core solver was edited. The block/weighted layouts require a full degree scan; the adapters replace the old leading-degree shortcut before using those orders.

The M4RI library is a pinned upstream release installed only under this experiment. Rebuilds need network access. The original library, generated binaries and disposable caches are ignored; their exact hashes, build commands and test logs are retained.

Full Dinur search, useful exponent fitting, bounded solving-degree scans, Joux-Vitse symbolic replay and GPU full IC benchmarks remain open. Fixed-degree Macaulay plus unbounded completion is explicitly not a claim about solving degree D. Existing source failures and missing external tools are named in the report.
