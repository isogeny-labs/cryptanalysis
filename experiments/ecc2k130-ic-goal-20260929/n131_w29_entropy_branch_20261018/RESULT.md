# Exact W29 prefix census and a bounded N131 public-point branch

The first-mask prefix `3` contains **261,794 source-valid W29 edges** among
all **1,048,576** canonical masks with that eight-bit prefix. A full
independent checked-Sage census matched the native count and both endpoint
inverse-trace counts. Restricting the frozen N131 five-pair public-point
XCNF to this prefix produced 3,505 solver restarts in the 600-second parent
interval and remained `BOUNDED_UNKNOWN` at the parent cap. This resolves the
branch's actual source size and measures the solver response to an
entropy-balanced restriction on the real public-point formula.

## Exact instance and branch

The curve is `EC1N131Ckb1heb5f1998f20b`, over
`GF(2)[u]/(u^131+u^13+u²+u+1)`, with subgroup order
`680564733841876926932320129493409985129`. The public-point workload is
`cc09e7eb202a`. The five W29 pair slots use fixed seed mask `898618` and
Frobenius rotations `(0,18,36,54,72)`; the exact three-plus-two target
formula is the archived [source XCNF](../n41_n131_fivepair_w9_w29_20261017/n131_3p2.xcnf)
with SHA-256 `6ec523cab2fd0b72e9bfe23dd1b2e612fa28641daea2aea0276051159535b74a`.
The [protocol](protocol.json) freezes its source hashes, public point,
solver, branch units and one-worker/600-second/4-GiB cap. The accepted
[Sage runtime](sage_runtime_info.json) was saved before the solver run.

The first W29 mask has 28 free bits; its canonical bit 19 is zero. The
branch fixes source-mask bit positions `0..7` to binary value `3` and leaves
all other source masks, signs represented by pair-output roots, middle
outputs, and the target equation free. The prefix was taken from a separate
constructed control before this public solver run. The
[mapping audit](mapping_audit_result.json) rebuilt the actual three-plus-two
XCNF byte for byte and confirmed these mask bits are variables `1..8`.
The arm adds unit literals `1,2,-3,-4,-5,-6,-7,-8`, changing the XCNF
header from `p cnf 121204 274931` to `p cnf 121204 274939`. The
[read-only verifier](verify.py) reconstructs the exact branched formula
hash from the immutable original and eight units; no generated formula
copy is needed.

| Public-point solver arm | Recorded value |
| --- | ---: |
| Original formula variables / clauses / native XOR rows | 121,204 / 232,429 / 42,502 |
| Added mask-prefix unit clauses | 8 |
| Branched XCNF SHA-256 | `d88f50a33e2473cd1536a0909e44d921e56f2d584c0118cbe91a53f585e17d02` |
| Formula patch plus hash | 0.0450 s |
| Solver restarts | 3,505 |
| Parent wall | 600.079 s |
| Sampled combined RSS peak | 774,111,232 B |
| Terminal observation | `BOUNDED_UNKNOWN`, parent wall cap; no SAT/UNSAT line or model |

The parent clock starts before formula patching and ends after the worker is
stopped and its logs are compressed. The input XCNF was constructed for this
public point in the earlier run, so this is a **warm formula-branch
diagnostic**, not the primary single-target online metric. The frozen
[result](result.json) retains the exact phase nanoseconds, solver command,
exit and stop reason, RSS samples, restart count, and raw/compressed log
hashes. The [compressed stdout](solver.stdout.gz) and
[stderr](solver.stderr.gz) are retained. The solver returned no terminal
state before the parent stopped it; this receipt does not decide whether
the prefix contains a relation.

## Full prefix source census

The [native census](prefix_result.json) iterated each of the `2^20`
canonical masks remaining under the eight fixed bits. For each mask `a`,
it set `b=a XOR 898618`, checked the canonical order and source trace,
inverted both nonzero field elements, and retained the edge when both
inverse traces were zero. The [separately frozen Sage audit](prefix_audit_result.json)
enumerated the same masks in the opposite nested-loop order using Sage
polynomial-field inversion and trace; it matched every total and the first
and last eligible mask.

| Exact prefix-3 source count | Native | Independent Sage |
| --- | ---: | ---: |
| Canonical masks checked | 1,048,576 | 1,048,576 |
| Endpoint inversions | 2,097,152 | 2,097,152 |
| Left inverse trace zero | 523,945 | 523,945 |
| Right inverse trace zero | 523,967 | 523,967 |
| Both inverse traces zero | **261,794** | **261,794** |
| First / last eligible mask | 3 / 536,345,603 | 3 / 536,345,603 |
| Worker wall | 2.233 s native | 7.967 s Sage |

The native parent wall was 2.453 s with 25,346,048 B sampled combined RSS;
the Sage audit recorded 243,728,384 B peak process RSS. Both completed
within their separately frozen caps. Four signed pair states per eligible
edge give **1,047,176** first-slot signed states for this prefix. Combining
that exact first-slot count with the earlier *sample-projected* 273,235,968
states in each other slot gives about 2.14 target representations under an
independent-uniform full-curve model. That model is only a width-selection
heuristic: the other-slot counts are projections, group sums may be
correlated, and cross-slot column filtering reduces usable tuples.

The first runtime-info capture encountered transient `ENOSPC` before any
solver work; its [first-attempt receipt](attempt1_runtime_failure.json)
and the successful retry runtime hash are retained. The native compiler
emitted an inherited `-Wreturn-type` warning from the archived field kernel;
the executable and source hashes are pinned in the
[prefix census protocol](prefix_protocol.json). `candidate_id` remains
`null` because this is a point-decomposition component without relation
matrix, factor-base logs, target descent, or paired rho stages.

## Next algorithmic test

The unpinned W29 three-plus-two formula and this source-sized prefix arm
both reached their respective roughly 600-second caps. Another isolated
mask prefix would mostly test search variance. The next gate is an **exact
target-conditioned nonlinear constraint across at least two unresolved
pair outputs or middle partial sums**, with a compact certificate that can
reject a family before full SAT search. Freeze its witness-positive N41
control and ordinary N41 misses, prove rejection soundness, and measure
source-family and memory costs before promoting it to this N131 workload.
