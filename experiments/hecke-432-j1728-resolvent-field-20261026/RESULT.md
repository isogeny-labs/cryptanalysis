# Exact coordinate field and quartic–octic C–E resolvent factorization

The level-432 C–E resolvent at a generic source `j=1728` point factors over its degree-18 C-coordinate field as an irreducible quartic times an irreducible octic. An exact coefficient certificate reconstructs the product and its source point. Reducing that certificate at all 66 C points from the fresh-prime factor-parity test reproduces every finite-field factor pattern, including the exchange of which characteristic-zero factor supplies the four linear roots in the `23 mod 24` class.

## Exact construction and verification

The frozen [`protocol.json`](protocol.json) identifies the characteristic-zero source-`j` map, its previously verified degree-18 x-eliminant, and the degree-12 C–E resolvent by hash. Work in `Q[x,y]` with `C: y²+y=x³−7`. Reducing the numerator of `j−1728` modulo the C equation gives a linear equation `A(x)+B(x)y=0`. Let `f(x)` be the monic irreducible degree-18 eliminant, let `K=Q[x]/(f(x))` with `a` the image of `x`, and set `b=−A(a)/B(a)`. The checked identities are `B(a)≠0`, `b²+b=a³−7`, and `j(a,b)=1728`; the coefficient vectors for `A` and `B` are in [`coordinate_field.json`](coordinate_field.json).

Specialize the [relative resolvent](../hecke-432-relative-resolvent-20261025/relative_resolvent.json) at `(a,b)`, obtaining `R(z)∈K[z]` of degree 12. The exact result is

`R(z) = u · Q₄(z) · Q₈(z)`, with `u∈K×`, `deg Q₄=4`, and `deg Q₈=8`.

[`factor_certificate.json`](factor_certificate.json) stores the full rational coefficient vector of the field polynomial, the source `y` expression, the unit, and every coefficient of both factors in the power basis of `K`. [`field_factor_sage.py`](field_factor_sage.py) constructs the specialization and certificate. [`check_certificate_sage.py`](check_certificate_sage.py) separately reconstructs it, verifies exact polynomial equality and irreducibility of both factors over `K`, and checks the C equation. The status in [`certificate_check.json`](certificate_check.json) is `PASS_EXACT_CERTIFICATE_AND_REDUCTIONS`. All Sage jobs used the repository's checked launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) records the accepted runtime.

## Finite-field bridge

The independent checker specializes the exact certificate at each of the 66 C points in the [refined factor-parity test](../hecke-432-j1728-ce-factor-20261026/RESULT.md), verifies the source `y` value and coefficient product modulo `p`, and matches the direct degree-12 resolvent. The factor patterns split as follows:

| Finite prime class and C rows | Quartic reduction | Octic reduction | Total linear roots |
| --- | --- | --- | ---: |
| `23 mod 24`, 3 rows | `1+1+1+1` | `2+2+2+2` | 4 |
| `23 mod 24`, 3 rows | `2+2` | `1+1+1+1+2+2` | 4 |
| `11 mod 24` and ordinary controls, 24 rows | `2+2` | `2+2+2+2` | 0 |
| ordinary controls, 36 rows | `2+2` | `4+4` | 0 |

The table records the 66 checked rows, not a universal splitting law. Its two `23 mod 24` rows explain why counting only total linear roots hid a choice between the two C sheets. The exact quartic–octic factorization provides a smaller object for computing the Frobenius character in the next proof step.

## Proof map and remaining bridge

| Result | Evidence or Lean declaration | Status |
| --- | --- | --- |
| Degree-18 source coordinate field and `b=−A(a)/B(a)` | Exact identities and irreducibility checks in `field_factor_sage.py` and `check_certificate_sage.py`; full vectors in `factor_certificate.json` | Exact computer-algebra certificate; faithful Lean encoding of `K` and the source map remains open |
| `R=uQ₄Q₈` with irreducible degrees 4 and 8 | Exact coefficient multiplication and independent Sage irreducibility checks in `check_certificate_sage.py` | Exact computer-algebra certificate; factor equality and irreducibility are not yet Lean formalized |
| Any root of such a product lies in the quartic or octic | `J1728ResolventField.root_lies_in_quartic_or_octic` in [`FactorRootGate.lean`](formal/FactorRootGate.lean) | Lean 4 proof checked; `#print axioms` reports `propext`, `Classical.choice`, `Quot.sound` |
| Specializations at the 66 finite C points | `certificate_check.json` | Exact replay passed at those rows; good-reduction and Frobenius criteria for arbitrary primes remain open |

The Lean project pins Lean `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. From `experiments/hecke-432-formal-ci-20261025`, the build command is `lake env lean ../hecke-432-j1728-resolvent-field-20261026/formal/FactorRootGate.lean`; its output is in [`lean-check.txt`](formal/lean-check.txt). The module contains no proof escape, and `lean4checker --fresh` was unavailable on this host. The full arithmetic theorem remains open in Lean because the quotient-field definition, 18-degree coefficient identities, and specialized irreducibility certificates have not been encoded there. The next mathematical task is to determine the splitting fields of `Q₄` and `Q₈` over `K` and identify the Frobenius condition behind the observed residue-class pattern.
