# Complete integer relation lattice for the p941 trace-18 X011 fiber

The 1,529 signed direct rows and 56 degree-two Hecke rows generate **every integer relation** among the 112 ordered p941 trace-18 X011 points. Their `1,585 × 112` integer matrix has Smith invariants `1` repeated 110 times, then `5` and `180`, so its row lattice has index `5·180=900` in `Z^112`. Every row is a point-group relation. The two frozen fiber points at indices 3 and 4 generate all 900 points of the curve group. The point map is therefore onto, and its kernel and the row lattice both have index 900; they coincide.

This confirmation uses the fixed rows from the p941 rank experiment. `protocol.json` and `pre-run.json` record the input digests, proposed Smith factors, generating pair and resource cap after a read-only Smith diagnostic and before the confirmation run. The result complements the p1009 full-lattice experiment: the p941 curve group is noncyclic, and degree two supplies the rank-gaining Hecke rows.

## Exact evidence

| Check | Result |
| --- | --- |
| Curve | `y²+y=x³−x²−10x−20` over `F_941` |
| Ordered trace-18 fiber | 112 points |
| Rows | 56 degree-two Hecke + 1,529 signed direct |
| Smith nonunit factors | `[5,180]` |
| Row-Hermite basis | `112 × 112`, absolute determinant 900 |
| Generating pair | indices 3, 4: `(32,685)`, `(43,695)` |
| Pair orders and span | 180, 60; combined span 900 |
| Curve group order | 900 |

The checked-Sage producer verifies all 1,585 group identities and computes the Smith factors and row-Hermite basis. The producer result was frozen by digest before the independent audit. `audit.py` counts the curve points with pure-Python finite-field arithmetic, checks the point orders and full pair span, and replays every row with an independent point group law. SymPy and FLINT independently compute the Smith factors from the original row matrix; FLINT computes a Hermite basis of determinant 900. The audit also checks the saved Sage basis digest and triangular diagonal product. `audit.json` reports `PASS`.

The first independent attempt completed its pure-Python and SymPy Smith stages but exceeded the 180-second cap in SymPy's Hermite routine. `audit-sympy-hnf-attempt.json` records that `CENSORED_RESOURCE_CAP` attempt and its traceback. The completed bounded audit uses FLINT for the Hermite stage; the saved failure is retained rather than pooled with its result.

## Written proof

Let `P_0,…,P_111` be the ordered fiber points, `L ⊆ Z^112` the lattice spanned by the saved rows, and `f : Z^112 → E(F_941)` send the `i`th standard basis vector to `P_i`. Independent group-law replay gives `L ⊆ ker f`. The recorded points `P_3` and `P_4` generate all 900 curve points, so `f` is surjective and `[Z^112:ker f]=900`. The Smith invariants, cross-checked by the Hermite determinant, give `[Z^112:L]=5·180=900`. Thus `L=ker f` by the equal-index subgroup theorem.

The result determines the integer relation lattice on this exact fiber and row family. The run records `candidate_id: null` and `target_online_ms: null`, while short Smith and Hermite durations remain finite-census diagnostics.

## Formal checks

The general index-to-kernel implication is proved in the stacked p1009 [`IndexEquality.lean`](../hecke-x011-p1009-relation-lattice-20261119/formal/IndexEquality.lean) module under pinned Lean and mathlib. The local generated `formal/HNFIndex.lean` checks the 461 saved nonzero Hermite entries lie on or above the diagonal and that their diagonal product is 900. Its `#print axioms` output reports no axioms. The concrete curve count, generating-pair span, row containment and matrix normal forms are independently replayed computations; the formal proof map keeps their Lean bridges open.

## Reproduction

From this worktree, with the preceding p941 rank artifacts present:

```sh
/Volumes/SSD990/cryptanalysis/sage --runtime-info > experiments/hecke-x011-p941-relation-lattice-20261119/runtime-info.json
/Volumes/SSD990/cryptanalysis/sage -python experiments/hecke-x011-p941-relation-lattice-20261119/run_sage.py
python3 experiments/hecke-x011-p941-relation-lattice-20261119/audit.py
python3 experiments/hecke-x011-p941-relation-lattice-20261119/generate_hnf_formal.py
cd experiments/hecke-x011-p941-relation-lattice-20261119/formal
lean HNFIndex.lean
```

The checked Sage runtime receipt was saved before the confirmation workload. `formal/lean-toolchain` pins Lean `v4.34.1` for the local core certificate; the general theorem's toolchain and mathlib revision are pinned in its own module directory. `lean4checker --fresh` was unavailable on the host. All raw and censored attempts, digest records, independent audit, and Lean build output are retained here.
