# Direct level-432 source-chain reconstruction at p=883 and p=997

The inverse algorithm recovers the unique cyclic 16/27 source-chain pair for each of 864 rational `(C,E,B)` triples at p=883 and 1,800 at p=997. It derives the source and intermediate j-invariants from `C`, constructs the canonical source curve, enumerates 2- and 3-isogeny paths, filters the 27 path by its j-sequence, and evaluates the corresponding forward B map. Every forward evaluation matched its frozen inverse triple. An independent comparison with the source censuses recovered the same 2,664 chain keys, with no missing, extra, or incorrect candidate sets.

| Prime | Exact input triples | Distinct C points | Forward evaluations | Matched | Candidate multiplicity | Independent audit |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| 883 | 864 | 216 | 864 | 864 | 864 single | pass |
| 997 | 1,800 | 342 | 1,800 | 1,800 | 1,800 single | pass |

The input is the exact GCD inverse's rational `C,E,B` triples. The producer loads neither source census nor forward image table; those are audit-only inputs in [`protocol.json`](protocol.json), frozen with SHA-256 before execution. At p=883 it selects the generic source curve or its quadratic twist by positive trace 20 or 52 and evaluates the kernel-transport B image. At p=997 it uses the canonical generic source curve and the three B preimages associated with its E projection. The source model, path indices, and exact `C,E,B` point are retained for every candidate in the 250-row shards listed in [`result.json`](result.json).

The pure-Python [`audit.py`](audit.py) reconstructs the p883 source keys from the independent full chain census and image table, locating `C` by the four j-functions. At p=997 it uses the independent original C lift and exact B-fiber allocation. It verifies source path indices, E/B compatibility, exact inverse-triple coverage, and equality of every chain-candidate set. See [`audit.json`](audit.json).

Run from the repository root:

```sh
./sage --runtime-info > experiments/hecke-432-direct-chain-crossprime-20261025/sage-runtime-info.txt
./sage -python experiments/hecke-432-direct-chain-crossprime-20261025/recover_sage.py
python3 experiments/hecke-432-direct-chain-crossprime-20261025/audit.py
cd experiments/hecke-432-direct-chain-crossprime-20261025/formal && lean ChainCoverage.lean
```

The checked Lean/Std theorem `generated_keys_perm_sources` proves that duplicate-free generated keys contained in a duplicate-free source list of the same length 2,664 form a permutation. The `source_count` theorem checks 864 + 1,800 = 2,664. The build and `#print axioms` output are in [`formal/build-output.txt`](formal/build-output.txt), with pinned compiler and dependency information in [`formal/DEPENDENCIES.json`](formal/DEPENDENCIES.json). Lean uses only `propext`, `Classical.choice`, and `Quot.sound` for the list theorem. Formalization of the elliptic-curve path enumeration and C/E/B map equality remains open; the finite-field implications are checked by the frozen producer and independent audit.

This extends the p887 direct inverse of PR #1140 to the two other measured primes. The next experiment is to replace source-curve path enumeration with a direct algebraic lift from the recovered `(C,E,B)` point and compare the exact candidate sets on these frozen inputs.
