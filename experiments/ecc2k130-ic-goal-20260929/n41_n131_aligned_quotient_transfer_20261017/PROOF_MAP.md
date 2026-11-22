# Quotient gate proof map

The checked [Lean module](QuotientGate.lean) uses pinned Lean 4.34.1 and
builds with `lean QuotientGate.lean`. The terminal [output](lean.stdout)
contains the `#print axioms` audit: `sound_two_family_filter` uses no axioms;
`finite_feature_separation` and `artin_schreier_curve_lift` use only
`propext`, `Classical.choice`, and `Quot.sound`. The source has no `sorry`,
`admit`, `sorryAx`, or custom axiom.
`lean4checker --fresh` is unavailable on this host.

| Mathematical step | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| An exact two-family sum survives label membership | `sound_two_family_filter` | Any additive commutative group, arbitrary target/suffix and total label map, with an actual witness in both families. Checked. For the reciprocal-x implementation, the target and positive witness have nonexceptional partial points; exceptional values are tracked separately. |
| A feature dependency excludes a feature combination | `finite_feature_separation` | Any field, finite list of scalar-weighted feature functions, a linear functional annihilating each feature, and a nonzero label syndrome. Checked. Taking features `1`, `x_i`, `x_i x_j` gives the degree-at-most-two exclusion. |
| Direct Artin–Schreier point lift | `artin_schreier_curve_lift` | Any field, a nonzero-x inverse-square witness `x*x*invx2=1`, and a solution `v*v+v=x+invx2`. Proves `(x,x*v)` satisfies `y²+xy=x³+1`. Checked. |
| N41 17-dimensional branch quotient | Prior `AlignedSymmetry.pair_root_difference` plus current exact integer-field computation | Prior theorem checks the root-difference identity. The concrete N41 rank and dual masks are independently computed; their matrix certificate is not yet a Lean object. |
| N131 47 label exclusions on 512 source codes | `finite_feature_separation` applies after supplying the left-nullspace witnesses | Independent Sage rebuilt 1,024 field roots, the 512-by-407 feature matrix of rank 407, its 105-dimensional left kernel, and nonzero syndromes for all 47 labels. The 512 code list, finite-field roots, and left-nullspace certificates are not yet encoded and kernel checked in Lean; concrete formalization remains open. |
| Source point pair to quadratic root | `artin_schreier_curve_lift`, prior pair identity, and independent checked-Sage group replay | All 512 sampled source codes had both endpoint points constructed by direct half-trace, and both group-sum reciprocal-x outputs matched the two quadratic roots. The full binary-curve group law and pair-output bridge are not yet encoded as a Lean theorem. |

The readable proof of gate soundness is substitution: if
`target = suffix + (a+b)`, then `target-suffix = a+b`, so applying any
label gives a member of the table for that pair family. A label collision
may admit a false positive but cannot remove the witness when both
partial coordinates are defined.

For the degree screen, represent every Boolean polynomial of degree at most
two in 28 bits as a linear combination of 407 feature columns: one
constant, 28 coordinate columns, and 378 pairwise product columns. A
left-nullspace row that evaluates to one on a label and zero on every
feature contradicts any such representation. The audited 512-row matrix
has rank 407; every one of the 47 label columns has a nonzero syndrome
under its 105-dimensional left kernel. Restriction to this valid source-code
sample is enough to exclude a degree-at-most-two expression over the full
valid-code set. This says nothing about degree-three or other compact
representations.
