# Frozen conductor-6 Hecke multiplicity census

`inputs.json` fixes eleven saved, nonempty conductor-6 matrices and the
SHA-256 of the regularized level-11 Hecke producer and the generic
multiplicity-aware collector. The panel uses one saved matrix per class
and prime, selecting the repaired D=-1407 matrix over its earlier
missing-point version, while retaining the fresh-prime D=-1407 instance.
The D=-39, D=-1295, and D=-2631 matrices are controls with existing
repeated-root audits.

For each saved point and degree 2 or 3, count rational neighbor x-roots
with multiplicity. Use the pinned collector only when an x-root repeats;
otherwise use the pinned producer's simple-root path. Reconstruct
complete rows only after the collector's moment and group checks, a
classical modular-polynomial check for every neighbor, and membership
in the frozen point set. Record every recovery status, any mismatch
against an archived complete neighbor multiset, rows newly admitted,
and archived rows not reproduced. Never silently drop a failure row.

For each matrix whose integer row multiset changes, calculate the exact
rational rank and ranks modulo 23 and 1,000,000,007 before and after.
For unchanged matrices, integer multiset equality itself establishes
rank equality. Keep source and runtime hashes and exact commands.
The outcome is a relation-stage coverage audit, not an online DLP
timing comparison.
