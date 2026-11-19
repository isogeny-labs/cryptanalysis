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

## Reproduce

From the repository root:

```sh
python3 experiments/xedni-fixed-family-root-census-20261119/run.py
python3 experiments/xedni-fixed-family-root-census-20261119/audit.py
```

`run.py` indexes unique modular roots. `audit.py` independently checks the relation equation for every scalar, coefficient vector, and offset pair, verifies one solution per pair, and recomputes all counts. `result.json` retains the protocol and both source hashes; `audit-output.txt` retains the replay output. The experiment uses only public modular arithmetic and the Python standard library. The protocol's 90-second cap was met by both commands.
