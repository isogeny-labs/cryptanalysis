# A square-three obstruction for the level-432 source fiber

**Theorem (source fiber).** Let `p>5` be prime, let `C/F_p` be `y²+y=x³−7`, and use the rational source-`j` map fixed in the [coordinate bridge](../hecke-27-coordinate-bridge-20261025/coordinate_map.json). If `3` is a nonsquare in `F_p`, there is no point of `C(F_p)` at which that map is defined and has value `1728`. Equivalently, the rational source fiber is empty for every prime `p>5` with `p ≡ 5` or `7 (mod 12)`. An exact resultant identity, an integer `√3` witness, and direct audits of the three denominator exceptions prove the statement.

The same computation identifies a smaller splitting-field gate for the C–E resolvent. Its degree-18 source coordinate field already contains `√3`. Adjoining `√2` factors the certified quartic as `2+2` and the octic as `4+4`; adjoining `i`, `√−2`, `√−3`, or `√−6` leaves both irreducible. These exact field results guide the remaining Frobenius analysis of the C–E correspondence.

## Written proof of the source-fiber theorem

Write the source map as `j=−n(x,y)/d(x,y)` and set `h=n+1728d`. Every coefficient denominator of `n` and `d` has only `3` and `5` as prime factors. The [previously established eliminant](../hecke-432-j1728-cubic-twist-holdout-20261026/elimination_result.json), recomputed in [`theorem_audit.py`](theorem_audit.py), gives the exact identity over `Q[x]`

`Res_y(h, y²+y−x³+7) = f(x)² / (3³⁰·5²)`,

where `f∈Z[x]` is monic of degree 18. For `p>5`, all displayed rational coefficients reduce and the scalar is nonzero. A rational C point with defined source `j=1728` gives a common y-root of `h` and the C equation, so `f(x)=0` in `F_p`.

[`sqrt3_certificate.json`](sqrt3_certificate.json) supplies integer polynomials `P,H` and a positive integer `D` with the exact identity

`P(x)² − 3D² = f(x)H(x)`.

The independent integer-polynomial replay in [`audit_sqrt3.py`](audit_sqrt3.py) checks every coefficient. When `p∤D`, a root of `f` would make `(P(x)/D)²=3` in `F_p`, contrary to the theorem's nonsquare hypothesis.

The complete prime factorization of `D` is `2·3²⁷·199·2917·5023·47809·154333·19441459`. Among primes `p>5` where `3` is nonsquare, only 199, 5023, and 19,441,459 divide `D`. At each one, [`check_exceptions_sage.py`](check_exceptions_sage.py) and the independent [`audit_exceptions.py`](audit_exceptions.py) factor `f` modulo `p`: it has exactly one rational x-root, of multiplicity two. The C-curve y-discriminant `4x³−27` at that root is a nonsquare (respectively 186, 3421, and 10,814,804 modulo the three primes). Thus no y lifts the exceptional x-root to a rational C point. This completes the prime cases in the theorem.

[`theorem_receipt.json`](theorem_receipt.json) binds the resultant, integer identity, complete denominator factorization, and exceptional-prime checks to their source hashes. The earlier bounded screens—110 primes in the `5 mod 12` class and 58 in the `7 mod 24` class—also satisfy the theorem's conditions and are checked in [`sqrt3_audit.json`](sqrt3_audit.json). Those finite screens are corroboration; the proof uses the exact identities and exhaustive denominator exceptions.

## Quadratic extension screen

[`protocol.json`](protocol.json) froze the seven rational radicands before the extension factorizations. [`quadratic_screen_sage.py`](quadratic_screen_sage.py) uses the exact [quartic–octic certificate](../hecke-432-j1728-resolvent-field-20261026/factor_certificate.json) over the degree-18 field `K`. All seven cells and their exact factor degrees are in [`quadratic_result.json`](quadratic_result.json).

| Radicand `d` | Field relation | Quartic degrees over `K(√d)` | Octic degrees over `K(√d)` |
| ---: | --- | --- | --- |
| `3` | `√3∈K` | `4` | `8` |
| `2`, `6` | genuine quadratic extension | `2+2` | `4+4` |
| `−1`, `−2`, `−3`, `−6` | genuine quadratic extension | `4` | `8` |

The `√3` inclusion has the explicit `P/D` witness above. The `√2` factorization is an exact computation over a relative degree-two extension; the next certificate task is to export its factor coefficients and relate their Frobenius permutations to rational C–E pairs. All new Sage runs used the repository's checked launcher; the accepted runtime is in [`sage-runtime-info.txt`](sage-runtime-info.txt).

## Lean proof map

The pinned Lean project uses Lean `v4.35.0-rc4` and Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. [`SquareThreeGate.lean`](formal/SquareThreeGate.lean) contains two checked implications:

| Declaration | Exact hypotheses and conclusion | Status |
| --- | --- | --- |
| `J1728SquareThreeGate.no_eliminant_root_from_sqrt_three_certificate` | Over any field, a polynomial identity `P²−3D²=fH`, `D≠0`, and nonsquare `3` imply `f` has no root | Checked; `#print axioms` lists `propext`, `Classical.choice`, `Quot.sound` |
| `J1728SquareThreeGate.curve_discriminant_is_square` | Over a commutative ring, `y²+y=x³−7` implies `(2y+1)²=4x³−27` | Checked; `#print axioms` lists `propext`, `Quot.sound` |

The build output is [`lean-check.txt`](formal/lean-check.txt), produced with `lake env lean -R /Volumes/SSD990/cryptanalysis /Volumes/SSD990/cryptanalysis/experiments/hecke-432-j1728-quadratic-extensions-20261026/formal/SquareThreeGate.lean` from the pinned Hecke Lean project. There are no proof escapes. `lean4checker --fresh` is unavailable on this host. Formalization of the full theorem remains **partial**: the exact 18-degree polynomial identity, source-map resultant identity, and three complete exceptional-prime root factorizations have not been encoded as Lean certificates. The theorem's written proof and exact replay artifacts remain the authoritative result while that bridge is open.
