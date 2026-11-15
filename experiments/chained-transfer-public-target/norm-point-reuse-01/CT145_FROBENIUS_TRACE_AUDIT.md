# CT145 — Frobenius/trace qualification of norm-point doubling

Date: 2026-11-15. Parent: cryptanalysis #1533 (CT125); root: crypto #3877. Standing: **[pcc:unverified]**. This is a **conditional mathematical obstruction / source-audit gate**, not a demonstrated error on the original q223 fixture, not a native benchmark, not a speedup.

## Exact proposition

Let (L/K) be a quadratic finite-field extension with Galois automorphism (sigma), let (E/K) be an elliptic curve, and let (f:E_L\to J_L) be a **K-defined group homomorphism** into an abelian variety. Then by equivariance and the group law,

[
\operatorname{Tr}_{L/K}(f(Z))=f(Z)+\sigma f(Z)
=f(Z+\sigma Z).
]

Consequently, replacing the **group trace** by (f([2]Z)) is justified if (Z=\sigma Z), or more generally if (f(\sigma Z-Z)=0). The ordinary elliptic-point identity is

[
\operatorname{Tr}_{L/K}(Z)-[2]Z=\sigma Z-Z.
]

Checking only that ([2]Z\in E(K)) does **not** imply that (Z\in E(K)) or that trace equals doubling: it implies (2(\sigma Z-Z)=0), so a nonzero 2-torsion discrepancy can remain.

**Odd-order safe subcase.** If (Z\in E[r]) for odd (r), then ([2]Z\in E(K)) implies (Z\in E(K)): the defect belongs to both (E[r]) and (E[2]), whose intersection is trivial. This argument requires actual subgroup membership for the evaluated (Z), not just an odd-order source generator. Lifts and correction fibres must be considered.

## Reproducible finite counterexample — separate from the original curve

In (K=\mathbb F_5), (L=K[u]/(u^2-2)), (E:y^2=x^3+1), take (Z=(4+u,3)). Frobenius is (\sigma(u)=-u). Exact group operations give:

- (Z\in E(L)\setminus E(K)), (\sigma Z=(4-u,3)).
- ([2]Z=(0,1)\in E(K)).
- (Z+\sigma Z=(2,2)\in E(K)), **different from** ([2]Z).
- The defect ((Z+\sigma Z)-[2]Z=(4,0)\neq O) is 2-torsion.

These can also be verified by hand: ((4+u)^2=3+3u), ((4+u)^3=3); the doubling slope is (4+4u), giving ([2]Z=(0,1)). The trace secant has slope zero and gives ((2,2)).

`python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct145_frobenius_trace_canary.py` and `python3 -O .../ct145_frobenius_trace_canary.py` enumerate **all 36 points** of (E(\mathbb F_{25})), check point-trace identities and find six nonrational points whose doubles descend but differ from their traces. Development-sandbox checks passed normal and optimized Python. Source file is independently added to this PR; no original Rust, fixtures or PCC ledger are changed.

## Applicability boundary to CT125

CT125's generated `norm_from_target_point(to,z)` calls `target.admit(&z)`, doubles (z) in the quadratic model, descends the **double**, and checks the descended point lies on the source curve. From these source checks alone, a general (\sigma z=z) condition is **not established**. The original `check_final` separately compares the actual final Jacobian norm, which may reject a bad reuse result; do not claim a current incorrect accepted log.

The actual map `target_phi` and `norm` may involve cover/deck correspondences rather than the simple field trace above. Before applying this proposition as a bug diagnosis, establish the exact identity defining their norm and whether it is Frobenius-equivariant with the stated (f). This report identifies a missing **explicit proof obligation**, not a proven defect in the specialized geometry.

**Next discriminating source/runtime check:** for every selected and exceptional lifted target point in the frozen 695/701-record corpus, record (z,\sigma z,[2]z,z+\sigma z) and the independently computed Jacobian norm. If the geometry guarantees rational (z), cite/check that invariant. Otherwise prove (f(\sigma z-z)=0) or retain the actual norm computation instead of the assumed doubling shortcut. Keep entire order/negative records. Only then price the approved native (C_{169}, C_{13a}, C_{13b},D) and compare full cold single-target solves.

## Prior sources and scope

Read: crypto [#3877](https://github.com/isogeny-labs/crypto/pull/3877), [#4215](https://github.com/isogeny-labs/crypto/pull/4215); cryptanalysis [#1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533), [#1562](https://github.com/isogeny-labs/cryptanalysis/pull/1562), [#1581](https://github.com/isogeny-labs/cryptanalysis/pull/1581), and CT125's `build_norm_reuse.py` and `compare_norm_reuse.py`. For Frobenius and rational fixed points see [Sage finite-field elliptic-curve reference](https://doc-gitlab.sagemath.org/html/en/reference/arithmetic_curves/sage/schemes/elliptic_curves/ell_finite_field.html) and [FLINT Frobenius specification](https://flintlib.org/doc/fq/frobenius.html). These are context for standard field/Galois operations; the group identity above is elementary. Live research-KB MCP and local wrapper were absent; searched repository-index terms and current PRs instead. No novelty or absence claim.

**Unmet gates:** actual native 695/701 parity, complete original-prime source/candidate comparison with matched strongest rho/BSGS/IC and all setup/transfer/LA/memory, independently signed PCC. No paid compute, protected merge, scientific promotion or source rewrite.
