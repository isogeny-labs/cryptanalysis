# Complete integer relation lattice for the p1009 X011 trace-20 fiber

The 568 signed direct rows and 28 degree-three Hecke rows generate **the full integer relation lattice** among the 84 ordered X011 trace-20 points over `F_1009`. Their `596 × 84` matrix has Smith invariants `1` repeated 83 times and `1020` once, so its row lattice has index 1020 in `Z^84`. Every row is a point-group relation. The first fiber point, `(2,155)`, has order 1020 and generates the curve group, also of order 1020. Thus the map from `Z^84` to the curve group is onto, its kernel has index 1020, and containment plus equal index makes the row lattice exactly that kernel.

This is a confirmation on fixed rows from the degree-three experiment. Its question and artifact hashes were frozen in `protocol.json` and `pre-run.json` after the initial Smith diagnostic and before the confirmation run. It strengthens the earlier rational and mod-17 rank result by determining the **integer** quotient rather than only ranks over fields.

## Evidence

| Check | Exact result |
| --- | --- |
| Curve | `y²+y=x³−x²−10x−20` over `F_1009` |
| Ordered fiber points | 84 |
| Rows | 28 degree-three Hecke + 568 signed direct |
| Smith nonunit factors | `[1020]` |
| Smith zero count for the rectangular matrix | 512 |
| Row-Hermite basis | `84 × 84`, absolute determinant 1020 |
| First fiber point | `(2,155)`, order 1020 |
| Curve group order | 1020 |

`run_sage.py` checks the frozen input digests and all 596 row identities on the curve, computes the integer Smith factors and a row-Hermite basis, and saves the basis and result. `result.json` was hash-frozen before audit. The independent `audit.py` uses a separate pure-Python group law to replay every row, counts curve points from finite-field quadratic discriminants, checks generator order with the prime divisors of 1020, and runs SymPy's Smith and column-Hermite algorithms on the original sparse rows. `audit.json` reports `PASS` and binds the producer result by SHA-256. The saved row-Hermite basis is also checked by digest and determinant.

## Written proof

Let `P_0,…,P_83` be the ordered fiber points, `L ⊆ Z^84` the lattice spanned by the 596 rows, and `f : Z^84 → E(F_1009)` the homomorphism sending the `i`th standard basis vector to `P_i`. The independently replayed group identities give `L ⊆ ker f`. Since `P_0=(2,155)` has order 1020 and the curve has exactly 1020 points, `f` is surjective and `[Z^84 : ker f]=1020`. The Smith invariants, independently cross-checked by a Hermite determinant, give `[Z^84 : L]=1020`. For subgroups `L ⊆ ker f` of finite index, equal indices force equality. Hence `L=ker f`.

The proof applies to this exact ordered fiber and the frozen 596-row family. It identifies an integer-lattice completion property; `candidate_id` and `target_online_ms` remain null in the result because no single-target IC timing workload was defined. The short local Smith and Hermite computation times in `result.json` are diagnostics.

## Lean proof map

`formal/IndexEquality.lean` proves the general group-theoretic implication: a subgroup of genuine relations equals the kernel when the point map is surjective and both indices equal the group order. The theorem is kernel-checked; `#print axioms` reports only Lean's standard `propext`, `Classical.choice`, and `Quot.sound`. `formal/HNFIndex.lean` checks the saved Hermite basis has 281 nonzero entries above or on its diagonal and that the diagonal product is 1020; its declarations report no axioms. The concrete row generation, matrix normal forms, curve count, and generator order are bound to the computational artifacts and independently replayed. The Lean formalization of those concrete bridges remains open; see `formal/PROOF_MAP.md`.

## Reproduction

From this worktree, with the preceding degree-two and degree-three artifacts present:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p1009-relation-lattice-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p1009-relation-lattice-20261119/run_sage.py
python3 experiments/hecke-x011-p1009-relation-lattice-20261119/audit.py
python3 experiments/hecke-x011-p1009-relation-lattice-20261119/generate_hnf_formal.py
cd experiments/hecke-x011-p1009-relation-lattice-20261119/formal
lean HNFIndex.lean
cd /Volumes/SSD990/cryptanalysis/experiments/xedni-lattice-obstruction-20261028/formal
lake env lean /Volumes/SSD990/x011-fiber-multiplicity-worktree-20261119/experiments/hecke-x011-p1009-relation-lattice-20261119/formal/IndexEquality.lean
```

The measured Sage launcher runtime receipt was saved before the confirmation workload. The Lean toolchain and mathlib revision are pinned in `formal/DEPENDENCIES.json`. `lean4checker --fresh` was unavailable on the host. The protocol, raw basis, producer and independent audit, formal modules, and build outputs are retained here.
