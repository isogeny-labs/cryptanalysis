# Blind mathematical brief: centered interval

Assess the following natural-number statement independently. Do not read
the Lean source/proof, proof map, review plan, README, receipts, or another
reviewer's material.

For arbitrary natural numbers `r`, `radius`, `center`, `n`, `m`, `k`, `l`,
assume:

1. `radius + radius < r`;
2. `n = k*r` and `m = l*r`;
3. `center ≤ n+radius` and `n ≤ center+radius`;
4. `center ≤ m+radius` and `m ≤ center+radius`.

Requested conclusion: `n=m`. Derive it or find a counterexample. Test whether
the premises are satisfiable and whether the strict diameter bound matters.
State precisely what this implication would and would not prove about a
concrete elliptic-curve order certificate. List every source actually read
and disclose any forbidden access.
