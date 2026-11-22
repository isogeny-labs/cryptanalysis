# Source-field ramification and order-index gate

The degree-18 j=1728 source field has exact discriminant **`2^18 · 3^45`**. Among the primes common to the relative-discriminant and conjugate-resultant roots in [the preceding experiment](../hecke-432-j1728-root-prime-support-20261026/RESULT.md), only 2 and 3 ramify in this source field. The remaining common primes 7, 11, 23, and 31 are absent from both the source-field discriminant and the index of `Z[α]` in its maximal order. Thus their appearance in the factor-discriminant roots comes from the factor extensions or their relative geometry, rather than ramification of the degree-18 base field.

The monic defining polynomial `f` is the exact one in the frozen [factor certificate](../hecke-432-j1728-resolvent-field-20261026/factor_certificate.json). Its discriminant and maximal-order index satisfy

`disc(f) = disc(K) · [O_K : Z[α]]²`.

The complete index factorization is

`2^18 · 3^276 · 199 · 2917 · 5023 · 47809 · 154333 · 1098287 · 1237499 · 5382037 · 19441459`.

| Prime | `v_p(disc(f))` | `v_p(disc(K))` | `v_p([O_K:Z[α]])` | `f mod p` pattern |
| ---: | ---: | ---: | ---: | --- |
| 2 | 54 | 18 | 18 | one linear and one quadratic factor, each exponent six |
| 3 | 597 | 45 | 276 | one linear factor, exponent eighteen |
| 7 | 0 | 0 | 0 | nine distinct quadratics |
| 11 | 0 | 0 | 0 | two distinct linears and eight distinct quadratics |
| 23 | 0 | 0 | 0 | two distinct linears and eight distinct quadratics |
| 31 | 0 | 0 | 0 | nine distinct quadratics |

[`protocol.json`](protocol.json) binds the factor and root-support inputs and the 240-second cap. The checked Sage run completed in about two seconds; its runtime selection is in [`sage-runtime-info.txt`](sage-runtime-info.txt), its exact values and finite-field factorizations in [`result.json`](result.json), and its receipt in [`attempt.json`](attempt.json). [`audit.py`](audit.py) independently recomputes the polynomial discriminant and all displayed mod-prime factor degrees with SymPy, checks the index identity and valuations, and reconstructs the complete index factorization using trial-prime checks; see [`audit.json`](audit.json).

An additional bounded checked-Sage run constructed an explicit integral basis. Its trace Gram determinant equals `disc(K)`, and the determinant of its coordinates in the power basis has absolute value `1/[O_K:Z[α]]`. The basis vectors and determinant certificate are in [`basis_result.json`](basis_result.json), with the frozen [`basis_protocol.json`](basis_protocol.json) and [`basis_attempt.json`](basis_attempt.json) receipt.

## Proof map

| Result | Lean declaration | Scope and status |
| --- | --- | --- |
| Trace Gram determinant under a basis change | `J1728FieldIndex.gram_change_basis` | Arbitrary commutative ring and square matrices; kernel checked |
| Exact polynomial/field/index integer identity | `J1728FieldIndex.polynomial_field_index_identity` | Saved source-field integers; kernel checked |
| Complete field discriminant factorization | `J1728FieldIndex.field_discriminant_factors` | Exact 27-digit integer; kernel checked |
| Complete order-index factorization | `J1728FieldIndex.order_index_factors` | Exact 183-digit integer; kernel checked |

[`formal/lean-check.txt`](formal/lean-check.txt) records the actual builds, `#print axioms` results, toolchain, and dependency revision. No claim-specific axioms or placeholders occur in the proofs. The full Lean bridge from this concrete degree-18 field and its integral basis to the two saved discriminants remains open; checked Sage supplies the field and basis computations, while Lean checks the general determinant transformation and exact integer identities. The next experiment should form the relevant relative discriminant ideals at 7, 11, 23, and 31 and determine their local splitting or inertia behavior in the factor extensions.
