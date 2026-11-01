# H111 — first-layer halving carry parity oracle

Date frozen: 2026-11-01

![H111 halving-carry evidence flow](../figures/h111-p2-halving-carry-flow.png)

Editable vector source: [`h111-p2-halving-carry-flow.svg`](../figures/h111-p2-halving-carry-flow.svg).

## Requirement-to-evidence contract

- **Mechanism-new relative to H110:** use a binary group-law section cocycle
  evaluated from one public target and its public group half; do not interpolate
  or store the full scalar-indexed H110 word.
- **Exact candidate:** freeze a constant family of 24 public bit predicates of
  the first-layer carry.  No fitted coefficients or curve-sized tables.
- **Measurement:** all seven curves, generator relabelings `1,2,3,5`, every
  nonzero target, full repeated-halving reconstruction for any exact row, and
  complete lift/group/field/verification costs.
- **Controls:** randomized Hensel sections, symmetry-matched random parity
  labels, coordinate-isomorphic models, torsion-section zero carries, and
  generic square-root references.
- **Proof:** Lean must prove that the carry is in the reduction kernel, that an
  exact predicate supplies the canonical parity bit, repeated-halving
  reconstruction, EC verification, and the conditional total-cost theorem.
- **PR:** paired draft PRs must contain this freeze before execution.

## Mechanism

Let `s_0:E(F_p)->E(Z/p^2Z)` be H110's coordinate-fixed Hensel section, which is
explicitly not assumed to be a homomorphism.  For `Q=[k]G`, compute the unique
group half

```text
H = [(r+1)/2] Q.
```

Its canonical scalar is `k/2` when `k` is even and `(k+r)/2` when `k` is odd.
The section's doubling carry is

```text
C_2(Q) = [2]s_0(H) - s_0(Q) in ker(E(Z/p^2Z) -> E(F_p)),
kappa(Q) = t(C_2(Q))/p in F_p.
```

This cancels the reduced point exactly and asks whether the integer wrap in
canonical halving survives in a fixed public bit of `kappa`.  Unlike H110, the
candidate is a direct parity oracle; it performs no scalar interpolation.

## Frozen predicate family

For offsets `c in {-1,0,1}`, reduce `z=kappa+c` modulo `p` and test four public
bits:

```text
zero(z)      = 1 iff z=0,
integer_lsb  = least nonnegative representative of z modulo 2,
centered(z)  = 1 iff representative(z) > (p-1)/2,
legendre(z)  = 1 iff z is a quadratic nonresidue; zero maps to 0.
```

Test each bit and its complement: `3*4*2=24` formulas per row.  The family is
constant and public; no formula is added after observation.  The target bit is
canonical scalar parity `k mod 2`.

An exact formula gives a decoder.  At each step query parity `b` on the current
point `R=[m]G`, record `b`, and replace

```text
R <- [(r+1)/2] (R - [b]G).
```

This changes the canonical scalar from `m` to `(m-b)/2`.  After at most
`ceil(log2 r)` steps the accumulated binary bits reconstruct `k`; verify
`[k]G=Q` independently.

## Frozen workload and controls

1. Execute all 28 curve/generator rows and all 9,096 nonzero targets.
2. Check both Hensel lifts, doubling, the mixed-projective subtraction, the
   projective curve equation, reduction to identity, unit `Y`, divisibility by
   `p`, and a separately composed split/formal calculation.
3. Completely score all 24 predicates.  Retain exact formulas, best accuracy,
   all ties, and operation counts.
4. On primary E101 and E127, run eight deterministic random-section controls
   and eight symmetry-matched parity-label controls each, for 32 controls total.
   Every control receives the identical predicate family.
5. Repeat the canonical primary words after the least nontrivial coordinate
   scaling isomorphism; report formula and accuracy stability.
6. Construct the unique prime-to-`p` torsion lifts of `H` and `Q` from H110's
   first-layer correction and verify that their carry is identity (`kappa=0`).
   This proves the homomorphic section destroys the proposed signal.
7. Run the complete repeated-halving decoder only for exact observed formulas.
   A primary-row positive must replicate across all four generators; the generic
   gate requires all 28 rows.

Stopping is exhaustive.  Any curve, lift, reduction, kernel, formal,
predicate, reconstruction, or EC mismatch invalidates the run.

## Cost and promotion gates

One query uses one EC halving multiplication, two Hensel lifts, one lifted
doubling, one mixed-projective kernel subtraction, one formal extraction, and
one constant predicate.  Charge all setup, queries, memory, advice, and final
verification.  If exact uniformly, `O(log r)` queries each costing
`poly(log p,log r)` would give polynomial—and therefore subexponential—runtime.

Promotion requires:

1. one public predicate exact on every generic row and generator relabeling;
2. every scalar reconstructed and EC-verified without a fallback search;
3. a uniform mathematical proof of the predicate, not only toy evidence;
4. Lean proofs of the actual carry/parity/reconstruction/cost path;
5. source-complete novelty review and complete charged complexity.

## Prior-art boundary

The bounded search retained Smart's anomalous-curve attack
([DOI](https://doi.org/10.1007/S001459900052)), Huang--Kueh--Tan's lifting
work ([DOI](https://doi.org/10.1007/10722028_22)), Silverman's lifting survey
([DOI](https://doi.org/10.1007/978-3-642-04159-4_6)), and Yasuda's formal-group
ECDLP analysis ([DOI](https://doi.org/10.1007/978-3-642-12827-1_9)).  They
establish lifting prior art and the generic relation-preservation obstruction.
The bounded Crossref/OpenAlex screen did not locate this fixed first-layer
halving-carry parity test.  Status: mechanism-distinct in this repository;
external novelty not established.

## Interpretation boundary

- Failure rejects only these 24 public predicates of this carry.
- A toy exact row is not a generic theorem.
- Control-matched performance is not EC-specific evidence.
- The torsion-section zero control cannot be used as a formal-log oracle.

