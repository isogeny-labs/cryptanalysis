# Sparse Hecke constraints, target connection and explicit extension traces

2026-10-30. **Finite correctness and relation-stage results; no qualified IC
speedup or sub-rho claim.** The four requested studies ran, followed by
target-growth and arity controls and an attempted larger conductor-30 continuation.

**Current baseline update:** the later [pair-index reuse study](PAIR_REUSE_RESULT.md)
harvests relations from the index already needed for target descent. It reduces
the required generic queries9→1,12→1 and45→1 in three cells; the sparsest cell
remains at12. The generic pair-only control closes two systems without Hecke.
Read the earlier scalar-only comparison below as its exact historical method,
not the strongest generic baseline. Same-total-budget superiority is unestablished.

## Main result: information survives sparse projections

For D_K=-39, conductor6 and degrees2,3, all three selected fields retain64
distinct projected points. Negation folding gives32 unknown logs. At subgroup
orders16,319 and206,477, doubling/tripling supplies no relations, but Hecke
supplies20 independent constraints on those32 unknowns. Only12 generic base-log
queries are then needed, versus32 for the frozen scalar-only bootstrap.
All labels and solved target scalars were independently replayed.

| Conductor | Field p | Subgroup r | Raw / unique projected / folded columns | Generic free logs | Hecke + scalar free logs | Initial target result |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| 6 | 11,587 | 769 | 64 / 64 / 32 | 29 | 9 | verified, attempt1 |
| 6 | 163,567 | 16,319 | 64 / 64 / 32 | 32 | 12 | verified, attempt20 |
| 6 | 1,032,607 | 206,477 | 64 / 64 / 32 | 32 | 12 | no match in256 attempts |
| 30 | 231,559 | 46,273 | 320 / 318 / 159 | 157 | 45 | verified, attempt1 |

This is a reduction in required generic base-label queries within the frozen
method. It is not a measured reduction in complete setup or online wall time:
geometric construction and linear-algebra costs also matter. The counted generic
query work, including each query's scalar replay, was219 vs825;858 vs2408;
3836 vs10356; and5941 vs20526 group-addition calls respectively. Those counters
exclude relation construction and LA and do not price the complete pipeline.

## Exact objects and prior work

The DLP curve is always E11=X_0(11): y²+y=x³-x²-10x-20 over Fp. D_K=-39
labels the auxiliary CM curves parameterized by modular points; it is not a
claim that E11 itself has that endomorphism discriminant. Each receipt records
N, r, h=N/r, the exact generator, public target, point set and full EC1/UID
preimage. The four identities are registered in the canonical curve catalog;
the actual projected bases are archived in [archive-manifest.json](archive-manifest.json).
The paired crypto PR mirrors those exact curve records, without new isogeny routes.

