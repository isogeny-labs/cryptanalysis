# Direct S3 coefficient construction: frozen stage comparison

[pcc:unverified]

The existing algebraic IC oracle calls pq_descent_symbolic::descend. Compare
that current generic symbolic builder against s3-direct-coefficients from the
same source and lockfile. Other optional arithmetic features stay disabled.
This is the equation-construction interval, including allocation and canonical
emission. It excludes relation search, solving, lifting, linear algebra and
scalar recovery; a stage result cannot establish a full IC improvement.

Freeze cases (field degree, basis dimension, summands): (31,8,2), (31,20,2),
(53,24,2), (63,32,2), with unchanged-S4 control (23,6,3). Use six fresh fixture
indices 60..65, alternating reference/candidate order. Each executable process
builds a fresh field context and performs its first descent. Primary recorded
interval is context plus first build; bare first-build time is secondary.
Do not replace cold first calls with amortized loop throughput. Source fixture
construction and 32 independent assignment checks are outside the timer.
Checksums bind all ordered coordinate masks, variable and field-monomial counts.
Require identical checksums and valid assignment checks in every pair.

Use one L4 allocation, four requested CPUs, 8 GiB and a 900-second cap. This is
CPU work; pin a single allowed CPU after compilation. Build both release
binaries with the same toolchain, lockfile and -j2, preserving logs, source and
binary hashes. Bound each build at 330 seconds and the controller at 780 seconds;
retain partial output and terminate its child process group on timeout. No
automatic retry or fixture substitution. Use baseline fixture0 S3(53,24) before
and after each pair; retain all A/A shifts outside 0.85..1.15.

This known gVisor host lacks required placement evidence. Qualified values
remain null and the run is invalid for promotion regardless of raw ratios.
Retain control regressions, calibration failures, compilation failures and caps.
Publish this protocol and source before generating the frozen fixtures.

## Derivation and evidence scope

In characteristic two, for Boolean u_i,w_j and basis v_i, direct coefficients
are v_i²*xR² for both linear groups and (v_i*v_j)*xR+(v_i*v_j)² for cross masks.
Symmetry permits one triangular calculation per unordered basis pair. Emit
cross masks, linear masks and the constant in canonical order, avoiding hash
maps and sorting. This adapts an elementary coefficient identity; no novelty
claim follows. The Lean source proves the identity and symmetry, with the
implementation correspondence remaining a separate verification obligation.

The generic path remains the default and reference. Tests compare every
ordered coordinate coefficient, including repeated/zero basis entries and the
64-variable boundary; existing truth-table and IC integration tests remain.
Native symbolic-descent/system-packing charges were added to the framework
for both arms independently of the optional optimization. No earlier S values
can be spliced into a comparison using the corrected accounting.

KB receipt: SQLite FTS revision9141e386254340a9bdba3036f2bb706a, four queries
covering direct S3 coefficients, negative symbolic descent results, current
algebraic-oracle performance and canonical ANF ordering. Relevant corpus IDs:
source:08f3e36526264f46e4eca5d5381c7e31 (FRAMEWORK.md),
source:fcf24cae0569063dfc31e2c4f7e07fbc (N131 word-descent limitation),
source:48f90779f520bc509eb3127a257f86ec (canonical-equation solver admission).
Current owning Rust sources were inspected. Search ranking is not proof.
