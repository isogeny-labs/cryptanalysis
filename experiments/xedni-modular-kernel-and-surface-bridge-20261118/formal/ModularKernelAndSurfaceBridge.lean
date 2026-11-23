import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Field.ZMod
import Mathlib.Algebra.Group.Subgroup.Lattice
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic.Ring

namespace XedniScalingBridge

/-!
# Multi-Prime Modular Relation Kernels and Section-Specialization Bounds for Xedni

1. **Multi-prime good-reduction relation-lattice soundness and incremental subgroup completeness**:
   certifies that intersecting auxiliary finite-group relation kernels `ker(ℤ^r → C(𝔽_{q_j}))`
   retains every exact global Mordell--Weil relation of arbitrary coefficient norm, and that the
   first-collision incremental step `m_k • Q_k = ∑_{i < k} c_i • Q_i` yields an exact, complete
   generator of the `k`-th relation coordinate even when `C(𝔽_{q_j})` is non-cyclic.
2. **Torsion-coprime specialization and fresh-mask union barrier**:
   formalizes `L4-lifting` Lemmas 1--2 and extends them unconditionally to elliptic-surface
   section specialization `sp : 𝓔(𝔽_p(t)) →+ E_0(𝔽_p)` across arbitrary Euler characteristic `χ`
   and dimension surplus.
-/

/-- Evaluate an integer combination `∑_{i ∈ s} n_i • P_i` in any additive commutative group. -/
def evalLinearCombination {ι A : Type*} [AddCommGroup A]
    (s : Finset ι) (P : ι → A) : (ι → ℤ) →+ A where
  toFun n := ∑ i ∈ s, n i • P i
  map_zero' := by simp
  map_add' a b := by
    simp only [Pi.add_apply, add_zsmul, Finset.sum_add_distrib]

/-- Exact subgroup of global integer relations `∑_{i ∈ s} n_i • P_i = 0`. -/
def globalRelationSubgroup {ι A : Type*} [AddCommGroup A]
    (s : Finset ι) (P : ι → A) : AddSubgroup (ι → ℤ) :=
  (evalLinearCombination s P).ker

