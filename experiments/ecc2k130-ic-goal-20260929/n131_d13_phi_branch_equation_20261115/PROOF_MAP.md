# Phi-chart branch proof map

| Result | Declaration or replay | Exact hypotheses and scope | Status |
| --- | --- | --- | --- |
| One polynomial equation selects the original or image phi chart | `BranchEquation.branch_equation` | Any commutative ring, Boolean branch, and `y=phi*phi+phi` | Lean 4.34.1 checked; `#print axioms` lists only `propext`, `Classical.choice`, `Quot.sound` |
| Image phi output is unique | `BranchEquation.image_unique` | Any field, same branch equation, and `1+y != 0` | Lean 4.34.1 checked; same standard foundations |
| Adjacent image point has reciprocal x-coordinate `y=phi²+phi` | Earlier `Adjacent.lean` polynomial proof and `n131_d13_phi_raw_fiber_20261115/audit_sage.py`; current `audit.py` | The exact curve `y²+xy=x³+1`, `x=1+1/phi`, nonexceptional valid d13 selectors | Group-law bridge to Lean remains partial; prior independent Sage replay covers all 4,134 selectors; new chart-specific Sage pass capped at 180 seconds |
| Image denominator is nonzero | Written trace argument and both finite audits | In `GF(2^131)`, `Tr(phi²+phi)=0` and `Tr(1)=1` | Written proof plus exact 4,134-selector checks; full Lean finite-field trace bridge open |
| Sparse branch-product gate count | Constructive expansion in `RESULT.md` | 13 source bits, 131 field bits, ten leaves | Derived Boolean circuit bound; no generated ten-leaf formula yet |

For a valid source selector, set `phi=1/(x+1)` and `y=phi²+phi`.
The adjacent image satisfies `x(P+tau(P))=1/y`, so its chart is
`phi_image=1/(1+1/y)=y/(1+y)`. Since `y` has trace zero in the odd-degree
field and `1` has trace one, `1+y` is nonzero. Let `b` be zero for the
original source and one for the image. The equation
`(1+b*y)*phi_out=phi+b*phi²` becomes `phi_out=phi` for `b=0`, and
`(1+y)*phi_out=y` for `b=1`; the latter uniquely gives `phi_image`.

The Lean file proves the branch algebra and uniqueness without axioms that
encode the research result. The existing adjacent-x polynomial proof and
the prior exact Sage curve replay support the concrete characteristic-two group
identity. The current chart-specific Sage attempt is capped as recorded in
`audit_sage_status.json`. Building a full Lean elliptic-curve group law, Frobenius map, and
`GF(2^131)` trace bridge remains the specific open formalization obligation.

Build command: `lean BranchEquation.lean` from this directory. The pinned
toolchain is `leanprover/lean4:v4.34.1`; `lean.stdout` retains the axiom
audit. `lean4checker --fresh` is unavailable on this host.
