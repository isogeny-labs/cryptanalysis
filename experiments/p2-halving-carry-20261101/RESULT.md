# H111 — first-layer halving-carry parity oracle: result

![Measured accuracy ranges for H111 and its controls](../figures/h111-p2-halving-carry-results.png)

## Outcome

The algebraic transfer exists, but the frozen parity bridge does not. All
9,096 targets passed the lift, doubled-half, reduction-kernel, formal-coordinate,
and torsion-section checks. An independent implementation reproduced every
carry and every score. Nevertheless, none of the 24 preregistered predicates
was exact on any of the 28 curve/generator rows. The repeated-halving decoder
therefore did not open.

This is a scoped null: it rejects the frozen offsets `{-1,0,1}` crossed with
zero, least-representative LSB, centered sign, and quadratic-character bits,
including their complements. It does not prove that every possible function
of the carry is useless, and it does not establish or refute external novelty.

## Frozen mechanism and positive structural result

For `Q=[k]G`, H111 computes the unique public group half

```
H = [(r+1)/2] Q
```

and the first-layer section carry

```
C_2(Q) = [2]s_0(H) - s_0(Q),        kappa(Q) = t(C_2(Q))/p in F_p.
```

Reduction sends `C_2(Q)` to the identity because `[2]H=Q`. The Lean theorem
`carry_mem_reduction_kernel` proves this for an arbitrary set-theoretic section.
The experiment also constructed the unique prime-to-`p` torsion lifts of `H`
and `Q`; their carry was zero on every target, as predicted for a homomorphic
section and proved by `homomorphic_section_carry_zero`.

These checks establish that the tested word is a genuine first-layer cocycle,
not an arithmetic artifact. They do not make its values scalar parity.

## Measurements and controls

| Evidence | Best accuracy after 24-way selection | Exact rows |
|---|---:|---:|
| 28 canonical rows | 0.526427–0.657658; median 0.561422 | 0/28 |
| 16 randomized-section controls | 0.518519–0.611111; median 0.573171 | 0/16 |
| 16 symmetry-matched label controls | 0.548780–0.685185; median 0.583333 | 0/16 |
| coordinate-isomorphic E101/E127 | 0.634146, 0.638889 | 0/2 |

The canonical range overlaps the controls. The largest canonical fit was
65.7658% on E211 with generator multiplier 5, below the 68.5185% maximum of the
matched-label controls. Generator relabeling changed which frozen predicate
won. Consequently the partial fits are not evidence for a uniform parity law.

The stable scientific digest was reproduced by two complete runs:

```
383eb1faf53a4fe17088780cb71528df3f20913abdc022c4348f411c26ce4fd5
```

The raw JSON SHA-256 is
`dc66a0d9f1d26d9412a375fdf011353db9c69c953d23df3594327c2e80686b3e`.

## Charged work

The canonical candidate path used 18,192 Hensel lifts, 9,096 lifted doublings,
9,096 mixed kernel sums, and 9,096 formal extractions. Its explicitly charged
ring work was 209,208 modular additions, 418,416 modular multiplications, and
36,384 modular inversions. It also required 9,096 public group-halving scalar
multiplications. Offline evaluation of all frozen predicates made 218,304
predicate calls and stored 9,096 field elements. The hypothetical online
algorithm would use one selected predicate and zero advice bits per query.

The torsion/structural control was intentionally more expensive and is recorded
separately in the artifact. No decoder or recovery cost is reported as
executed because the exactness gate failed.

## Proof and verification boundary

`formal/H111P2HalvingCarry.lean` proves:

1. the carry lies in the reduction kernel;
2. an additive (torsion) section has zero carry;
3. an exact public predicate supplies the canonical parity bit;
4. recursive parity-guided halving reconstructs every nonnegative integer;
5. direct EC verification makes a recovered scalar unique; and
6. the charged total-cost interface.

Lean does not assert the empirical premise that a frozen predicate is exact.
Measurement rejected that premise. The independent verifier does not import
the canonical H111 runner and replayed all canonical, randomized-section,
matched-label, and coordinate-isomorphic observations.

## Prior-art and claim boundary

The bounded screen retained Smart's anomalous-curve attack
([DOI](https://doi.org/10.1007/S001459900052)), Huang–Kueh–Tan's lifting work
([DOI](https://doi.org/10.1007/10722028_22)), Silverman's lifting survey
([DOI](https://doi.org/10.1007/978-3-642-04159-4_6)), and Yasuda's
formal-group analysis ([DOI](https://doi.org/10.1007/978-3-642-12827-1_9)).
The exact H111 predicate family was not found in that bounded screen, but
external novelty is not established.

The frozen protocol is timestamped in
[crypto #3118](https://github.com/isogeny-labs/crypto/pull/3118) and independently
in [cryptanalysis #1349](https://github.com/isogeny-labs/cryptanalysis/pull/1349).
Because zero rows passed, H111 supplies no generic, subexponential, or
polynomial-time ECDLP algorithm.
