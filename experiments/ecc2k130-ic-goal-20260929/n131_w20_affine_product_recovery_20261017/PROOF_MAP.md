# Affine recovery proof map

For the characteristic-two target quadratic `A d²+B d+D=0` and right pair
quadratic `C d²+p d+H=0`, assume an explicit inverse `inverseD` with
`D*inverseD=1`. The S3 equation gives
`d*((A*d+B)*inverseD)=1`. Replacing `1/d` in the pair equation yields the
affine product expression

`p=(C+H*A*inverseD)*d+H*B*inverseD`.

| Result | Lean declaration | Hypotheses | Status |
| --- | --- | --- | --- |
| Recovered product satisfies the pair law | `AffineRecovery.recovered_product_satisfies_pair` | commutative ring, `2=0`, S3, inverse of `D` | Checked |
| S3 root inverse | `AffineRecovery.s3_root_inverse` | same | Checked |
| Genuine pair product is unique | `AffineRecovery.recovered_product_unique` | preceding plus pair law | Checked |

The pinned `leanprover/lean4:v4.34.1` module is
[`AffineRecovery.lean`](AffineRecovery.lean). The recorded `lean
AffineRecovery.lean` run passed; `#print axioms` for all three declarations
lists only `propext`, `Classical.choice`, and `Quot.sound`. The archived
source table and independent full-candidate audit check the computational
bridge to the exact N131 W20 source and frozen target fixture.
