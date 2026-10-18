# Reciprocal exception proof map

The first two aligned W29 slots have equal Frobenius rotation zero. Their
source products range over the same 28-dimensional binary subspace generated
by `PB`, independently of whether a product code is a curve-valid source.
The SAT circuits search this larger domain, so a certified exclusion on the
larger domain would also exclude a two-torsion intermediate from the
curve-valid domain. Solver caps are recorded as bounded searches.

| Mathematical step | Lean declaration | Hypotheses and scope | Status |
| --- | --- | --- | --- |
| Roots of the two fixed-seed pair quadratics are forced to `u=Cp+Hq`, `v=Hp+Cq` when `uv=1` | `PairException.reciprocal_roots_linearize` | Arbitrary characteristic-two field, `C+H=1`, `uv=1`, both quadratics | Checked |
| Reciprocal roots force `(Cp+Hq)(Hp+Cq)=1` | `PairException.reciprocal_roots_force_product_one` | Same field and hypotheses | Checked |
| Substitution `q=p+s` gives `p²+ps+CHs²` | `PairException.sparse_product_identity` | Arbitrary characteristic-two field, `C+H=1`, `q=p+s` | Checked |
| Adding `T=(0,1)` maps nonzero `x` to `1/x` on `y²+xy=x³+1` | `PairException.two_torsion_translate_x` | Arbitrary characteristic-two field, nonzero `x`, affine curve equation | Checked as the affine coordinate identity |
| `CH=s²` follows from `C+H=1` and `H²+H=s²` | `PairException.seed_square_factorization` | Arbitrary characteristic-two field and stated equations | Checked |
| An additive functional that vanishes on the three sparse terms and maps `1` to `1` excludes the equation | `PairException.additive_separator` | Arbitrary field, additive functional and term-value hypotheses | Checked |

The Lean module does not yet define elliptic-curve points or the group law.
Consequently the structural bridge `P+Q=T ⇒ x(P)x(Q)=1` is represented by
the standard affine addition formula and the two-torsion coordinate lemma,
but is not itself a Lean theorem about curve points. The exact N131 circuit
bit-vector semantics and the W29 source construction are checked by the
frozen Sage build and its sampled pair-root identities, not by Lean. A full
formalization would define the N131 field quotient, curve points, affine
group law, and circuit-to-field decoding.

The full fixed-instance exclusion is given by the explicit
`linear_certificate.json` parity mask and generator checks, independently
replayed in `linear_certificate_sage_replay.json`. The statement for all
`p,d∈V` follows by binary linearity of square, product and coefficient
extraction. This finite-field generator check has no faithful Lean theorem
yet; its formalization remains partial rather than presenting the checked
abstract identities as a complete Lean proof of the N131 result.

The proof was checked with pinned `lean-toolchain` (`leanprover/lean4:v4.34.1`)
by `lean PairException.lean`; command output is in `lean_check.log` and exit
status in `lean_exit_code.txt`. Every theorem is audited by `#print axioms`.
Only `propext`, `Classical.choice`, and `Quot.sound` occur. `lean4checker`
was unavailable on this host.
