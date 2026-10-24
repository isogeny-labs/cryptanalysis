# The local Hecke commutator removes 72 rows on the two-lift holdout

**Contribution.** The frozen $D=-1295$, $p=11719$ two-lift holdout has **72 exact eight-term certificates** expressing every conductor-2 degree-3 row through rows from conductors 1 and 3. Its conductor-2 block adds **zero** rank to the other 288 rows, despite the two rational $X_0(11)$ lifts above each conductor-2 CM $j$-invariant. The complete relation matrix has rational rank 288 across 360 rows; its nonfloor projection has rank 272. The local redundancy therefore survives the change from one lift in the separately sealed $D=-1199$ experiment to two lifts here.

| Quantity | $D=-1199$ one-lift case | $D=-1295$ two-lift holdout |
| --- | ---: | ---: |
| Rational class points | 228 | 432 |
| Eligible degree-2/3 rows | 190 | 360 |
| Conductor-2 degree-3 rows with eight-term certificates | 38 | **72** |
| Increment from these rows after other rows | 0 | **0** |
| Full rational row rank | 152 | 288 |
| Nonfloor projected rank | 150 | 272 |

[protocol.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-commutator-two-sheet-20261023/protocol.json) fixed the unique-descendant, 72-certificate, eight-term, and zero-increment predictions before this replay. It binds the prior [sealed holdout](/Volumes/SSD990/cryptanalysis/experiments/hecke-two-sheet-small-order-20261023/SEAL.json), the replay source, and the applicable Lean theorem by SHA-256. The predecessor's checked-Sage audit reconstructed all 432 points and 360 relations, including conductor labels, modular-polynomial root counts, elliptic-curve group sums, and exact ranks. This replay reads those immutable rows and point labels; it starts no new Sage process.

For every conductor-1 point $P$, [replay.py](/Volumes/SSD990/cryptanalysis/experiments/hecke-commutator-two-sheet-20261023/replay.py) reconstructs the $T_2$ and $T_3$ neighbor multisets directly from the saved relation rows. It finds a unique conductor-2 descendant $Q$ in $T_2P$ and applies the eight-term identity proved by `HeckeCommutator.isolate_unique_two_descendant` in the [pinned Lean module](/Volumes/SSD990/cryptanalysis/experiments/hecke-ramified11-fullrank-20261023/formal/HeckeCommutator.lean). The formula uses $R_2=T_2+2I$ and $R_3=T_3+I$, so its premise is the commutation of $T_2,T_3$. [Snowden's lecture](https://websites.umich.edu/~asnowden/teaching/2013/679/L16.html) states the general Hecke commutation rule. The 72 computed descendants are distinct and exhaust the conductor-2 points; every formula reconstructs its target row coefficient for coefficient. [replay.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-commutator-two-sheet-20261023/replay.json) retains each source, target, and eight coefficients.

The remaining 288 rows have rank 288 modulo both 101 and 1,000,000,007, giving a rational lower bound of 288. The exact certificates put the other 72 rows in their span, giving an upper bound of 288. Their full-rank increment is therefore exactly zero. The predecessor's exact Sage audit gives nonfloor rank 272; the replay also obtains rank 272 modulo both primes after omitting the floor columns and the redundant rows. The resulting 16 floor-only directions are a whole-matrix rank difference, not an estimate of new independent conductor-2 relations.

The model coefficients are $[0,-1,1,-10,-20]$. [verify_curve.py](/Volumes/SSD990/cryptanalysis/experiments/hecke-commutator-two-sheet-20261023/verify_curve.py) parses them from the frozen source without executing it and independently counts five points over each of $\mathbf F_2$ and $\mathbf F_3$, yielding $a_2=-2$ and $a_3=-1$. Its [receipt](/Volumes/SSD990/cryptanalysis/experiments/hecke-commutator-two-sheet-20261023/curve_check.json) binds that arithmetic check to the replay.

The general operator and local-isolation implications are Lean-checked in the preceding formalization. For this holdout, the hypotheses identifying the concrete $X_0(11)$ rows with the abstract operators are checked by the saved finite-field audit and this exact replay; their modular-curve Lean bridge remains open. This is a relation-stage result with `candidate_id: null` and `timing_claim: null`. A further discriminant with a different degree-2 fiber geometry would test the unique-descendant hypothesis itself.
