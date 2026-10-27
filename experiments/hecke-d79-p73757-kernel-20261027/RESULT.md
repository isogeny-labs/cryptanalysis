# The p73757 F199 relation kernel is the class-point log line

Every verified homogeneous relation among the 40 p73757 D79 class points annihilates their projected discrete-log vector modulo 199. The support-four matrix has rank 34 and a six-dimensional right kernel. Adding either direct or degree-13 Hecke support-five rows raises the rank to 39, and the remaining one-dimensional kernel is **exactly** the line spanned by that log vector. The rank-39 ceiling therefore follows from the group relation itself: an additional valid homogeneous relation on the same columns cannot remove this line.

## Structural result

Let `P₀,…,P₃₉` be the class points and let `φ:E(F₇₃₇₅₇)→F₁₉₉` be the homomorphism obtained by multiplying by 370 and taking the discrete log in the order-199 subgroup relative to `T=370P₀`. For every integer relation row `a=(a_i)` satisfying `Σ a_i P_i = O`, additivity gives `Σ a_i φ(P_i)=φ(O)=0` in `F₁₉₉`. Since `φ(P₀)=1`, the vector `v=(φ(P_i))` is nonzero. Thus any matrix made entirely of these homogeneous relation rows has rank at most 39 over `F₁₉₉`.

The checked Sage producer and independent pure-Python group-law audit enumerate all 199 multiples of `T`, recover each `φ(P_i)`, verify all 40 projected point identities, and check every relation row both as an elliptic-curve group identity and as a zero dot product with `v`. All 40 coordinates of `v` are nonzero; its canonical compact-JSON SHA-256 is `ebe81a3608feaf9dde4c79725dbccd5fe0212fab2bef49f3bcaa8a079f3432bb`.

| Frozen row family | Rows | Rank over F199 | Right-kernel dimension | Kernel relation |
| --- | ---: | ---: | ---: | --- |
| Support-four | 419 | 34 | 6 | Contains `v` |
| Support-four plus direct support-five | 573 | 39 | 1 | Exactly `span(v)` |
| Support-four plus Hecke support-five | 552 | 39 | 1 | Exactly `span(v)` |
| Support-four plus both support-five arms | 706 | 39 | 1 | Exactly `span(v)` |

For each of the three rank-39 families, augmenting the relation matrix by a known-coordinate equation `x_i = φ(P_i)` gives rank 40 for **every** `i=0,…,39`; `anchor-audit.json` checks all 120 augmented ranks. With the declared anchor `x₀=1` (known by the choice `T=370P₀`), modular elimination on the 706 relation rows plus that anchor recovered all 40 coordinates, matching the independently enumerated vector and replaying every equation. This is a finite class-log normalization component. For larger subgroup orders, obtaining such an anchor remains a separate computation and must be charged in any complete pipeline.

The p73757 field, curve, 40 class points, support-four rows, both support-five arms and parent audits are pinned by SHA-256 in `inputs.json`. The checked repository Sage launcher and saved runtime receipt produced the modular kernels. The pure-Python auditor independently implements the curve group law and modular elimination. The producer's kernel computation took 0.152 seconds after inputs were loaded; the anchored linear solve took 0.010 seconds. These are local stage diagnostics; `candidate_id` and `target_online_ms` remain null.

## Formalization and next step

`Structural.lean` proves the conditional homomorphism-annihilation theorem with no axioms. `FiniteP73757.lean` checks the exact 706-row modular annihilation, a nonzero log vector, membership of 39 selected rows in the matrix, and an invertible 39-by-39 minor modulo 199. Both modules build under the pinned Lean toolchain; the finite certificates use only standard `propext` where reported. `PROOF_MAP.md` identifies the remaining formal connection from Sage elliptic-curve points and projected logs to the Lean lists.

The next experiment should treat the rank-39 line as the expected normalization freedom. It should specify how a known base log or target-dependent equation enters the system, then measure complete subgroup-log and target handling on a frozen single-target workload. Searching for a further homogeneous row on these same 40 columns cannot raise the F199 rank.
