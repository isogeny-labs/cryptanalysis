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

end M31MixedTwistSum
