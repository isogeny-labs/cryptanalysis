# Certified quartic splitting components at four odd primes

The two degree-four factors over the degree-36 field each have at least the following distinct degree-two prime components. A monic integral quartic's exponent-one factors modulo a base prime lift uniquely by the coprime Hensel factorization theorem. The frozen local polynomial reductions supply those factors, and the preceding relative-discriminant calculation shows that the selected primes are unramified in the maximal relative order.

| Rational prime | Certified degree-two primes, left | Certified degree-two primes, right | Certified absolute degree mass per side | Unresolved absolute degree mass per side |
| ---: | ---: | ---: | ---: | ---: |
| 7 | 48 | 48 | 96 | 48 |
| 11 | 60 | 60 | 120 | 24 |
| 23 | 48 | 48 | 96 | 48 |
| 31 | 66 | 66 | 132 | 12 |

Each side has absolute degree 144. `squarefree_cert.py` derives the component and mass table from the prior checked-Sage local reductions, retaining every repeated residue block as unresolved degree mass. The exact per-place and per-factor records are in `squarefree_result.json`; `audit.py` checks frozen input hashes, degree accounting, and bounded run receipts. A simple factor inside a repeated reduction contributes a certified component; the repeated block's internal splitting is left open.

## Direct relative-field computation

`run_sage.py` attempts complete degree-144 prime decomposition with PARI `rnfinit` and `rnfidealprimedec`, under `protocol.json`'s 600-second limit. All jobs used the checked repository Sage launcher, whose runtime receipt is `sage-runtime-info.txt`.

| Attempt | Outcome | Elapsed seconds |
| --- | --- | ---: |
| 1 GiB PARI stack | stack exhaustion in `rnfinit` | 63.097 |
| 2 GiB PARI stack | stack exhaustion in `rnfinit` | 69.713 |
| 4 GiB, initial binding | `rnfinit` completed; Python argument error, subsequently corrected | 279.326 |
| 4 GiB, uninstrumented retry | `TIME_LIMIT` | 600.284 |
| 4 GiB, checkpoint retry | `rnfinit` completed and saved a 9,260,825-byte binary checkpoint; `TIME_LIMIT` | 600.355 |
| 4 GiB, checkpoint loaded | `TIME_LIMIT` before a prime-7 row | 600.259 |

The direct prime-decomposition status is `BOUNDED_UNKNOWN` for all four selected primes in this 4 GiB, 600-second route. The checkpoint is a PARI `writebin` object bound to its architecture and protocol hash; it is retained to continue without rebuilding the relative field. `attempt*.json` files preserve the exact terminal statuses and phase output.

## Proof map and next computation

`formal/SquarefreeMass.lean` proves the structural partition of local degree mass into exponent-one and repeated blocks and checks the four absolute mass identities. Its `#print axioms` audit uses standard Lean foundations. Formalization of the field-level Hensel lift and the link from the frozen Sage residue factors to number-field prime ideals remains open; the formalization status of that bridge is **partial**. The mathematical argument uses the monic integrality and coprime exponent-one factors recorded in `squarefree_result.json`.

The next experiment should factor each unresolved repeated block over its local completion, with its base prime, precision, and termination bound recorded. This targets the 48, 24, 48, and 12 remaining absolute degree units per side without rebuilding the full relative field.
