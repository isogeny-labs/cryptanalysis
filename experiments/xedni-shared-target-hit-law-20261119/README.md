# Exact public-hit law for shared-target offset queries

The shared-target query law has an **exact expected count of `315799645/18247372 ≈ 17.3066` public relations** across four independent uniform nonzero target scalars per field on the eight frozen subgroups. The two deterministic SHA-derived panels recorded 22 and 14 hits. Both lie within the exact reference distribution: the upper tail at 22 is about 0.1800, and the lower tail at 14 is about 0.2847. This reference accounts for the shared scalar, identity exclusions, first-16 offset-pair selection, and dependence among the 13 vector tests within a query.

## Law and proof

For `U=(w−t₁)G` and `V=(w−t₂)G` in a subgroup of prime order `q`, the fixed vector `(a,b)` gives

`aU+bV=O  ⇔  (a+b)w = a t₁+b t₂ (mod q)`.

Every vector in the frozen family has `a+b ≠ 0 mod q` for all eight subgroups. Hence each fixed vector and offset pair has one root `w` in `ZMod q`; the root may be zero, create an identity input, or fall outside the first 16 selected offset pairs. The runner enumerates all `w=1,…,q−1` and applies those rules. The independent audit reverses the calculation: it indexes the unique root of each vector and offset pair, then admits it only when the pair is selected at that root. Both methods agree on all 3,310 population rows.

The [Lean module](../xedni-affine-reduction-bridge-20261118/SharedTargetRelation.lean) checks the field identity and unique-root theorem. The proof expands the two point coefficients, rearranges the affine equation, and divides by the nonzero sum `a+b`. `unique_target_mod_prime` specializes it to `ZMod q` with `q` prime. The full first-16 selection and the 3,310-row arithmetic census are recorded in Python, with source-panel digests and complete population ledger.

| Result | Lean declaration | Status and hypotheses |
| --- | --- | --- |
| Relation equals one linear target equation | `relation_iff_linear_equation` | Any field; checked |
| One possible target scalar | `unique_target` | Any field, `a+b≠0`; checked |
| Prime-field specialization | `unique_target_mod_prime` | Prime `q`, `a+b≠0` in `ZMod q`; checked |
| Full query-law population and distribution | `run.py`, `audit.py`, `result.json` | First-16 identity filter and all frozen vectors; exact arithmetic and independent root-index audit passed |

## Exact census and reference distribution

| Field `p` | Subgroup `q` | Scalars enumerated | Expected hits in four uniform targets | Height-selected panel | Fresh-wide panel |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 330 | 2.5455 | 1 | 0 |
| 421 | 439 | 438 | 1.9178 | 3 | 0 |
| 431 | 419 | 418 | 2.0096 | 1 | 2 |
| 547 | 571 | 570 | 1.4737 | 6 | 0 |
| 571 | 599 | 598 | 1.4047 | 0 | 4 |
| 593 | 313 | 312 | 2.6923 | 3 | 3 |
| 617 | 293 | 292 | 2.8767 | 6 | 2 |
| 677 | 353 | 352 | 2.3864 | 2 | 3 |
| **Total** | | **3,310** | **17.3066** | **22** | **14** |

The exact total histogram in [result.json](result.json) is the convolution of each field's complete one-target histogram, raised to its four-target count. Its denominator is the product of `(q−1)^4` across the eight fields. The independent audit uses rational-coefficient convolution and checks both inclusive tails. The target scalars in the two observed panels are deterministic SHA outputs; their tail positions describe a specified uniform reference law and are not repeated-sampling uncertainty estimates for those panels.

## Reproduce

```sh
python3 experiments/xedni-shared-target-hit-law-20261119/run.py
python3 experiments/xedni-shared-target-hit-law-20261119/audit.py
cd experiments/xedni-affine-reduction-bridge-20261118
lake build SharedTargetRelation
```

[The protocol](protocol.json) pins both source result hashes, fields, vectors, offsets, population, reference distribution, and failure handling. [The compressed ledger](population.jsonl.gz) has raw and compressed SHA-256 receipts in the result. `run.py` checks the complete original vector ledgers against the frozen scalar and offset law; `audit.py` checks the inverse-root population, exact distribution, and source totals. Lean uses pinned `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. The proof build and `#print axioms` receipt is in the formal directory's `build-shared-target-output.txt`; only standard Lean foundations appear. `lean4checker --fresh` is unavailable on this host.
