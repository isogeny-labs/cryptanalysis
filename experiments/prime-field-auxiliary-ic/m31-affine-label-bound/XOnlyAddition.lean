import Mathlib

namespace M31XOnlyAddition

variable {K : Type*} [Field K] [DecidableEq K] {W : WeierstrassCurve.Affine K}

/-- xRep also covers infinity. The two outputs for a sign-ambiguous input
coincide exactly in the two-torsion cases. -/
theorem sameOutput (P Q : W.Point) :
    (P + Q).xRep = (P - Q).xRep ↔ (2 : ℕ) • Q = 0 ∨ (2 : ℕ) • P = 0 := by
  rw [WeierstrassCurve.Affine.Point.xRep_eq_xRep_iff, sub_eq_add_neg, neg_add,
    neg_neg, add_right_inj, add_left_inj, two_nsmul, two_nsmul]
  simp only [← eq_neg_iff_add_eq_zero]

/-- A deterministic binary operation on projective x-representatives cannot
implement ordinary addition for all signed inputs when P,Q are not killed by 2. -/
theorem noBinaryAdd (P Q : W.Point) (hp : (2 : ℕ) • P ≠ 0) (hq : (2 : ℕ) • Q ≠ 0) :
    ¬ ∃ f : (Fin 2 → K) → (Fin 2 → K) → (Fin 2 → K),
      ∀ A B : W.Point, f A.xRep B.xRep = (A+B).xRep := by
  rintro ⟨f,h⟩
  have eq : (P+Q).xRep = (P-Q).xRep := by
    calc (P+Q).xRep = f P.xRep Q.xRep := (h P Q).symm
         _ = (P-Q).xRep := by simpa only [WeierstrassCurve.Affine.Point.xRep_neg,
              sub_eq_add_neg] using h P (-Q)
  exact ((sameOutput P Q).mp eq).elim hq hp

/-- At the state R+T the difference needed for step S is R+T-S.
Its x-representative agrees with the saved state R in exactly two cases. -/
theorem previousX (R T S : W.Point) :
    (R+T-S).xRep = R.xRep ↔ T = S ∨ (2 : ℕ) • R = S-T := by
  rw [WeierstrassCurve.Affine.Point.xRep_eq_xRep_iff, two_nsmul]
  constructor
  · rintro (h | h)
    · left
      exact add_left_cancel (a := R) ((sub_eq_iff_eq_add.mp h))
    · right
      linear_combination (norm := abel) h
  · rintro (rfl | h)
    · simp
    · right
      linear_combination (norm := abel) h

theorem uniquePrevious (T S : W.Point) (different : T ≠ S)
    (odd : Odd (Nat.card W.Point)) : ∃! R : W.Point, (R+T-S).xRep = R.xRep := by
  simp only [previousX, different, false_or]
  exact odd.coprime_two_right.nsmul_right_bijective.existsUnique (S-T)

end M31XOnlyAddition
