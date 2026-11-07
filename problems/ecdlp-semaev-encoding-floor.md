# Semaev decomposition: the constraint-degree floor

- **Status:** argument complete, needs review
- **Kind:** lower bound on solving degree; rules out a family of attacks
- **Affected work:** `docs/INSTRUCTION-COST-ACCOUNTING.md`, point-decomposition experiments
- **Next action owner:** unassigned
- **Last updated:** 2026-11-06

## Problem

Index-calculus attacks on prime-field ECDLP decompose `R = P1 + ... + Pm` by
solving Semaev's summation polynomial together with a factor-base membership
constraint. The cost is governed by the degree of regularity `d_reg` of that
system, and the standard hope is that a better choice of coordinate function
`h` lowers `d_reg` enough to beat Pollard rho.

This note records a floor that does not depend on `h`: for every encoding of
membership by a degree-`N` polynomial (which is what `prod_{b in B}(x_i - b) =
0` and `x_i^N = 1` both are), `d_reg >= N`. At `m = 3` that floor is roughly
575x above the value needed to beat rho at 30-bit primes, so no coordinate
change can rescue the family.

## What would unblock it

### Definitions, because the floor is not the same statement for all of them

Three things get called "degree of regularity":

| name | definition | floor here |
|---|---|---|
| `d_reg` (semi-regular / Macaulay) | least `d` such that the degree-`d` graded piece of `R/I` vanishes | `>= N` |
| F4/F5 solving degree | top degree of a polynomial in the computed Groebner basis | **not** `>= N` in general |
| first-fall degree `d_ff` | first degree where the rank drops faster than semi-regular | a proxy, no floor |

Claim A below is about the first. The second can in principle be smaller: a
reduced basis may generate `C` from lower-degree elements. What survives for
the second is a **size** floor, not a degree floor: a zero-dimensional quotient
with `D` solutions needs linear algebra on at least `D` states, and the
Macaulay matrix at degree `d` in `n` variables has `binom(n+d, d)` columns. For
the decomposition system `D` is small (the system is overdetermined: a random
pair `(b1, b2)` satisfies `S_3 = 0` with probability `~2/p`), so this does not
rescue the attack, but the claim must be stated as Claim A, not as "the
solving degree is at least `N`".

### Claim A (degree floor)

Let `B` be a factor base of size `N`, and let the membership condition be a
polynomial `C(x)` of degree `N`. For the system

```
S_m(x_1, ..., x_{m-1}, x_R) = 0
C(x_i) = 0                        for i = 1..m-1
```

the degree of regularity satisfies `d_reg >= N`, for every `m` and every
coordinate function `h` used to build `S_m`.

### Argument for Claim A

`d_reg` is the largest degree reached by the Macaulay matrix before the ideal
becomes zero-dimensional (equivalently, the top degree of the `d`-th
homogeneous component in the F4/F5 sense).

If `d_reg < N`, then no multiple of `C` of degree `<= d_reg` exists, because `C`
itself has degree `N`. The Macaulay matrix at every degree `<= d_reg` is then
built from `S_m` alone, and the variety it describes is **unconstrained** in
`x_1, ..., x_{m-1}`: the factor-base condition never enters the computation.

A solver that returns solutions of the unconstrained system is solving a
different problem — the decomposition without the factor base — which is not
the relation the attack needs. Any solver that enforces membership must
therefore reach degree `>= N`.

`h` does not appear: it changes the degree and monomial support of `S_m`, and
therefore the *value* of `d_reg` above the floor, but it cannot change the
floor itself, which comes from `C`.

### Numbers at `m = 3`

With `N = p^{1/3}`, the survival condition against rho with `omega = 2` is

```
d_reg < p^{1/(18 omega)} = p^{1/36}
```

| quantity | `p = 2^30` | `p = 2^60` |
|---|---|---|
| `N = p^{1/3}` | `2^10 = 1024` | `2^20 = 1.05e6` |
| required `d_reg` | `2^{0.833} ~ 1.8` | `2^{1.67} ~ 3.2` |
| floor | `1024` | `1.05e6` |
| shortfall | **~575x** | **~3.3e5 x** |

The gap widens with `p`: the floor grows like `p^{1/3}` while the requirement
grows like `p^{1/36}`.

### Claim B (description floor)

Any algebraic description of membership in a set of size `N` costs `Omega(N)`:
a univariate polynomial vanishing exactly on `B` has degree `N`, and the
auxiliary-variable encoding below needs `Omega(N)` variables. Claim A turns the
first into a degree floor. The second is not a theorem, but the semi-regular
prediction is that a dense system in `n` variables with `Omega(n)` quadrics has
`d_reg = Omega(n)`, so the wall reappears with `n` in place of `N`.

