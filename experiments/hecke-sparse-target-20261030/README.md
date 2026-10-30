# Sparse Hecke/index-calculus studies

[Results](RESULT.md), [PDF](report.pdf), [diagram](evidence.svg), [plots](counts.svg).

[Current pair-index reuse result](PAIR_REUSE_RESULT.md) strengthens the generic
control and reduces bootstrap queries without additional pair-construction
curve sums. It explicitly updates the interpretation of the earlier controls.
[Prepared cost comparison](COST_CELL_PROTOCOL.md) records the next complete
fixed-base workload and its retained no-CUDA preflight failure. No benchmark
execution or qualified speed comparison is claimed.

The primary protocol covers four fields and all four user-requested questions.
Follow-up protocols explicitly distinguish post-result continuation controls.
Raw receipts remain loose because verifiers and archived source snapshots name
their exact paths. The larger conductor30 selector failure is retained.

Dependencies: Python3.12, python-flint0.9.0 and NumPy for the study; Matplotlib,
ReportLab, pypdf and Graphviz for report rendering. No Sage runtime is used.

From the repository root, run `python3 -m unittest discover -s
experiments/hecke-sparse-target-20261030 -p 'test_*.py' -v`. Research commands
must pass `bash scripts/checkpoint.sh gate` first. `study.py --cell NAME --out
UNIQUE_PATH` runs a frozen primary cell; `verify.py --out UNIQUE_PATH` performs
independent short-model replay; `growth.py` and `continuation.py` implement
the explicit continuation protocols. Every output uses exclusive creation.

Rebuild the report from this directory with `python3 build_report.py`.
The four point-set archives rebuild from immutable independently checked
source receipts; they are source-snapshot rebuilds, not new CM enumerations.
No result is a qualified wall-speed or sub-rho claim.
