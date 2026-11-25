import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic

namespace M31.PrimitiveMinor

/-- The first occupied coordinate fixes the global sign. -/
def Canonical {n : ℕ} (a : Fin n → ℤ) : Prop :=
  ∃ i, 0 < a i ∧ ∀ j < i, a j = 0

/-- Equal positive L1 weight removes the scaling ambiguity, even for
nonprimitive vectors. Fixing the sign then distinguishes every two rows. -/
theorem exists_minor {n : ℕ} (a b : Fin n → ℤ) (w : ℤ) (hw : 0 < w)
    (ha : ∑ j, |a j| = w) (hb : ∑ j, |b j| = w)
    (ca : Canonical a) (cb : Canonical b) (hne : a ≠ b) :
    ∃ i j, a i * b j - b i * a j ≠ 0 := by
  by_contra! hz
  have cross (i j : Fin n) : a i * b j = b i * a j := sub_eq_zero.mp (hz i j)
  obtain ⟨i, ai, az⟩ := ca
  obtain ⟨k, bk, bz⟩ := cb
  have piv : i = k := by
    rcases lt_trichotomy i k with h | h | h
    · have e := cross i k
      rw [bz i h, zero_mul] at e
      exact False.elim ((mul_pos ai bk).ne' e)
    · exact h
    · have e := cross k i
      rw [az k h, zero_mul] at e
      exact False.elim ((mul_pos bk ai).ne' e.symm)
  subst k
  have weights : |a i| * w = |b i| * w := by
    calc |a i| * w = ∑ j, |a i * b j| := by rw [← hb, Finset.mul_sum]; simp only [abs_mul]
         _ = ∑ j, |b i * a j| := Finset.sum_congr rfl fun j _ => congrArg abs (cross i j)
         _ = |b i| * w := by rw [← ha, Finset.mul_sum]; simp only [abs_mul]
  rw [abs_of_pos ai, abs_of_pos bk] at weights
  have same : a i = b i := mul_right_cancel₀ hw.ne' weights
  apply hne
  funext j
  have e := cross i j
  rw [← same] at e
  exact (mul_left_cancel₀ ai.ne' e).symm

/-- An equal positive weight pair of weight at most eight has a certified pivot directly in the group-order field. -/
theorem bounded_modular_minor {n : ℕ} (a b : Fin n → ℤ)
    {w : ℤ} (hw : 0 < w) (cap : w ≤ 8)
    (ha : ∑ j, |a j| = w) (hb : ∑ j, |b j| = w)
    (ca : Canonical a) (cb : Canonical b) (hne : a ≠ b) :
    ∃ i j, (a i : ZMod 2147505293) * b j - b i * a j ≠ 0 := by
  obtain ⟨i, j, h⟩ := exists_minor a b w hw ha hb ca cb hne
  refine ⟨i, j, ?_⟩
  have bound (v : Fin n → ℤ) (hv : ∑ k, |v k| = w) (k : Fin n) : |v k| ≤ 8 := by
    apply le_trans _ cap
    rw [← hv]
    exact Finset.single_le_sum (fun t _ => abs_nonneg (v t)) (Finset.mem_univ k)
  have prod (k l : Fin n) : |a k * b l| ≤ 64 := by
    rw [abs_mul]
    exact mul_le_mul (bound a ha k) (bound b hb l) (abs_nonneg _) (by decide)
  intro hz
  have hc : ((a i * b j - b i * a j : ℤ) : ZMod 2147505293) = 0 := by
    push_cast
    exact hz
  obtain ⟨z, he⟩ := (ZMod.intCast_zmod_eq_zero_iff_dvd _ _).mp hc
  have h₁ := abs_le.mp (prod i j)
  have h₂ := abs_le.mp (prod j i)
  rw [mul_comm (a j) (b i)] at h₂
  norm_num at he
  omega

/-- A weight-eight pair has a certified pivot directly in the group-order field. -/
theorem exists_modular_minor {n : ℕ} (a b : Fin n → ℤ)
    (ha : ∑ j, |a j| = 8) (hb : ∑ j, |b j| = 8)
    (ca : Canonical a) (cb : Canonical b) (hne : a ≠ b) :
    ∃ i j, (a i : ZMod 2147505293) * b j - b i * a j ≠ 0 :=
  bounded_modular_minor a b (by decide) (by decide) ha hb ca cb hne

end M31.PrimitiveMinor
