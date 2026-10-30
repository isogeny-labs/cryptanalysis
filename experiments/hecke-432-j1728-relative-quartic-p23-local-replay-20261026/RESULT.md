# Direct local resolution of the two p=23 quadratic clusters

The two doubled irreducible quadratic residue clusters left open after the simple-factor and doubled-linear calculations both split into **two local factors of relative degree 2**. This independently verifies the `[2,2]` entries in the complete p=23 splitting table of the preceding quartic experiment; its global-discriminant parity argument is not an input to this replay.

| Quartic side | Base place index | Residue quadratic `h(u)` | Taylor coefficients `(A,B,C)` in `F_23[u]/(h)` | Discriminant | Relative degrees |
| --- | ---: | --- | --- | --- | --- |
| left | 0 | `u² + 2u + 17` | `(5, 5u + 2, 7u + 21)` | `14u + 10` | `[2,2]` |
| right | 3 | `u² + 2u + 17` | `(5, 13u + 8, 2u + 12)` | `14u + 10` | `[2,2]` |

For each frozen place `P`, `run_sage.py` reconstructs the degree-36 base field and exact quartic from hashed certificates, checks the place generators against the earlier local screen, and verifies that `P` has absolute ramification index one and the quartic has zero maximal relative discriminant valuation. It lifts the monic irreducible residue quadratic `h` to a monic `H` over the number field and reduces `g`, `g'`, and `g''` modulo `H`. The coefficients of `g mod H` have `P`-valuation at least 2, and those of `g' mod H` at least 1. Thus `g(u+23t)/23²` has an integral quadratic reduction over the degree-two residue extension with coefficients `(A,B,C)` shown above. Both leading coefficients and discriminants are nonzero.

The exact square identity

`(10 + 13u)² = 14u + 10` in `F_23[u]/(u² + 2u + 17)`

gives two distinct roots of each normalized Taylor quadratic. Hensel lifting supplies the two local roots in the unramified quadratic extension above each cluster, so the quartic has two degree-two factors over the original local base field. `audit.py` recomputes both Taylor discriminants and the square-root identity using separate integer-pair arithmetic modulo 23; it also checks the two entries against the prior complete splitting table. The checked-Sage run took 18.02 seconds. The initial representative-lift assertion failed before the Taylor calculation because its leading coefficient was a local unit rather than exactly one; `attempt_lift_normalization_error.json` preserves that attempt, and the completed run normalizes the lift to a monic polynomial.

## Proof map

`formal/P23ResidueSquare.lean` proves both Taylor-discriminant identities and the explicit square identity in every commutative ring with `23 = 0` and `u² + 2u + 17 = 0`. All three declarations build and use only standard Lean foundations, as recorded in `formal/lean-check.txt`. The full Lean number-field theorem remains open at the exact residue-field identification, valuation-to-scaled-Taylor construction, and local Hensel descent to prime ideals. The mathematical argument and exact computation above retain those bridges explicitly.
