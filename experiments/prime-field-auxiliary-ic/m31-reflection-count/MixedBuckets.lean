import Correlation
import M31FixtureObstruction

namespace M31Reflection
open Finset

/-- One representative per mixed bucket, using the smaller canonical coordinate. -/
def mixedRepresentative (x : F) : Prop :=
  x.val < (-x).val ∧ ¬ (IsSquare (cubic x) ↔ IsSquare (cubic (-x)))

private noncomputable def mark (x : F) : ℤ := by
  classical exact if mixedRepresentative x then 1 else 0

theorem sign_at (x : F) : quadraticChar F (cubic x) =
    if IsSquare (cubic x) then 1 else -1 := by
  classical
  have nz : cubic x ≠ 0 := M31FixtureObstruction.no_root x
  by_cases hs : IsSquare (cubic x)
  · simpa only [hs, ↓reduceIte] using (quadraticChar_one_iff_isSquare nz).mpr hs
  · simpa only [hs, ↓reduceIte] using (quadraticChar_neg_one_iff_not_isSquare.mpr hs)

private theorem split (x : F) : quadraticChar F (cubic x * cubic (-x)) =
    1 - 2 * (mark x + mark (-x)) := by
  classical
  rw [map_mul, sign_at, sign_at]
  unfold mark mixedRepresentative
  have negneg : - -x = x := neg_neg x
  erw [negneg]
  rcases lt_trichotomy x.val (-x).val with h | h | h
  · have hr := not_lt_of_gt h
    by_cases a : IsSquare (cubic x) <;> by_cases b : IsSquare (cubic (-x)) <;> simp [a,b,h,hr]
  · have fixed := ZMod.val_injective 2147483647 h
    rw [← fixed]
    by_cases a : IsSquare (cubic x) <;> simp [a]
  · have hr := not_lt_of_gt h
    by_cases a : IsSquare (cubic x) <;> by_cases b : IsSquare (cubic (-x)) <;> simp [a,b,h,hr]

noncomputable def mixedBuckets : Finset F := by
  classical exact univ.filter mixedRepresentative

theorem mixed_bucket_count : mixedBuckets.card = 536844426 := by
  classical
  have h := correlation_exact
  simp_rw [split] at h
  rw [sum_sub_distrib, ← mul_sum, sum_add_distrib] at h
  have perm : (∑ x : F, mark (-x)) = ∑ x : F, mark x := Equiv.sum_comp (Equiv.neg F) mark
  rw [perm] at h
  have total : (∑ _x : F, (1 : ℤ)) = 2147483647 := by simp [F, ZMod.card]
  rw [total] at h
  have count : (∑ x : F, mark x) = (mixedBuckets.card : ℤ) := by
    exact Finset.sum_boole (R := ℤ) mixedRepresentative univ
  rw [count] at h
  omega

end M31Reflection

#print axioms M31Reflection.mixed_bucket_count