### Auxiliary-variable (boolean indicator) encodings

Replace `C(x_i) = 0` by

```
z_{i,b}^2 - z_{i,b} = 0,  sum_b z_{i,b} = 1,  x_i - sum_b b z_{i,b} = 0
```

for `b in B`. Every generator now has degree `<= 2`, so Claim A's letter no
longer applies. What is left is Claim B: `n = (m-1)N + O(1)` variables and
`(m-1)(N+1)` equations. For `m = 3`, `N = p^{1/3}`, that is already `~2p^{1/3}`
variables — the algebraic description is as large as the degree-`N` generator
it replaced.

The honest status: this encoding is **not** excluded by Claim A, and the
semi-regular argument that it is excluded by Claim B is heuristic. A Macaulay
rank computation at toy size (`p = 2^10`, `N = 2^3`, `n ~ 16`) would settle
which of the two floors is operative. Until then, the claim to defend is
"every known encoding pays `Omega(N)` in degree or dimension", not "no encoding
can do better".

### What would beat it

Only one of:

1. A membership encoding of degree `o(N)` — i.e. a factor base with low-degree
   algebraic structure, independent of coordinates.
2. A decomposition algorithm that does not compute a Groebner basis or Macaulay
   matrix, so that `d_reg` is not the cost measure.
3. `m` growing with `p` so that `N = p^{1/m}` shrinks faster than the permitted
   `d_reg`; this is the `L_p[1/2]` regime, not a constant improvement.

### Measured support (reproducible)

`tools/semaev/s3_support.py` expands `S_3` symbolically. For `y^2 = x^3 + 3x + 7`:

```
monomials: 13 of the 27 in the box [0,2]^3
degree in x1 / x2 / xR:  2 / 2 / 2
total degree: 4
```

so the semi-regular estimate has real sparsity to exploit, and still cannot go
below the constraint floor.

## Evidence and uncertainty

- The argument is elementary and should be checkable by a reviewer in minutes;
  it is **not** peer-reviewed.
- Claim A assumes `d_reg` is the graded-vanishing (Macaulay) degree and that
  membership is one degree-`N` polynomial. The F4 solving degree is not bounded
  by `N` in general; only Claim B applies there.
- Claim B is heuristic: it rests on the semi-regular prediction for dense
  systems with `Omega(n)` quadrics. The boolean-indicator encoding escapes
  Claim A by construction, and its exclusion depends entirely on Claim B.
- The `p^{1/(18 omega)}` threshold is the constant from the cost model in the
  delphi brief; changing the model changes the exact shortfall, not the
  asymptotic gap `p^{1/3}` vs `p^{1/36}`.
- Nothing here says anything about `m >= 4` with `m` growing; the claim is
  uniform in `m`, but the threshold arithmetic is not.

## Next discriminating step

Two computations, both at toy size:

1. **Claim A.** `m = 3`, `p = 2^10`, `N = 2^3`, membership by `prod (x - b)`;
   compute the Macaulay rank profile. `d_reg` should be `>= N` and the profile
   should show a jump exactly when multiples of `C` enter.
2. **Claim B.** The same system in the boolean-indicator encoding (`n ~ 16`);
   measure `d_reg` and compare with the semi-regular prediction. If the
   indicator encoding is materially cheaper than the degree-`N` one, Claim B is
   false and the family is not dead.

If either computation contradicts the corresponding claim, the document is
wrong and should be withdrawn rather than patched.

## Preliminary probe (2026-11-06)

`tools/semaev/gb_solving_degree.py` builds a solvable instance, then compares
Groebner bases for the two encodings:

| p | N | encoding | variables | basis size | max basis degree |
|---|---|---|---|---|---|
| 101 | 3 | `prod (x - b)` | 2 | 2 | 2 |
| 101 | 3 | indicators | 8 | 8 | 2 |
| 1009 | 4 | `prod (x - b)` | 2 | 2 | 2 |
| 1009 | 4 | indicators | 10 | 10 | 2 |

Two readings, both provisional. First, the solving degree is **2**, below `N`,
in both encodings and both sizes — direct confirmation that Claim A does not
transfer to the F4 definition. Second, the indicator encoding is not visibly
worse at this scale; the basis grows with the variable count but the degree
does not.

Neither size is large enough to test Claim B: `N` must be big enough for the
degree to climb, and the right observable is a rank profile, not the maximum
degree of a basis of a solvable instance. Treat this as a smoke test of the
harness, not evidence either way.

## Resolution and history

- 2026-11-06: written from a delphi-goal run on prime-field ECDLP; the support
  computation is `tools/semaev/s3_support.py`.
