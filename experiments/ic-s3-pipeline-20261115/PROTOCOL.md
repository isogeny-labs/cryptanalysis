# Fixed-instance S3 optimization in the IC pipeline

[pcc:unverified] Compare the current generic symbolic constructor against the
optional s3-direct-coefficients constructor inside the actual run_pipeline API.
The new construction/system-packing charge applies to both. No historical S
values enter this experiment. This experiment tests whether the constructor
change lowers complete execution cost; it does not assert a novel asymptotic
method or a globally optimal factor base.

Use existing registered public instances EC1N15Crbhe4e02575ec1c and
EC1N18Crbhe731503070c0, with exact records in instances.json copied from the
registry. Keep their defining polynomials, coefficients, subgroup orders,
cofactors and generators unchanged. Prefix abscissa subspaces have dimensions6
and7. Their full curve lifts are handled through the prime-order cofactor
quotient; record strict subgroup membership separately. [pcc:unverified] Both frozen bases
contain no pure torsion; actual usable counts are58 and134 before sign folding,
with29 and67 matrix columns. Producer input claim PCC-20261116-a18172 records
the native/independent-builder comparison. Archive the exact points/column labels and require
independent pure-Python rebuild equality. Do not substitute a dimension for B.

Methods: buchberger-f2, f4-f2, fes-f2-wide and negation-folded mitm, each with two
summands, walk relation collection, incremental-gauss LA,50,000 trial cap and
one-second per-solver-call budget. The methods share the same factor base and
exact target per fixture. Report each method separately and the best tested
control; a gain over a slower method cannot establish a gain over that control.
These controls are a bounded current-method comparison, not a global-best claim.

Freeze fresh fixture indices100..105 before materializing targets. The source
pins StdRng/rand through Cargo.lock and a public seed law, returning the exact
scalar, target point and walk seed. The scalar is used only for correctness
checking and constructing the benchmark input. Archive one-target workload
manifests and run each target in a fresh process. Never substitute target seeds
or select only completed targets. Publish protocol/source before generating
these frozen targets. Use fixture0 solely for baseline before/after A/A checks.

For every curve/target, execute the repository plain and negation-map rho on
the same point and walk seed, retaining both. These generic binary curves have
no Koblitz signed-Frobenius reference. Require actual verified completion before
using a rho value. Keep missing/capped references explicit. Report counted S,
context-inclusive counted S and raw complete interval time separately. Raw cold
interval is Gf2/curve context construction plus first run_pipeline execution;
curve selection/order discovery, planted-input generation, benchmark calibration,
input-file loading, correctness replay and output encoding are outside that
attack interval. Record outer process time and calibration time as well.
The counted S model and wall-derived group equivalents are distinct outputs;
neither is a signed full-cost result on this unqualified host.

One L4 allocation,4 requested CPUs,8GiB,900-second hard cap; CPU execution only.
Compile two release probes -j2 from the same source/lockfile, other optional
features off;330-second per-build limit and780-second controller soft limit.
After builds, pin a single allowed CPU. Each process has a12-second deadline;
terminate its process group on timeout and retain stdout/stderr. Continue the
frozen matrix after a per-arm failure; preserve partial rows if the whole
controller budget ends. No automatic retries or cap extension.

Fixture-major order, then curve, then methods rotated by fixture offset;
reference/direct order alternates by fixture. Before/after each method pair,
run reference mitm fixture0 on that curve. Retain every A/A ratio outside
0.85..1.15 and every control regression. Require exact curve/target/walk seed,
base count and outcome agreement before interpreting a pair. Solver order may
choose different valid decompositions; do not demand identical trial counts
between distinct methods. Same-method feature pairs should have identical
non-timing counts; flag disagreements for investigation rather than discarding.

Known gVisor placement evidence remains incomplete. All qualified values are
null and the record is invalid for promotion. Matching answers and producer
recomputation are unsigned consistency evidence. Preserve failure and budget
outcomes and every raw row. No default activation follows from this panel.

Current-source context: docs/ic/FRAMEWORK.md, ic_framework/solvers.rs (FES-wide
reference and partial native-op counts), ic_boundary.rs (cofactor quotient and
matched rho), and the immutable registry/archives. Prior KB revision
9141e386254340a9bdba3036f2bb706a sources08f3e36526264f46e4eca5d5381c7e31
(framework) and48f90779f520bc509eb3127a257f86ec (ordered-equation admission)
remain finding-aid context. Owning sources were read for this comparison.
