# Four-part Hecke/index-calculus discriminator

2026-10-30. User scope: execute steps 1–4 from the preceding discussion, publish
the evidence in a PR, and continue toward a verified IC improvement. No speed
claim is authorized by rank alone. The prior dense control is in
`../hecke-d39-scalar-closure-20261030/RESULT.md`.

## Frozen selection and execution

Use X_0(11)=11a1: y²+y=x³-x²-10x-20. For D_K=-39 and f=6,
select the first p=v²+351 at or above each of 10,000, 100,000, 1,000,000
with p prime, gcd(2v,6)=1 where possible (if this excludes the original
f=6 construction, use gcd(v,3)=1), and largest prime r of N=#11a1(Fp)
satisfying r>=p/20 and gcd(N/r,r)=1. Precisely: require gcd(v,3)=1;
v is necessarily even for eligible odd p. Search at most 200 consecutive
even v per threshold, retain every considered candidate and rejection.
Do not select on rank, closure or target outcome. Include the saved p=367
matrix as a correctness control, not as a sparse observation.

For richer conductors use f=30, p=v²+8775 at or above 200,000, with
gcd(v,15)=1 and the same subgroup rule and 200-candidate limit. Do not
replace an absent cell with a different discriminant or field. Each field's
curve, order, prime subgroup, cofactor, generator and public target must be
serialized explicitly, with canonical hashes and registry identities.

This is a bounded CPU-only correctness and algorithmic-relation diagnostic,
not a CUDA IC benchmark or qualified wall-time comparison. Use one process,
at most 15 GiB memory, 600 seconds per field and 2400 seconds for the suite.
Run only after `scripts/checkpoint.sh gate` succeeds; checkpoint results.
Use Python/FLINT for certified Hilbert class polynomials and modular arithmetic.
No Sage jobs or unchecked Sage installation are used. Record dependencies,
commands, hashes, host, caps, exits, failures, all phase times (diagnostic only),
group-operation counters and raw point/row witnesses.

## 1. Fixed geometry in sparse subgroups

Enumerate every j root of the certified H_(-39d²) for d|6 and every rational
X_0(11) lift. Reconstruct the j-map and Hecke moments from the eta newform and
formal Weierstrass expansion over Fp, checking extra coefficients. Require
exact reproduction of the original p=367 point set and degree-2/3 rows before
interpreting new fields. Independently verify each retained j's underlying
elliptic-curve trace magnitude 2v. Never infer conductor or membership from
the class-size prediction alone. Record expected/actual stratum counts.

For every sparse field compare: Hecke degrees 2,3; Atkin–Lehner; scalar
closure 2,3; their combinations; projected equalities/zeros; and fixed-seed
random projected bases of the same size with the same scalar budget.
Record projected collisions and multiplier matches, r, C and C²/r. No
failure to find a collision is a nonexistence theorem outside that fixture.

## 2. Effective information

Project by h=N/r. Deduplicate projected points, drop projected zero, rewrite
and verify every row modulo r. Then fold Atkin–Lehner pairs using its actual
signed relation and killed torsion offset. Record unknown count, independent
rank and residual nullity at each step; compare combinations on those same
columns. Independently cross-check dense FLINT and sparse modular ranks.
Do not count new rows plus new unknowns as a gain without measuring nullity.

## 3. Target connection

Choose one public target per field by SHA-256-derived x-coordinate search,
lift and cofactor projection, without choosing a known target scalar. Reject
zero; record the exact point. Choose G as the first nonzero projected point
from ascending x. On the collapsed relation system, solve only its free
base-log variables with a reusable generic BSGS table for G; recover pivot
logs by linear algebra and replay every label. This bootstrap is charged
setup and does not make Hecke rank alone a DLP solver.

Build a signed two-sum index of the labeled base. Try Q+[a]G for the fixed
256 offsets a=0..255, stop at the first match, recover and independently
replay the scalar. Retain a failure at the cap; do not count a generic fallback
as IC target success. Separately solve the same target with generic BSGS as
a correctness reference, with its setup and query counters distinct. Compare
required bootstrap logs and target attempts, not unqualified wall speed.
Also inspect the target's degree-2/3 Hecke fiber: record existing versus new
projected columns and the change in residual nullity. A new neighbor is not
an anchored log. A planted target decomposition may be a correctness control
only, never the primary natural-target yield.

## 4. Richer degrees, conductors and explicit extension traces

On the smallest selected sparse f=6 field, compare full fibers for degrees
2,3,5,7. On the selected f=30 field compare degrees 2,3 against 2,3,5 on the
same complete class. Charge base expansion and moment/fiber construction.

For nonsplit squarefree neighbor polynomials, recover y as a polynomial in x
from the trace-moment matrix. Verify the curve equation in the quotient ring.
Factor the polynomial, compute the actual elliptic-curve Frobenius trace of
each irreducible orbit using extension arithmetic, and check that the sum
of orbit traces equals a_l P in E11(Fp). Retain unsupported repeated-x fibers
as explicit missing coverage, not silently omitted successes. Count how many
trace points are already represented in the factor base; add new trace
columns explicitly and measure the resulting nullity. These are actual
computed points, not formal trace symbols assumed known.

## Controls, reporting and continuation

Preserve all failures and raw outputs in unique attempts. Source the modular
identities, formal-series construction and existing evidence in the report.
Include unit tests for arithmetic, rational/extension traces and linear
recovery, a proof map (finite checked statements versus any unformalized
general theorem), editable diagrams, rank/collision plots and a PDF.
Update the existing sparse-closure/descent problem with actual outcomes.
For a verified stage gain, identify its measured scope and next full-pipeline
test. If generic controls explain it, record that and pursue a concrete
target-connection or relation-cost improvement instead. No result here alone
establishes a cryptographic-size attack or a speedup over matched rho.
