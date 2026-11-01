# H112 — second-digit `p^3` halving carry

Date frozen: 2026-11-01

![H112 second-digit carry evidence flow](../figures/h112-p3-second-digit-carry-flow.png)

Editable vector source: [`h112-p3-second-digit-carry-flow.svg`](../figures/h112-p3-second-digit-carry-flow.svg).

## Requirement-to-evidence contract

- **Mechanism-new relative to H111:** lift to `Z/p^3Z` and retain the second
  formal digit and cross-digit structure. Do not reuse a low-digit-only
  predicate rejected by H111.
- **Exact candidate:** freeze 144 constant public predicates before execution.
  No fitted coefficients, curve-sized lookup tables, or scalar interpolation.
- **Measurement:** all seven curves, generator relabelings `1,2,3,5`, every
  nonzero target, complete scoring, eligible repeated-halving reconstruction,
  and total costs.
- **Controls:** randomized two-digit sections, symmetry-matched labels,
  coordinate isomorphisms, exact two-layer torsion-section zero carries, and
  generic square-root references.
- **Proof:** Lean must cover reduction-kernel membership, digit decomposition,
  conditional parity/reconstruction, EC verification, and charged cost.
- **PR:** paired draft PRs must contain this freeze before execution.

## Mechanism

For `Q=[k]G`, let `H=[(r+1)/2]Q`.  Define a two-digit Hensel section by

```text
x(s_(u1,u2)(Q)) = x(Q) + p*u1 + p^2*u2  (mod p^3),
y(s_(u1,u2)(Q)) = the unique Hensel lift congruent to y(Q) (mod p).
```

The canonical section is `s_(0,0)`.  Its halving carry and normalized formal
word are

```text
C_3(Q) = [2]s_(0,0)(H) - s_(0,0)(Q),
K(Q)   = t(C_3(Q))/p mod p^2,
K(Q)   = kappa_0(Q) + p*kappa_1(Q),  0 <= kappa_i < p.
```

`kappa_0` is H111's first-layer word.  H112 asks whether the genuinely new
second digit, or a fixed joint function of both digits, retains the canonical
integer wrap distinguishing even `k/2` from odd `(k+r)/2`.

## Frozen 144-predicate family

For a field element `z`, define four bits exactly as in H111:

```text
zero(z), integer_lsb(z), centered(z), legendre(z).
```

Each bit is tested with its complement.  Freeze two subfamilies:

1. **Depth channels (72):** for each channel
   `kappa_1`, `kappa_0+kappa_1`, `kappa_1-kappa_0`, each offset
   `c in {-1,0,1}`, each of four bits, and complement:
   `3*3*4*2 = 72`.
2. **Cross-digit XOR (72):** for offsets `c,d in {-1,0,1}` and each of four
   bit kinds, XOR the bit of `kappa_0+c` with the same bit of `kappa_1+d`,
   then test it and its complement: `3*3*4*2 = 72`.

Total: 144.  No predicate depending only on `kappa_0` is included.  The target
label is canonical scalar parity `k mod 2`.

An exact predicate invokes the same public repeated-halving decoder as H111:

```text
R <- [(r+1)/2] (R - [b]G).
```

After at most `ceil(log2 r)` queries, verify the reconstructed `k` by `[k]G=Q`.

## Frozen workload and controls

1. Execute all 28 rows and all 9,096 nonzero targets.
2. Check the `p^3` Hensel equation, lifted doubling, mixed-projective kernel
   subtraction, projective equation, reduction to identity, unit `Y`, formal
   divisibility by `p`, and digit recombination.
3. Score all 144 formulas completely and retain all ties and exact predicates.
4. On E101 and E127, run eight deterministic randomized two-digit section
   controls and eight symmetry-matched parity-label controls each.
5. Repeat primary canonical words after coordinate scaling by `lambda=2`.
6. Solve the unique two-digit prime-to-`p` torsion lifts of `H` and `Q`.  The
   first correction digit must kill `kappa_0`; the second must kill
   `kappa_1`; their doubled-half carry must be exact identity modulo `p^3`.
7. Run full reconstruction only for exact rows.  A primary positive must be
   stable across all four generator relabelings; a generic gate needs 28/28.

Stopping is exhaustive.  Any arithmetic, digit, torsion, control, decoder, or
EC mismatch invalidates the run.

## Cost and promotion gates

Charge both Hensel digits, lifted group operations modulo `p^3`, formal
extraction, predicate work, public EC halvings, setup, controls, memory, advice,
and final verification.  A uniform exact predicate would give `O(log r)`
queries with polynomial bit complexity and hence a subexponential algorithm.

Promotion requires 28/28 exactness, complete reconstruction and EC
verification, a uniform proof of the actual predicate, compiled Lean
interfaces, complete charged complexity, and a source-complete novelty review.

## Prior-art and interpretation boundary

The bounded screen retains Smart's anomalous-curve lifting attack
([DOI](https://doi.org/10.1007/S001459900052)), Huang--Kueh--Tan
([DOI](https://doi.org/10.1007/10722028_22)), Silverman's lifting survey
([DOI](https://doi.org/10.1007/978-3-642-04159-4_6)), and Yasuda's formal-group
analysis ([DOI](https://doi.org/10.1007/978-3-642-12827-1_9)).  They establish
the lifting/formal-group context.  This bounded screen did not locate the exact
second-digit halving-carry test.  External novelty is not established.

Failure rejects only these 144 functions of this canonical `p^3` word.  A toy
positive is not a generic theorem; control-matched fit is not EC-specific
evidence; and a zero torsion-section carry is a control, not a formal-log
oracle.
