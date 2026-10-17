# Three-code norm joined to an unpinned six-slot N41 public query

## Result

**The six-slot hybrid eliminates the first three pair-output x roots inside an
exact nested norm while leaving all six source-code choices free.** Its frozen
public-point XCNF has **101,810 AND gates**, 117,547 variables, 306,947
ordinary clauses, and 15,446 native XOR rows. The archived ordinary relation
satisfies every generated row, and independent Sage replay checks the source
quadratics, three-source norm, six-pair group sum and public target. The
one-worker unpinned CryptoMiniSat query reached its **600.027 s** parent cap
with status `BOUNDED_UNKNOWN`; its raw output contains no SAT or UNSAT
terminal line. The sampled combined peak RSS was **374,849,536 bytes**, below
the frozen 4-GiB cap.

This tests an algebraic root-elimination topology on the exact public N41
source. The norm replaces three explicit pair-output x-root variables with
one reciprocal coordinate for their group sum. It is connected through two
right-triple S3 links and one final public-target S3 link, so the public point
constrains both still-free partial sums. The checked query shows that this
representation is feasible to build and retains the ordinary relation;
under the measured solver and cap, its extra algebraic gate did not complete
the public search.

## Method and exact source

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
\(\mathbb F_2[t]/(t^{41}+t^3+1)\) with \(y^2+xy=x^3+1\). The frozen six-pair
source uses seed code 56, rotations `(0,6,12,18,24,30)`, 40 allowed
canonical codes and four signed point states per code in each slot. The raw
public target is `(2026560328086,1928332930914)`; the subgroup target is
its cofactor-four image. All 42 code wires are free in the public formula,
and the existing twelve-column distinctness policy is enforced across all
six choices.

For the left slots 0–2, each selected code defines a two-root quadratic
\(x_i^2=\alpha_i x_i+\beta_i\) in reciprocal x. The nested norm of the
four-summation resultant is the product over all eight root triples. It
vanishes exactly when the left group sum has the selected reciprocal x under
the nonexceptional chart. Right slots 3–5 keep the direct bilinear pair
leaves. Two reciprocal S3 equations construct their three-pair subtotal;
a final S3 equation joins it to the left norm coordinate and the public raw
target. Global point negation is available within each signed source family,
so an x-coordinate match to either orientation of the public target can be
oriented to that point. The conditional group argument is checked in
`HybridStructure.lean`; the finite source and curve bridges are audited in
Sage and mapped in `PROOF_MAP.md`.

| Exact public formula | Value |
| --- | ---: |
| Left nested-norm AND gates at its checkpoint | 92,544 |
| Complete hybrid AND gates | 101,810 |
| Variables | 117,547 |
| CNF clauses / native XOR rows | 306,947 / 15,446 |
| XCNF bytes | 8,596,207 |
| Formula build / archived-assignment check | 0.653 s / 0.446 s |
| Public solver parent wall / status | 600.027 s / `BOUNDED_UNKNOWN` |
| Sampled peak parent-plus-solver RSS | 374,849,536 B |

The query used the hashed `/opt/homebrew/bin/cryptominisat5` binary with
`--threads=1`, `--maxtime=590`, `--zero-exit-status`, `--verb=1` and
`--printsol=1`. The parent stopped the solver at 600 s with no terminal
answer. The formula build, checked-Sage startup, audits and terminal readback
are separate from that solver interval. This is an ordinary-host
point-decomposition diagnostic with `candidate_id: null`.

## Verification and preserved failures

`build.py` completed a full Boolean assignment from the archived relation
and checked all 306,947 clauses and 15,446 XOR rows. The independent Sage
control rebuilt the six elliptic-curve points, their left/right subtotals,
the public raw sum, the source quadratics and the witness norm value. A
second Sage program checked **all 240 source quadratic roots** for slots
0–2 and eight predeclared three-code panels, each with 64 signed states and
32 distinct reciprocal subtotal coordinates. Its direct group values are
roots of the corresponding eight-factor norm. A separate formula audit
rebuilt the XCNF byte for byte and found no unit clause on any of the 42
source-code wires. `terminal.json` checks the source and binary hashes,
protocols, raw solver logs, independent audits, Lean output and censored
query classification.

The first formula-build attempt stopped in the control assignment constructor
at an incorrect module reference before writing XCNF. Its original source,
protocol, stdout/stderr and `PRODUCER_FAILURE` receipt remain as version 1.
The first formula-audit attempt likewise stopped at a path-type error before
rebuilding XCNF; its original source, protocol, logs and failure receipt are
retained. The corrected version-2 builder and auditor passed without changing
the mathematical circuit source.

Lean 4.34.1 checked `two_triples_are_six_sum` and `orient_target`; each
`#print axioms` reports only standard `propext`. The prior nested-norm work
has a checked common-root resultant implication. The complete curve-to-S3
and quadratic-algebra norm bridges remain the explicit formalization
obligations in `PROOF_MAP.md`; `lean4checker --fresh` was unavailable here.

## Next gate

The added norm supplies an exact code-bit relation but brings the complete
N41 formula to 101,810 AND gates and leaves the unpinned query bounded at
600 s. The next design should derive a **small target-conditioned rejection
on code families before evaluating the full norm or explicit right roots**.
A cheap falsifier is to project one or more low-cost subresultant coefficients
onto the 40-code N41 domain, measure whole-family rejection and construction
work, and require an independently replayed unpinned relation under the same
one-worker envelope. Only a passing N41 search and source-bound N131 resource
projection should trigger the frozen N131 public-point attempt.
