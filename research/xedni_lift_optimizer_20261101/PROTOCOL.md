# Xedni affine-lift optimizer protocol — 2026-11-01

Status: prospectively frozen for a deterministic algorithmic diagnostic; no
timing or ECDLP-success claim.

## Requested question and exact scope

The user asked whether the old xedni lift construction, including the often
misremembered “nine points” step, admits an easy modern improvement.  The
primary JKSST description actually permits `2 <= r <= 9` and recommends
`r = 4..6`; nine is only the maximum number of independent point conditions
for a ten-coefficient plane cubic.

This diagnostic tests one narrower implementation hypothesis:

> Combining high-precision LLL, Babai nearest-plane, and a bounded exact
> discriminant search can find a lower-discriminant representative of the
> same Step-7 coefficient coset than an unreduced exact-algebra solution, and
> can improve on the Babai coefficient-height representative itself.

It does **not** test whether the lifted rational points are dependent, recover
a discrete logarithm, compare against Pollard rho, or construct a lift over a
binary extension field.

## Frozen input

- Fixture: `inputs/p67_balanced_snf.json`
- Prime-field curve: `y^2 = x^3 + 28` over `F_67`
- Generator used only to derive the four finite-field points: `P0 = (1,30)`,
  of order 73 in the JKSST experiment.
- Multipliers: `(1,5,17,29)`.
- Balanced affine lifts `(x,y,1)`:
  `(1,30,1)`, `(14,-5,1)`, `(7,-6,1)`, `(12,9,1)`.
- Signed coefficient order:
  `(a0,a1,a3,-a00,-a2,-a4,-a6)`.
- Residue vector: `(1,0,0,-1,0,0,-28) mod 67`.
- The committed particular solution and three directions were obtained from
  one exact Smith-decomposition solve of `B u = 0`, `u = u0 (mod 67)`.
  The evaluator does not trust that derivation: it rechecks all four exact
  incidence rows and every coefficient congruence before and after search.

This is a deliberately awkward exact-algebra representative.  Therefore any
large improvement from the raw particular is **not** a comparison with the
paper's Havas–Majewski–Matthews HNF implementation, which also sought short
vectors.  The separate Babai row is the meaningful control for the nonlinear
discriminant refinement.

## Frozen candidate and controls

- Reduction: repository `lll_reduce_hp`, delta `0.99`.
- CVP center: deterministic Babai nearest-plane on the reduced basis.
- Exact objective: first nonsingularity, then absolute completed-square cubic
  discriminant bit length, coefficient-height bit length, and squared L2 norm.
- Neighborhood radii: `0, 1, 2, 4`.
- Candidate caps: exact full neighborhoods for rank three:
  `1, 27, 125, 729` respectively.
- Positive control: `suite/tests/fixtures/xedni_lift_toy.json`, whose affine
  coset contains a known short nonsingular curve.
- Negative controls: an incidence-changing direction and a noncongruent
  direction must be rejected before search.

## Acceptance and stop rules

Every completed row must satisfy:

1. all four exact incidence values equal their values at the input particular;
2. all seven coefficients remain congruent to the input modulo 67;
3. the selected curve is nonsingular;
4. its lexicographic exact objective is no worse than the input;
5. the number of exact evaluations is no greater than the frozen cap.

The run stops after the four radii.  A smaller discriminant at radius `r>0`
than at radius zero is a measured toy-stage improvement over Babai for this
one coset.  No improvement is a null result, not proof that nonlinear search
never helps.  No result changes the JKSST conditional asymptotic bound.

## Reproduction

From repository root after building `ca-icx` in release mode:

```sh
python3 research/xedni_lift_optimizer_20261101/run_evaluation.py \
  --binary suite/target/release/ca-icx \
  --output research/xedni_lift_optimizer_20261101/runs/run-20261101
```

This is a correctness/solution-quality diagnostic on the ordinary managed
host, not a performance benchmark.  Wall-clock ratios are intentionally not
recorded or interpreted.

