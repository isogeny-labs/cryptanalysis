# Proof map for the removable j-map branch

`NormBranch.lean` pins the exact integer coefficient polynomials `a`, `b`
from `jfun.json` (`A(x,y)=a(x)+b(x)y`). Its `X011.norm_factor` proves for
every integer `x` that the numerator norm on
`y²+y=x³−x²−10x−20` equals `(x−16)^11 q(x)`.
This is an independent check of an identity and regularization already
formalized more fully in the archived D=−1407 module
`experiments/hecke-d1407-f6-20261023/formal/RegularBranch.lean`.
`X011.branch_values` checks `A(16,60)=0`, the nonzero conjugate numerator
`A(16,-61)=81402749386839761113321`, and
`q(16)=−121 A(16,-61)`. Both declarations are kernel-checked with no
research axioms, `sorry`, or `admit`. Their axiom output contains only
Lean's standard `propext` and `Quot.sound` foundations.

The written argument in `AMENDMENT.md` supplies the local-ring bridge:
when `2·60+1=121` is invertible in the field, `u=x−16` is a local
parameter. The conjugate numerator is a unit at `(16,60)`. Dividing the
norm factorization by that unit yields the regular local value `−121`.
This local-ring implication and the modular interpretation of the pinned
`j` table are not encoded in Lean here. Thus the formalization is partial
for the full modular-curve statement; the exact integer polynomial
identities are fully checked.

Build and axiom audit command (from the pinned existing mathlib project):

```sh
cd /Volumes/SSD990/cryptanalysis/experiments/xedni-lattice-obstruction-20261028/formal
lake env lean /Volumes/SSD990/x011-fiber-multiplicity-worktree-20261119/experiments/hecke-x011-trace-fiber-census-20261119/formal/NormBranch.lean
```

The local formal directory records the same Lean toolchain and mathlib
revision. `lean4checker --fresh` was unavailable on this host.
