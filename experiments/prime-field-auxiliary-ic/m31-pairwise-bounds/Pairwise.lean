import Mathlib

namespace M31Pairwise

/-- Two observations of a uniform start and a uniform step, with other steps fixed. -/
def twoObservations {F : Type*} [Field F] (a b s t : F) (h : b ≠ a) :
    (F × F) ≃ (F × F) where
  toFun := fun (u,v) => (u + a*v + s, u + b*v + t)
  invFun := fun (x,y) =>
    let v := (y-x+s-t)/(b-a)
    (x-a*v-s, v)
  left_inv := by
    rintro ⟨u,v⟩
    apply Prod.ext <;> dsimp <;> field_simp [sub_ne_zero.mpr h] <;> ring
  right_inv := by
    rintro ⟨x,y⟩
    apply Prod.ext <;> dsimp <;> field_simp [sub_ne_zero.mpr h] <;> ring

theorem threeHitMajorant (z : ℕ) :
    (if 3 ≤ z then 6 else 0) ≤ z * (z-1) := by
  split_ifs with h
  · exact Nat.mul_le_mul h (by omega : 2 ≤ z-1)
  · omega

theorem fourteenHitMajorant (z : ℤ) :
    (if 14 ≤ z then 90 else 0) ≤ (z-4)*(z-5) := by
  split_ifs with h
  · nlinarith [mul_nonneg (show 0 ≤ z-14 by omega) (show 0 ≤ z+5 by omega)]
  · by_cases hz : z ≤ 4
    · exact mul_nonneg_of_nonpos_of_nonpos (by omega) (by omega)
    · exact mul_nonneg (by omega) (by omega)

/-- Aggregate the integer majorant for any finite nonnegatively weighted histogram. -/
theorem weightedFourteen {ι : Type*} (S : Finset ι) (w : ι → ℝ)
    (hits : ι → ℤ) (hw : ∀ i ∈ S, 0 ≤ w i) :
    (∑ i ∈ S, w i * (if 14 ≤ hits i then 90 else 0)) ≤
    ∑ i ∈ S, w i * (((hits i : ℝ)-4)*((hits i : ℝ)-5)) := by
  apply Finset.sum_le_sum
  intro i hi
  apply mul_le_mul_of_nonneg_left _ (hw i hi)
  have bound := fourteenHitMajorant (hits i)
  split_ifs at * <;> exact_mod_cast bound

end M31Pairwise
