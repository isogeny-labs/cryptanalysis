# A multiplicity-aware Hecke collector recovers nine complete rows

The new [collector](multiplicity.py) reconstructs complete rational
Hecke fibers when two neighbors share an x-coordinate. On four frozen
`D_K=-7` classes it recovers **nine previously omitted rows**: three at
conductor 42, and two each at conductors 70, 150, and 210. Every
previously accepted neighbor multiset is preserved. The augmented row
multisets close under the Fricke involution in all four cases.

| Reached conductor | Degrees | Old rows | Recovered rows | Fricke row pairs | Exact rank before → after |
| ---: | --- | ---: | ---: | ---: | ---: |
| 42 | 2, 3, 7 | 129 | 3: two degree 2, one degree 7 | 66 | 104 → 104 |
| 70 | 2, 5, 7 | 170 | 2: degree 2 | 86 | 140 → 140 |
| 150 | 2, 3, 5 | 656 | 2: degree 2 | 329 | 500 → 500 |
| 210 | 2, 3, 5, 7 | 1082 | 2: degree 2 | 542 | 784 → 784 |

The [protocol](PROTOCOL.md) fixed all four raw matrices, source hashes,
degree supports, and acceptance checks before the replay. The collector
uses the unchanged archived Hecke function source by its SHA-256 digest.
For a degree-`ell` polynomial, it requires `ell+1` rational roots counted
with multiplicity. A Vandermonde solve on the **distinct** x-roots
recovers their aggregate y-coordinates. It enumerates point counts among
the curve lifts of each x-root and accepts a unique multiset only when
every x/y power sum and the elliptic-curve Hecke group sum match. It
returns explicit statuses for missing rational roots, inconsistent
moments, missing or ambiguous y-assignments, and a 65,536-assignment
resource cap. Simple-root fibers use the original code path.

The checked-Sage [replay](replay.json) examined every saved point and
Hecke degree. All nine new rows have points inside their saved class,
satisfy the classical modular polynomial, and pass the group sum.
There were zero mismatches against previously accepted neighbor
multisets. Exact rational rank and ranks modulo 23 and 1,000,000,007
agree in every before/after cell. The [independent integer
validator](validation.json) uses separate affine point arithmetic and
sparse modular elimination to replay all nine new group sums and both
modular ranks. The [runtime receipt](runtime-info.json), stdout, and
stderr retain the execution context.

The degree-7 double-x fiber found in
[PR #1201](https://github.com/isogeny-labs/cryptanalysis/pull/1201) is
one positive control. The eight additional degree-2 rows show that the
coverage issue also appears in otherwise complete class matrices. The
rank identity observed for these four matrices survives their insertion;
the stronger conclusion is that the saved relation **ledger** was
incomplete even where its rank was stable. This remains a relation-stage
diagnostic with `candidate_id: null` and `timing_claim: null`.

**Proof and verification boundary.** The point multiset is accepted by
directly checking the defining moment and group equations, so its
correctness on the four exact fields is established by executable
certificates and the independent replay. The generic claim that every
moduli-theoretic Hecke fiber is represented by these q-expansion
functions remains the source theorem used by the archived producer; a
Lean formalization of the full modular curve and these rational
functions is still open. This bundle adds an implementation improvement
and measured coverage result, not a new general mathematical theorem.