/-- Subgroup of integer relations vanishing after a homomorphism `φ : A →+ B` (such as good reduction). -/
def modularRelationSubgroup {ι A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (s : Finset ι) (φ : A →+ B) (P : ι → A) : AddSubgroup (ι → ℤ) :=
  (evalLinearCombination s (φ ∘ P)).ker

/-- Composing `evalLinearCombination` with any additive homomorphism `φ` pushes evaluation to `φ ∘ P`. -/
theorem evalLinearCombination_map {ι A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (s : Finset ι) (φ : A →+ B) (P : ι → A) (n : ι → ℤ) :
    φ (evalLinearCombination s P n) = evalLinearCombination s (φ ∘ P) n := by
  simp only [evalLinearCombination, AddMonoidHom.coe_mk, ZeroHom.coe_mk,
    Function.comp_apply, map_sum, map_zsmul]

/-- Every exact global relation lies in the modular relation lattice of any good-reduction map `φ`. -/
theorem globalRelation_le_modularRelation {ι A B : Type*} [AddCommGroup A] [AddCommGroup B]
    (s : Finset ι) (φ : A →+ B) (P : ι → A) :
    globalRelationSubgroup s P ≤ modularRelationSubgroup s φ P := by
  intro n hn
  rw [globalRelationSubgroup, AddMonoidHom.mem_ker] at hn
  rw [modularRelationSubgroup, AddMonoidHom.mem_ker, ← evalLinearCombination_map, hn, map_zero]

/-- Zero-false-negative soundness of multi-prime kernel intersection:
the global relation lattice is contained in the intersection of `modularRelationSubgroup`
across any family of good-reduction primes/groups `(B j)_{j ∈ J}`. -/
theorem globalRelation_le_iInf_modularRelation {ι J A : Type*}
    {B : J → Type*} [AddCommGroup A] [∀ j, AddCommGroup (B j)]
    (s : Finset ι) (φ : ∀ j, A →+ B j) (P : ι → A) :
    globalRelationSubgroup s P ≤ ⨅ j, modularRelationSubgroup s (φ j) P :=
  le_iInf fun j => globalRelation_le_modularRelation s (φ j) P

/-- Incremental subgroup-kernel generator soundness: if `m • Qk = ∑_i c_i • Q_i`,
then `(-c_0, ..., -c_{k-1}, m)` is an exact integer relation on `(Q_0, ..., Q_{k-1}, Qk)`. -/
theorem incremental_kernel_generator_zero {k : ℕ} {B : Type*} [AddCommGroup B]
    (Q : Fin k → B) (Qk : B) (c : Fin k → ℤ) (m : ℤ)
    (hm_rel : m • Qk = ∑ i, c i • Q i) :
    (∑ i, (-c i) • Q i) + m • Qk = 0 := by
  rw [hm_rel]
  simp only [neg_zsmul, Finset.sum_neg_distrib, neg_add_cancel]

/-- Incremental subgroup-kernel completeness (works for cyclic and non-cyclic `C(𝔽_q)` alike):
if `m > 0` is the least positive multiple of `Qk` lying in the span of `Q_0, ..., Q_{k-1}`,
then every integer relation `(∑_i a_i • Q_i) + ak • Qk = 0` satisfies `m ∣ ak` and reduces
modulo the generator `(-c, m)` to a pure prefix relation on `Q_0, ..., Q_{k-1}`. -/
theorem incremental_kernel_step_complete {k : ℕ} {B : Type*} [AddCommGroup B]
    (Q : Fin k → B) (Qk : B) (c : Fin k → ℤ) (m : ℤ)
    (hm_pos : 0 < m)
    (hm_rel : m • Qk = ∑ i, c i • Q i)
    (hm_min : ∀ r : ℤ, 0 < r → r < m → ¬ ∃ d : Fin k → ℤ, r • Qk = ∑ i, d i • Q i)
    (a : Fin k → ℤ) (ak : ℤ)
    (ha_rel : (∑ i, a i • Q i) + ak • Qk = 0) :
    m ∣ ak ∧ ∑ i, (a i + (ak / m) * c i) • Q i = 0 := by
  have hm_ne : m ≠ 0 := ne_of_gt hm_pos
  set q := ak / m
  set r := ak % m
  have hdiv : m * q + r = ak := Int.mul_ediv_add_emod ak m
  have hr_nonneg : 0 ≤ r := Int.emod_nonneg ak hm_ne
  have hr_lt : r < m := Int.emod_lt_of_pos ak hm_pos
  have hq_sum : (q * m) • Qk = ∑ i, (q * c i) • Q i := by
    have hmap := map_zsmul (evalLinearCombination Finset.univ Q) q c
    simp only [evalLinearCombination, AddMonoidHom.coe_mk, ZeroHom.coe_mk, Pi.smul_apply,
      zsmul_eq_mul, Int.cast_id] at hmap
    rw [mul_zsmul, hm_rel, ← hmap]
  have hr_eq : r • Qk = ∑ i, (-(a i + q * c i)) • Q i := by
    have hak_split : ak • Qk = (q * m) • Qk + r • Qk := by
      rw [← add_zsmul, mul_comm q m, hdiv]
    have hcomb : (∑ i, (a i + q * c i) • Q i) + r • Qk = 0 := by
      calc
        (∑ i, (a i + q * c i) • Q i) + r • Qk =
            (∑ i, a i • Q i) + ((∑ i, (q * c i) • Q i) + r • Qk) := by
          simp only [add_zsmul, Finset.sum_add_distrib, add_assoc]
        _ = (∑ i, a i • Q i) + ak • Qk := by
          rw [← hq_sum, ← hak_split]
        _ = 0 := ha_rel
    have hneg := eq_neg_of_add_eq_zero_right hcomb
    rw [hneg, ← Finset.sum_neg_distrib]
    apply Finset.sum_congr rfl
    intro i _
    rw [neg_zsmul]
  have hr_zero : r = 0 := by
    by_contra hr_nz
    have hr_pos : 0 < r := lt_of_le_of_ne hr_nonneg (Ne.symm hr_nz)
    exact hm_min r hr_pos hr_lt ⟨fun i => -(a i + q * c i), hr_eq⟩
  have hdvd : m ∣ ak := Int.dvd_of_emod_eq_zero hr_zero
  refine ⟨hdvd, ?_⟩
  have hak_qm : ak = q * m := by
    rw [← hdiv, hr_zero, add_zero, mul_comm]
  have hsum_eq :
      ∑ i, (a i + q * c i) • Q i = (∑ i, a i • Q i) + ak • Qk := by
    simp only [add_zsmul, Finset.sum_add_distrib, ← hq_sum, ← hak_qm]
  rw [hsum_eq, ha_rel]

/-- Torsion-coprime specialization kills global torsion (covering both number-field reduction
`E'(K)_tors → E(𝔽_p)` and elliptic-surface specialization `𝓔(𝔽_p(t))_tors → E_0(𝔽_p)`):
if `sp : E_global →+ G` targets a group `G` of exponent `q` and `(T : ℤ) • t = 0` with
`Nat.Coprime T q`, then `sp t = 0`. -/
theorem torsion_coprime_specialization_kills_torsion {E_global G : Type*}
    [AddCommGroup E_global] [AddCommGroup G]
    (sp : E_global →+ G) {T q : ℕ} (hcop : Nat.Coprime T q)
    (hq_exp : ∀ g : G, (q : ℤ) • g = 0)
    {t : E_global} (ht : (T : ℤ) • t = 0) :
    sp t = 0 := by
  have hbez : (1 : ℤ) = (T : ℤ) * Nat.gcdA T q + (q : ℤ) * Nat.gcdB T q := by
    have h := Nat.gcd_eq_gcd_ab T q
    rw [hcop.gcd_eq_one, Nat.cast_one] at h
    exact h
  have hT_sp : (T : ℤ) • sp t = 0 := by
    rw [← map_zsmul, ht, map_zero]
  calc
    sp t = (1 : ℤ) • sp t := (one_zsmul _).symm
    _ = ((T : ℤ) * Nat.gcdA T q + (q : ℤ) * Nat.gcdB T q) • sp t := by rw [← hbez]
    _ = Nat.gcdA T q • ((T : ℤ) • sp t) + Nat.gcdB T q • ((q : ℤ) • sp t) := by
      rw [add_zsmul, mul_comm (T : ℤ), mul_zsmul, mul_comm (q : ℤ), mul_zsmul]
    _ = 0 := by rw [hT_sp, hq_exp (sp t), smul_zero, smul_zero, add_zero]

/-- `L4-lifting` Lemma 2 & elliptic-surface section corollary (no torsion factor `T` in the count):
any torsion-modulo global/section relation `∑_{i ∈ s} m_i • sec_i = t` with `(T : ℤ) • t = 0`
and `Nat.Coprime T q` specializes to the exact source relation `∑_{i ∈ s} m_i • sp(sec_i) = 0`. -/
theorem torsion_relation_specializes_zero {ι E_global G : Type*}
    [AddCommGroup E_global] [AddCommGroup G]
    (s : Finset ι) (sp : E_global →+ G) {T q : ℕ} (hcop : Nat.Coprime T q)
    (hq_exp : ∀ g : G, (q : ℤ) • g = 0)
    (m : ι → ℤ) (sec : ι → E_global) {t : E_global}
    (ht : (T : ℤ) • t = 0)
    (hrel : ∑ i ∈ s, m i • sec i = t) :
    ∑ i ∈ s, m i • sp (sec i) = 0 := by
  have hmap : sp (∑ i ∈ s, m i • sec i) = sp t := congr_arg sp hrel
  rw [map_sum] at hmap
  simp only [map_zsmul] at hmap
  rw [hmap, torsion_coprime_specialization_kills_torsion sp hcop hq_exp ht]

/-- Scalar mask combination `∑_i m_i * (u_i + x * v_i)` induced in `ZMod q` by fresh masks
`R_i = u_i P + v_i Q` (`Q = x P`). -/
def maskDot {k q : ℕ} (x : ZMod q) (m u v : Fin k → ZMod q) : ZMod q :=
  ∑ i, m i * (u i + x * v i)

/-- Updating mask coordinate `u_{j}` by `δ` shifts `maskDot` by `m_j * δ`. -/
theorem maskDot_update_add {k q : ℕ} [DecidableEq (Fin k)]
    (x : ZMod q) (m u v : Fin k → ZMod q) (j : Fin k) (δ : ZMod q) :
    maskDot x m (Function.update u j (u j + δ)) v = maskDot x m u v + m j * δ := by
  unfold maskDot
  have hsplit := (Finset.add_sum_erase Finset.univ (fun i => m i * (Function.update u j (u j + δ) i + x * v i)) (Finset.mem_univ j)).symm
  have hsplit0 := (Finset.add_sum_erase Finset.univ (fun i => m i * (u i + x * v i)) (Finset.mem_univ j)).symm
  rw [hsplit, hsplit0]
  have herase :
      (∑ i ∈ Finset.univ.erase j, m i * (Function.update u j (u j + δ) i + x * v i)) =
        ∑ i ∈ Finset.univ.erase j, m i * (u i + x * v i) := by
    apply Finset.sum_congr rfl
    intro i hi
    rw [Function.update_of_ne (Finset.ne_of_mem_erase hi)]
  rw [Function.update_self, herase]
  ring

/-- Useful-relation discrete-log extraction: whenever `maskDot x m u v = 0` and `∑_i m_i * v_i ≠ 0`
in `ZMod q`, the secret scalar `x` is uniquely recovered by `-(∑ m_i u_i) * (∑ m_i v_i)⁻¹`. -/
theorem useful_mask_relation_recovers_log {k q : ℕ} [Fact (Nat.Prime q)]
    (x : ZMod q) (m u v : Fin k → ZMod q)
    (hrel : maskDot x m u v = 0)
    (huseful : (∑ i, m i * v i) ≠ 0) :
    x = -(∑ i, m i * u i) * (∑ i, m i * v i)⁻¹ := by
  have hexpand : maskDot x m u v = (∑ i, m i * u i) + x * (∑ i, m i * v i) := by
    unfold maskDot
    have hterm : ∀ i, m i * (u i + x * v i) = m i * u i + x * (m i * v i) := fun _ => by ring
    simp_rw [hterm]
    rw [Finset.sum_add_distrib, ← Finset.mul_sum]
  rw [hexpand] at hrel
  have hx_mul : x * (∑ i, m i * v i) = -(∑ i, m i * u i) :=
    eq_neg_of_add_eq_zero_right hrel
  calc
    x = x * ((∑ i, m i * v i) * (∑ i, m i * v i)⁻¹) := by
      rw [mul_inv_cancel₀ huseful, mul_one]
    _ = (x * (∑ i, m i * v i)) * (∑ i, m i * v i)⁻¹ := by ring
    _ = -(∑ i, m i * u i) * (∑ i, m i * v i)⁻¹ := by rw [hx_mul]

/-- `L4-lifting` Lemma 1 (exact `1/q` law): for any nonzero relation vector `m : Fin k → ZMod q`
(`∃ j, m j ≠ 0`) and secret `x : ZMod q`, the exact number of mask pairs `(u, v)` satisfying
`maskDot x m u v = 0` equals `q ^ (2 * k - 1)` out of `q ^ (2 * k)`. -/
theorem fresh_mask_hits_card {k q : ℕ} [Fact (Nat.Prime q)]
    (x : ZMod q) (m : Fin k → ZMod q) (hm : ∃ j : Fin k, m j ≠ 0) :
    (Finset.univ.filter
        (fun uv : (Fin k → ZMod q) × (Fin k → ZMod q) => maskDot x m uv.1 uv.2 = 0)).card =
      q ^ (2 * k - 1) := by
  obtain ⟨j, hj⟩ := hm
  have hk_pos : 1 ≤ k := Nat.succ_le_of_lt j.pos
  set S := Finset.univ.filter
    (fun uv : (Fin k → ZMod q) × (Fin k → ZMod q) => maskDot x m uv.1 uv.2 = 0)
  have hbij :
      (S ×ˢ (Finset.univ : Finset (ZMod q))).card =
        (Finset.univ : Finset ((Fin k → ZMod q) × (Fin k → ZMod q))).card := by
    apply Finset.card_bij
      (fun p _ => (Function.update p.1.1 j (p.1.1 j + (m j)⁻¹ * p.2), p.1.2))
    · intro p _
      exact Finset.mem_univ _
    · intro p₁ hp₁ p₂ hp₂ heq
      rcases p₁ with ⟨⟨u₁, v₁⟩, t₁⟩
      rcases p₂ with ⟨⟨u₂, v₂⟩, t₂⟩
      rw [Finset.mem_product] at hp₁ hp₂
      have hu₁ : maskDot x m u₁ v₁ = 0 := (Finset.mem_filter.mp hp₁.1).2
      have hu₂ : maskDot x m u₂ v₂ = 0 := (Finset.mem_filter.mp hp₂.1).2
      have hv : v₁ = v₂ := Prod.mk.inj heq |>.2
      subst hv
      have hupd :
          Function.update u₁ j (u₁ j + (m j)⁻¹ * t₁) =
            Function.update u₂ j (u₂ j + (m j)⁻¹ * t₂) := Prod.mk.inj heq |>.1
      have hmd := congr_arg (fun w => maskDot x m w v₁) hupd
      rw [maskDot_update_add, maskDot_update_add, hu₁, hu₂, zero_add, zero_add,
        ← mul_assoc, ← mul_assoc, mul_inv_cancel₀ hj, one_mul, one_mul] at hmd
      subst hmd
      have hu_eq : u₁ = u₂ := by
        ext i
        by_cases hij : i = j
        · subst hij
          have hj_eq := congr_fun hupd i
          simp only [Function.update_self] at hj_eq
          exact add_right_cancel hj_eq
        · have hi_eq := congr_fun hupd i
          simpa [Function.update_of_ne hij] using hi_eq
      subst hu_eq
      rfl
    · intro uv _
      rcases uv with ⟨u', v'⟩
      set t := maskDot x m u' v'
      set u₀ := Function.update u' j (u' j - (m j)⁻¹ * t)
      have hu₀_zero : maskDot x m u₀ v' = 0 := by
        have hsub : u' j - (m j)⁻¹ * t = u' j + (-((m j)⁻¹ * t)) := sub_eq_add_neg _ _
        dsimp only [u₀]
        rw [hsub, maskDot_update_add, mul_neg, ← mul_assoc, mul_inv_cancel₀ hj, one_mul]
        exact add_neg_cancel t
      refine ⟨((u₀, v'), t), ?_, ?_⟩
      · rw [Finset.mem_product]
        exact ⟨Finset.mem_filter.mpr ⟨Finset.mem_univ _, hu₀_zero⟩, Finset.mem_univ _⟩
      · ext i
        · dsimp only [u₀]
          by_cases hij : i = j
          · subst hij
            simp [sub_add_cancel]
          · simp [Function.update_of_ne hij]
        · rfl
  rw [Finset.card_product] at hbij
  simp only [Finset.card_univ, Fintype.card_prod, Fintype.card_fun, Fintype.card_fin,
    ZMod.card] at hbij
  have hpow : q ^ k * q ^ k = q ^ (2 * k - 1) * q := by
    rw [← pow_add, ← two_mul]
    have h2k : 2 * k - 1 + 1 = 2 * k := Nat.sub_add_cancel (by omega)
    rw [← pow_succ, h2k]
  rw [hpow] at hbij
  exact Nat.eq_of_mul_eq_mul_right (Fact.out : Nat.Prime q).pos hbij

/-- `L4-lifting` Theorem X union core & function-field bounded-height specialization bound:
for any finite set `M` of nonzero candidate relation vectors in `Fin k → ZMod q`
(such as Cramer--Hadamard--Minkowski or Shioda bounded-height boxes), the number of fresh-mask
pairs `(u, v)` admitting any relation in `M` is at most `M.card * q ^ (2 * k - 1)`. -/
theorem fresh_mask_candidate_set_union_bound {k q : ℕ} [Fact (Nat.Prime q)]
    (x : ZMod q) (M : Finset (Fin k → ZMod q))
    (hM : ∀ m ∈ M, ∃ j : Fin k, m j ≠ 0) :
    (Finset.univ.filter
        (fun uv : (Fin k → ZMod q) × (Fin k → ZMod q) =>
          ∃ m ∈ M, maskDot x m uv.1 uv.2 = 0)).card ≤
      M.card * q ^ (2 * k - 1) := by
  let filterFor (m : Fin k → ZMod q) :=
    Finset.univ.filter (fun uv : (Fin k → ZMod q) × (Fin k → ZMod q) => maskDot x m uv.1 uv.2 = 0)
  have h_sub :
      Finset.univ.filter
          (fun uv : (Fin k → ZMod q) × (Fin k → ZMod q) =>
            ∃ m ∈ M, maskDot x m uv.1 uv.2 = 0) ⊆
        M.biUnion filterFor := by
    intro uv huv
    rw [Finset.mem_filter] at huv
    rcases huv.2 with ⟨m, hmM, hzero⟩
    exact Finset.mem_biUnion.mpr ⟨m, hmM, Finset.mem_filter.mpr ⟨Finset.mem_univ _, hzero⟩⟩
  calc
    (Finset.univ.filter
        (fun uv : (Fin k → ZMod q) × (Fin k → ZMod q) =>
          ∃ m ∈ M, maskDot x m uv.1 uv.2 = 0)).card
        ≤ (M.biUnion filterFor).card := Finset.card_le_card h_sub
    _ ≤ ∑ m ∈ M, (filterFor m).card := Finset.card_biUnion_le
    _ = ∑ _m ∈ M, q ^ (2 * k - 1) := by
      apply Finset.sum_congr rfl
      intro m hm_mem
      exact fresh_mask_hits_card x m (hM m hm_mem)
    _ = M.card * q ^ (2 * k - 1) := by
      rw [Finset.sum_const, smul_eq_mul]

#print axioms evalLinearCombination_map
#print axioms globalRelation_le_modularRelation
#print axioms globalRelation_le_iInf_modularRelation
#print axioms incremental_kernel_generator_zero
#print axioms incremental_kernel_step_complete
#print axioms torsion_coprime_specialization_kills_torsion
#print axioms torsion_relation_specializes_zero
#print axioms maskDot_update_add
#print axioms useful_mask_relation_recovers_log
#print axioms fresh_mask_hits_card
#print axioms fresh_mask_candidate_set_union_bound

end XedniScalingBridge
