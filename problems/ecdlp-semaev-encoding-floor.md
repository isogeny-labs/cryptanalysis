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

### Claim

Let `B` be a factor base of size `N`, and let the membership condition be a
polynomial `C(x)` of degree `N`. For the system

```
S_m(x_1, ..., x_{m-1}, x_R) = 0
C(x_i) = 0                        for i = 1..m-1
```

the degree of regularity satisfies `d_reg >= N`, for every `m` and every
coordinate function `h` used to build `S_m`.

### Argument

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
- It assumes `d_reg` is defined via the Macaulay/F4 degree, and that membership
  is imposed by a single degree-`N` polynomial. Encodings using `N` auxiliary
  variables (boolean indicators) escape the letter of the claim while paying
  the same cost in dimension; that case needs its own statement.
- The `p^{1/(18 omega)}` threshold is the constant from the cost model in the
  delphi brief; changing the model changes the exact shortfall, not the
  asymptotic gap `p^{1/3}` vs `p^{1/36}`.
- Nothing here says anything about `m >= 4` with `m` growing; the claim is
  uniform in `m`, but the threshold arithmetic is not.

## Next discriminating step

Formalize the claim for the two-variable case (`m = 3`, `C(x_1), C(x_2)`) as a
statement about the initial ideal, and check it against a Macaulay rank
computation at `p = 2^10`, `N = 2^3`: the measured `d_reg` should be `>= N`
and the rank profile should show the degree-`N` jump when `C` enters. If it
does not, the argument above is wrong and should be withdrawn.

## Resolution and history

- 2026-11-06: written from a delphi-goal run on prime-field ECDLP; the support
  computation is `tools/semaev/s3_support.py`.