We reviewed the original [D39 result](../ecdlp-hecke-d39-holdout-20261026/RESULT.md),
its copied Hecke producer, the repeated-root audit, the earlier dense
[scalar-closure control](../hecke-d39-scalar-closure-20261030/RESULT.md), and the
lead atlas's class-group/ECDLP bridge and representative-selection records.
These prevent treating class-group relations or dense scalar collisions as
an ECDLP reduction. The eta/formal-series implementation follows the existing
producer and the differential normalization documented in
[Sage's modular-parametrization reference](https://doc.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/modular_parametrization.html).
FLINT0.9.0's Hilbert class polynomial routine supplies the integer CM polynomials.
The attempted online FLINT reference fetch returned403; package API inspection
and the exact saved Sage fixture were available. No novelty claim is made.

## 1. Fixed-geometry sparse fields

The [primary protocol](PROTOCOL.md) was committed and pushed before selection.
The deterministic selector uses p=v²+39f²/4, the first eligible candidate at
each frozen threshold, and r>=p/20. Every candidate/rejection is in its receipt.
No field was selected on rank or target outcome. The public target is generated
by a fixed hash-to-x/lift/projection rule without supplying its scalar.

The new finite-field implementation first reproduced all64 saved p=367 points,
all48 degree2/3 rows, rank40 and128 actual rational/extension-trace fiber checks.
For new fields every class-polynomial stratum has the expected number of roots
and lifts, and every auxiliary j's trace magnitude is independently counted.
These are class-polynomial strata; a separate Sage endomorphism-order audit
was not run. No new Sage process or unchecked installation was used.

The [small](runs/f6-small-01/receipt.json), [medium](runs/f6-medium-01/receipt.json),
[large](runs/f6-large-01/receipt.json) and [conductor30](runs/f30-01/receipt.json)
receipts retain points, rows, ranks, source hashes, generator/target and counters.
Every attempt has a launch record, cap, exit and raw stdout/stderr. All four
primary cells exited0. Fixed-seed random bases use the same point count,
negation policy and multiplier budget; their exact scalar ranks are in the receipts.

## 2. Effective information, including new trace columns

Each system was checked on original columns, deduplicated nonzero projections
and negation-folded columns. FLINT dense elimination agrees with a separate
sparse modular algorithm. A separate short-curve verifier checks raw Hecke
rows, projected involution rows, normalized labels and returned scalars.
The [independent receipt](runs/independent-01/receipt.json) also recomputes
effective ranks with a third elimination implementation.

For an extended matrix [A_old A_new], the rank of constraints that survive
elimination of new columns is rank([A_old A_new])-rank(A_new). The report
therefore distinguishes full rank from information on the original logs.

| Trace experiment | Original folded columns | Baseline rank | Full extended columns / rank | Rank on original columns | Extra original constraints |
| --- | ---: | ---: | --- | ---: | ---: |
| f6, r769, degrees2,3,5,7 | 32 | 23 | 129 / 118 | 31 | 8 |
| f30, r46273, degrees2,3,5 | 159 | 114 | 480 / 442 | 121 | 7 |
| f6, r206477 continuation, degrees2,3,5,7 | 32 | 20 | 164 / 120 | 20 | 0 |

The last row is particularly discriminating:132 new columns and100 more
rank do not provide a single extra constraint on the original32 logs.
All three rows are finite observations, not a general scaling theorem.

## 3. Target connection and continuation after failure

The frozen bootstrap solves only free base logs using a shared generic BSGS
table, then recovers pivot logs by LA and replays every label. This generic
work is target-independent setup; it is not omitted or presented as a result
of Hecke rank alone. Signed two-sum queries then try Q+[a]G for a=0..255.
The small r=769 target is already represented in the projected base; its
attempt1 is a coverage correctness control, not evidence of new descent.
The same target is separately solved by BSGS for correctness. That reference
is not matched optimized rho, so distance to rho and qualified speed are unknown.

The original large-field target failed all256 attempts. Its [follow-up](FOLLOWUP_PROTOCOL.md)
retains that failure and derives known labels for actual orbit traces where
there is exactly one nonlinear orbit and all rational neighbors are already
labeled. This needs no new generic log query. All new labels and recovered
target scalars are checked by the independent short model.

| Same large-field target, exploratory continuation | Known points incl. zero | Growth additions | Pair-index additions | Query attempts |
| --- | ---: | ---: | ---: | --- |
| Original base | 65 | 0 | 2145 | failed at256 |
| Trace-grown | 201 | 528 | 20301 | verified at3 |
| Generic growth, same growth-addition budget | 869 | 528 | 378015 | verified at2 |
| Generic growth, matched201-point base | 201 | 70 | 20301 | verified at10 |

The [growth receipt](runs/growth-01/receipt.json) and
[matched-size control](runs/matched-base-01/receipt.json) show an executable
finite target connection after the charged bootstrap. They do not establish
Hecke-specific online superiority: the same-size generic base is cheaper to
grow, whereas the trace base uses fewer queries on this already observed target.
Fiber-construction and verification costs are additional. This is generic
decomposition with geometric preprocessing, not an algebraic PDP solver or
evidence of an asymptotic sub-rho algorithm. No post-result target is called a holdout.

A final [arity continuation](ARITY_PROTOCOL.md) reused the original2107-entry
pair index without growing the base. The [retained result](runs/arity-01/receipt.json)
found no three-term match in65 signed-base-offset attempts and no four-term
match in256 sorted pair-offset attempts. Neither arm repaired this target
within its cap. These are bounded negatives, not impossibility statements.

## 4. Degrees, conductor and actual extension traces

On the same complete conductor30 point set, degrees2,3 give folded rank100
on159 columns; adding degree5 gives rank112. Thus degree5 adds12 independent
constraints before the common scalar rows. On f6, degrees5 and7 have no
complete rational fibers in the checked field, but their extension fibers
are computed rather than represented by unknown formal symbols.

The neighbor y-coordinate is recovered from the trace-moment matrix and
verified against the curve equation in the quotient ring. Each irreducible
orbit is summed under Frobenius using explicit extension-field arithmetic.
Its rational trace point is checked, as is the sum-of-orbits Hecke identity.
The original and continuation f6 fields have patterns[1,1,4] for degree5
and[4,4] for degree7. No repeated-x fiber occurred in these cells; repeated-x
inputs remain an explicit unsupported status, not an assumed successful row.

The larger conductor30 continuation did not select an eligible field in its
frozen200-candidate window. The [retained selector record](runs/f30-large-01/selection.json)
and exit1 launch show missing evidence, not a failed mathematical claim.
Its threshold or subgroup condition was not silently relaxed.

## Validation, limits and next work

Four arithmetic/information-accounting [unit tests](validation/unit-tests.txt)
pass, including an independently calculated quadratic-orbit trace. All primary
receipts and all new labels have independent short-model group replay.
The initial signed-eigenvalue bug, its source snapshot and failed control
are retained under runs/control-01; the corrected full control passes.
The four factor-base archives rebuild byte-for-byte from source-bound receipts.
Curve identity metadata validates locally and matches the paired crypto mirror.

This host is CPU-only; [hardware](hardware.json) and [execution](execution.json)
record observable placement/limits. Physical memory technology is unknown.
Wall times are diagnostic aggregate times, not isolated comparisons. Exclusive
phase timers and a matched strong-rho run remain missing, so complete costs
and speedups are unknown. These runs do not ratchet the best verified full IC
baseline. The narrow observed advance is fewer generic base-label queries.

Proof map: finite curve equations, group rows, ranks and scalar outputs are
checked by the retained code/certificates. General identification of all
formal-series functions with Hecke correspondences relies on the sourced
construction; a kernel-checked general theorem and Lean versions of the finite
certificates remain open. [Lean availability](validation/lean-availability.txt)
records that Lean4/mathlib are absent. No weaker theorem or unbuilt source is
claimed as a checked proof.

| Requested step | Execution status | Remaining goal |
| --- | --- | --- |
| 1: fixed geometry, sparse subgroups | verified finite panel | larger sizes and held-out scaling |
| 2: effective constraints | verified, including elimination of new trace columns | structural/formal explanation |
| 3: target connection | verified bounded implementation; one initial failure, then verified growth recovery | cheaper scalable descent and matched rho |
| 4: richer Hecke relations | verified degrees/conductor/extension cells | larger f30 continuation missing within its selector cap |
| PR and continued pursuit | reports, source, receipts, archives and paired metadata PR | hosted gates; next registered experiment |

Next: reduce the remaining12 generic bootstrap queries in sparse f6 without
paying for unanchored trace columns, or construct a cheaper known-label target
oracle. The measured candidate should then face fresh single-target controls,
complete phase accounting and matched strong rho on the required benchmark host.
The existing [problem record](../../problems/hecke-d39-sparse-closure-and-descent.md)
tracks these exact gaps; recording this result does not resolve the full goal.

The [diagram](evidence.svg), [plots](counts.svg) and [PDF](report.pdf) are rebuilt
from editable sources. Existing dense-D39 and surface-transfer diagrams were
checked; this changes relation evidence, not isogeny-route edges, so those
canonical graphs stay unchanged. The lead-atlas review should link this finite
bootstrap/target result rather than treating it as a class-group/ECDLP reduction.
