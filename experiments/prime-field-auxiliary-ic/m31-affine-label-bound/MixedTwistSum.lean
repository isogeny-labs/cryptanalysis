import Mathlib

namespace M31MixedTwistSum

variable {G : Type*} [AddCommGroup G]

/-- P and T may each already be a signed sum. For a fixed P and an
anti-invariant T, their sum descends exactly when T is killed by two. -/
theorem fixedSum (σ : G →+ G) {P T : G} (hp : σ P = P) (ht : σ T = -T) :
    σ (P + T) = P + T ↔ (2 : ℕ) • T = 0 := by
  rw [map_add, hp, ht, add_right_inj, two_nsmul]
  constructor
  · intro h
    calc T + T = -T + T := congrArg (fun x => x + T) h.symm
         _ = 0 := neg_add_cancel T
  · intro h
    exact (eq_neg_of_add_eq_zero_left h).symm

theorem oddFixedSum (σ : G →+ G) {P T : G} (hp : σ P = P) (ht : σ T = -T)
    (odd : Odd (addOrderOf T)) : σ (P + T) = P + T ↔ T = 0 := by
  rw [fixedSum σ hp ht]
  constructor
  · intro h
    apply AddMonoid.addOrderOf_eq_one_iff.mp
    exact Nat.dvd_one.mp (odd.coprime_two_right ▸ Nat.dvd_gcd
      (dvd_refl _) (addOrderOf_dvd_iff_nsmul_eq_zero.mpr h))
  · rintro rfl
    simp

/-- Taking the trace of the mixed sum cancels the entire twist contribution. -/
theorem traceSum (σ : G →+ G) {P T : G} (hp : σ P = P) (ht : σ T = -T) :
    P + T + σ (P + T) = (2 : ℕ) • P := by
  rw [map_add, hp, ht, two_nsmul]
  abel

/-- The x-coordinate forgets the sign of the sum. Its second descent case
occurs precisely when the fixed component is killed by two. -/
theorem fixedX {K : Type*} [Field K] [DecidableEq K] {W : WeierstrassCurve.Affine K}
    (σ : W.Point →+ W.Point) {P T : W.Point} (hp : σ P = P) (ht : σ T = -T) :
    (σ (P + T)).xRep = (P + T).xRep ↔
      (2 : ℕ) • T = 0 ∨ (2 : ℕ) • P = 0 := by
  rw [WeierstrassCurve.Affine.Point.xRep_eq_xRep_iff, fixedSum σ hp ht]
  apply or_congr_right
  rw [map_add, hp, ht, neg_add, add_left_inj, two_nsmul]
  constructor
  · intro h
    calc P + P = -P + P := congrArg (fun x => x + P) h
         _ = 0 := neg_add_cancel P
  · exact eq_neg_of_add_eq_zero_left

end M31MixedTwistSum
