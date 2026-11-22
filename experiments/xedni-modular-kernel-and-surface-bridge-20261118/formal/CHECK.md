# Formal verification receipt: multi-prime modular relation kernels and section-specialization bounds

Date: 2026-11-18

Pinned Lean `leanprover/lean4:v4.35.0-rc4` and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9` built
`ModularKernelAndSurfaceBridge.lean` with zero errors and audited all 11 named
theorems (15 module constants) with zero failing and zero compiler-trust
foundations. [pcc:unverified]

Every theorem uses only standard Lean foundations (`propext`,
`Classical.choice`, and `Quot.sound` as applicable), with no `sorry`, `admit`,
`sorryAx`, `native_decide`, or project-defined assumptions. [pcc:unverified]

## Proof map

| Lean theorem (`XedniScalingBridge.*`) | Mathematical statement | Foundations |
|---|---|---|
| `evalLinearCombination_map` | Pushing `∑_{i ∈ s} n_i • P_i` through any `φ : A →+ B` evaluates `∑_{i ∈ s} n_i • φ(P_i)` | `propext, Classical.choice, Quot.sound` |
| `globalRelation_le_modularRelation` | Every exact global relation lies in the modular relation subgroup `ker(ℤ^s → B)` | `propext, Classical.choice, Quot.sound` |
| `globalRelation_le_iInf_modularRelation` | Zero-false-negative soundness of multi-prime kernel intersection: `globalRelationSubgroup ≤ ⨅_j modularRelationSubgroup_j` across any family of good-reduction primes | `propext, Classical.choice, Quot.sound` |
| `incremental_kernel_generator_zero` | First-collision relation `m • Q_k = ∑_{i<k} c_i • Q_i` yields exact kernel vector `(-c_0, …, -c_{k-1}, m)` | `propext, Classical.choice, Quot.sound` |
| `incremental_kernel_step_complete` | Completeness on arbitrary (cyclic or non-cyclic) `C(𝔽_q)`: minimal `m > 0` divides `a_k` in every relation `(∑_{i<k} a_i • Q_i) + a_k • Q_k = 0` and reduces `a` to the prefix subgroup | `propext, Classical.choice, Quot.sound` |
| `torsion_coprime_specialization_kills_torsion` | Any specialization/reduction `sp : E_global →+ G` into a prime-exponent-`q` group maps `T`-torsion (`gcd(T, q) = 1`) to `0` | `propext, Quot.sound` |
| `torsion_relation_specializes_zero` | Machine-checks `L4-lifting` Lemma 2 for both number-field lifts and elliptic-surface sections `𝓔(𝔽_p(t))`: torsion-modulo relations specialize without a torsion factor `T` | `propext, Classical.choice, Quot.sound` |
| `maskDot_update_add` | Affine translation identity `maskDot x m (update u j (u_j + δ)) v = maskDot x m u v + m_j * δ` over `ZMod q` | `propext, Classical.choice, Quot.sound` |
| `useful_mask_relation_recovers_log` | Useful scalar relation (`∑ m_i v_i ≠ 0`) uniquely recovers `x = -(∑ m_i u_i) * (∑ m_i v_i)⁻¹` in `ZMod q` | `propext, Classical.choice, Quot.sound` |
| `fresh_mask_hits_card` | Machine-checks `L4-lifting` Lemma 1: for any nonzero `m : Fin k → ZMod q`, exact mask-hit cardinality is `q^(2k - 1)` out of `q^(2k)` (exact probability `1/q`) | `propext, Classical.choice, Quot.sound` |
| `fresh_mask_candidate_set_union_bound` | Machine-checks the union core of `L4-lifting` Theorem X and extends it to function-field bounded-Shioda-height section boxes: hit count is at most `|M| * q^(2k - 1)` | `propext, Classical.choice, Quot.sound` |

## Scope boundary

- Certifies that our Rust multi-prime abelian-subgroup kernel + HNF + LLL
  relation extractor (`suite/src/cryptanalysis/xedni_solver.rs`) loses zero
  global Mordell--Weil relations regardless of relation norm or non-cyclic
  `C(𝔽_q)` group structure. [pcc:unverified]
- Establishes unconditionally that elliptic-surface dimension surplus over
  `𝔽_p(t)` (`LEAD-ICP-xedni-function-field-sections`,
  `LEAD-TRF-function-field-xedni-lift`) still obeys the `|M| / q` fresh-mask
  ceiling unless either Shioda rank grows as `Ω(√(log q))` (`χ = Ω(√(log q))`)
  or relations are shared across trials via a common factor base rather than
  fresh per-trial masks. [pcc:unverified]

## Reproduce

```sh
cd experiments/xedni-modular-kernel-and-surface-bridge-20261118/formal
lake exe cache get
lake build ModularKernelAndSurfaceBridge
```
