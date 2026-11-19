# Exact root census for a fixed xedni relation family

The 13 frozen coefficient vectors and all 56 ordered distinct pairs from eight frozen offsets produce **419 distinct nonzero public-relation roots** at each of the tested prime subgroup orders 10,007 and 65,537. At order 1,009 they produce 406. The exact census and an independent forward-equation audit agree. These are necessary public-relation hits; a selected lift relation can only occur at a root and may occur at fewer scalars.

## Frozen law

`protocol.json` was committed before the run. It copies the vectors and offsets from the earlier shared-target protocol, pinned by SHA-256 `9348d6c7eecb4c6096ef9116c5e8263f9cf1fa209bf26789cd148a5601a3c62f`. Every ordered pair of distinct offsets is admitted, without the earlier first-16 query selection. For each pair `(t1,t2)` and coefficient vector `(a,b)`, the program solves the exact modular equation `(a+b)w = a*t1+b*t2` and counts distinct nonzero roots among all `w=1,…,q−1`. All coefficient sums are nonzero at the three frozen prime orders.

| Prime order `q` | Pair capacity `13·56` | Distinct nonzero roots | Missed nonzero targets | Lean capacity lower bound on misses | Duplicate pair roots |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1,009 | 728 | 406 | 602 | 280 | 321 |
| 10,007 | 728 | 419 | 9,587 | 9,278 | 308 |
| 65,537 | 728 | 419 | 65,117 | 64,808 | 308 |

The Lean theorem `missed_nonzero_target_count_lower_bound` proves at least `q−1−728` missed scalars for any selector satisfying its additive-reduction hypotheses. This census gives the exact necessary public-root count for the frozen family, including root collisions. The matching 419 counts at the two larger tested orders suggest a finite rational-root plateau; proving a threshold for all larger primes is a separate exact-arithmetic and Lean task.

## Rational-root plateau certificate

The separately frozen `plateau-protocol.json` checks the rational roots before modular reduction. `plateau.py` uses Python's exact `Fraction` arithmetic; `plateau-audit.py` independently normalizes integer numerator-denominator pairs with `gcd` and recomputes all pairwise cross-determinants. Both report 420 distinct rational roots, 419 nonzero roots, maximum reduced denominator 11, and maximum absolute cross-determinant 2,046. Source and protocol hashes are retained in `plateau-result.json`; `plateau-audit-output.txt` records the independent replay.

These finite facts imply the following mathematical statement. For a prime `q > 2046`, every reduced denominator is nonzero modulo `q`. Any two distinct canonical fractions have a nonzero integer cross-determinant whose absolute value is below `q`, so their modular images remain distinct. Zero stays zero. Therefore the 728 coefficient-offset combinations have exactly **419 distinct nonzero modular roots** for every prime `q > 2046`. The proof accounts for the observed 419 counts at 10,007 and 65,537; the 1,009 row lies below the threshold and has additional modular collisions.

`FixedFamilyRationalRootPlateau.lean` checks the 728-case rational enumeration in 13 chunks, its 420 distinct reduced fractions and 419 nonzero fractions, denominator bound 11, numerator absolute bound 191, and pairwise determinant nonvanishing. The coordinate bounds give a checked conservative determinant bound 4,202, from which `canonical_modular_roots_card_419` proves 419 nonzero modular images for every prime `q > 4202`. The exact 2,046 determinant bound is established by the independent exact-arithmetic replays but has not been kernel-checked. A generic Lean equality between each raw modular coefficient-offset quotient and its normalized rational-fraction image remains to be proved. Thus the written `q > 2046` raw-family theorem has **partial Lean formalization**, while the canonical-image `q > 4202` theorem is checked.

## Reproduce

From the repository root:

```sh
python3 experiments/xedni-fixed-family-root-census-20261119/run.py
python3 experiments/xedni-fixed-family-root-census-20261119/audit.py
python3 experiments/xedni-fixed-family-root-census-20261119/plateau.py
python3 experiments/xedni-fixed-family-root-census-20261119/plateau-audit.py
```

`run.py` indexes unique modular roots. `audit.py` independently checks the relation equation for every scalar, coefficient vector, and offset pair, verifies one solution per pair, and recomputes all counts. `result.json` retains the protocol and both source hashes; `audit-output.txt` retains the replay output. The experiment uses only public modular arithmetic and the Python standard library. The protocol's 90-second cap was met by both commands.
