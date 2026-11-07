# Frobenius excludes rational j=1728 3-paths for p≡7 (mod 24)

For every prime `p>3` with `p≡7 (mod 24)`, the curve `E/F_p: y²=x³+x` has **no Frobenius-stable cyclic subgroup of order 3 or 27**. Its trace is zero, and Frobenius on `E[3]` satisfies `π²+1=0`; the polynomial `T²+1` has no root over `F₃`, so it has no invariant line. This gives an exact structural reason to prune this congruence class from rational cyclic 3/27 source-path holdouts.

The frozen source-free screen sought a prime above 1439 and below 5000 with at least four valid `j=1728` C/E/B triples on two rational C sheets. It recorded **58 eligible primes and zero rational `j=1728` C points at every one**, ending with `BOUNDED_NO_J1728_TWO_SHEET_PRIME`. The complete 3/27-path census independently found zero rational paths at all 58. At the three `p≡23 (mod 24)` controls—1319, 1367, and 1439—Frobenius split over `F₃` and the checked census found two rational 3-paths and two rational 27-paths per prime.

| Evidence boundary | `p≡7 (mod 24)` cases | `p≡23 (mod 24)` controls |
| --- | ---: | ---: |
| Frozen primes | 58, from 1447 through 4999 | 1319, 1367, 1439 |
| Trace on `y²=x³+x` | 0 in all 58 | 0 in all three |
| Frobenius polynomial on `E[3]` | `T²+1`, irreducible in `F₃[T]` | `T²−1`, split in `F₃[T]` |
| Rational cyclic 3/27 paths | 0 / 0 in all 58 | 2 / 2 per control |
| Roots of exact degree-18 C-source eliminant | 0 in all 58 | 2 x-roots per control |

## Proof and its formalization boundary

For `p≡7 (mod 24)`, `p≡3 (mod 4)`, so `−1` is a nonsquare. Let `f(x)=x³+x` and let `χ` be the quadratic character. Since `f(−x)=−f(x)`, the terms `χ(f(x))` and `χ(f(−x))` cancel; the `x=0` term is zero. Thus the character sum and the Frobenius trace are zero. The standard Frobenius characteristic equation, restricted to `E[3]`, is `π²−tπ+p=0`. Here `t=0` and `p≡1 (mod 3)`, giving `π²+1=0` on the two-dimensional `F₃`-space `E[3]`. No scalar in `F₃` squares to `−1`, so an invariant one-dimensional subspace cannot exist. A Frobenius-stable cyclic subgroup of order 27 would have a unique subgroup of order 3 that is also stable, yielding the same contradiction. The [Frobenius characteristic equation](https://math.mit.edu/classes/18.783/2022/LectureNotes8.pdf) and [Galois-invariant kernel criterion](https://math.mit.edu/classes/18.783/2025/LectureNotes5.pdf) provide the standard elliptic-curve bridges used here.

The pinned Lean module [`formal/FrobeniusObstruction.lean`](formal/FrobeniusObstruction.lean) proves the structural `F₃` implication: a linear operator squaring to negative identity has no nonzero eigenvector or stable cyclic line. Its build and `#print axioms` receipt is [`formal/build-output.txt`](formal/build-output.txt), with toolchain and dependency revisions in [`formal/DEPENDENCIES.json`](formal/DEPENDENCIES.json). The character-sum trace proof, the identification of the Frobenius action on the actual `E[3]`, and the cyclic-kernel bridge are written above; their Lean formalization remains partial. The coarse C-coordinate fiber is a separate boundary: the 58-prime zero-root statement below is an exact bounded computation, while a uniform coarse-moduli/normalization implication remains to be proved.

## Exact eliminant and independent audits

[`elimination_protocol.json`](elimination_protocol.json) bound the exact source-j coordinate map before the checked-Sage [elimination](eliminate_sage.py). On `C:y²+y=x³−7`, eliminating y from the curve equation and `numerator+1728·denominator=0` gives a degree-36 x-resultant equal to a nonzero rational scalar times the **square of one irreducible degree-18 polynomial**. An independent [SymPy replay](audit_elimination.py) reconstructs the resultant and factorization from the source terms. The [modular root audit](audit_eliminant.py) finds zero roots of that factor at all 58 frozen `p≡7` primes and exactly two x-roots at each control, matching the observed C coordinates.

[`obstruction_protocol.json`](obstruction_protocol.json) froze the 58 sieve primes and three controls before the checked-Sage [path census](path_census_sage.py). Its [result](path_census.json) retains every prime, trace, characteristic polynomial modulo 3, and rational 3/27-path count. An independent [character-sum audit](audit_frobenius.py) recomputes all 61 traces and checks the mod-3 eigenvalue test. The sieve, eliminant, Frobenius, and independent audit statuses are preserved as separate artifacts. All local Sage jobs used the repository's checked launcher; [`sage-runtime-info.txt`](sage-runtime-info.txt) records its runtime.

The next prospective special-j product test should choose a source-free prime in a congruence class with rational 3-lines, such as `p≡1 (mod 4)`, and freeze its prime rule and product prediction before the full inverse. The `p≡7 (mod 24)` branch can be pruned at the rational 3-path gate. This is an IC stage diagnostic with `candidate_id: null`.

Replay from the repository root:

```sh
python3 experiments/hecke-432-j1728-cubic-twist-holdout-20261026/sieve.py
./sage --runtime-info > experiments/hecke-432-j1728-cubic-twist-holdout-20261026/sage-runtime-info.txt
./sage -python experiments/hecke-432-j1728-cubic-twist-holdout-20261026/eliminate_sage.py
./sage -python experiments/hecke-432-j1728-cubic-twist-holdout-20261026/path_census_sage.py
python3 experiments/hecke-432-j1728-cubic-twist-holdout-20261026/audit_elimination.py
python3 experiments/hecke-432-j1728-cubic-twist-holdout-20261026/audit_eliminant.py
python3 experiments/hecke-432-j1728-cubic-twist-holdout-20261026/audit_frobenius.py
cd experiments/hecke-432-formal-ci-20261025 && lake env lean ../hecke-432-j1728-cubic-twist-holdout-20261026/formal/FrobeniusObstruction.lean
cd ../hecke-432-j1728-cubic-twist-holdout-20261026 && shasum -a 256 -c SEAL.sha256
```
