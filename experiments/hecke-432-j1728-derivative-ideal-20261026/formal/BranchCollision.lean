import Mathlib.Tactic.Ring

namespace BranchCollision

variable {K : Type*} [Field K]

def cubic (X T : K) : K := T ^ 3 - X * T ^ 2 - 64
def remainder (a b c T : K) : K := a * T ^ 2 + b * T + c
def denominator (a b c X : K) : K := b * (a * X + b) - a * c
def numerator (a b c X : K) : K := 64 * a ^ 2 - c * (a * X + b)

/-- The exact linear branch equation belongs to the cubic/remainder ideal. -/
theorem elimination_identity (a b c X T : K) :
    denominator a b c X * T - numerator a b c X =
      a * (a * cubic X T - T * remainder a b c T) +
      (a * X + b) * remainder a b c T := by
  unfold denominator numerator cubic remainder
  ring

theorem branch_equation (a b c X T : K)
    (hF : cubic X T = 0) (hR : remainder a b c T = 0) :
    denominator a b c X * T = numerator a b c X := by
  have h : denominator a b c X * T - numerator a b c X = 0 := by
    simpa [hF, hR] using elimination_identity a b c X T
  exact sub_eq_zero.mp h

/-- Two distinct common cubic/remainder roots force both branch values to zero. -/
theorem two_common_roots_force_indeterminacy
    (a b c X T₁ T₂ : K)
    (hF₁ : cubic X T₁ = 0) (hR₁ : remainder a b c T₁ = 0)
    (hF₂ : cubic X T₂ = 0) (hR₂ : remainder a b c T₂ = 0)
    (hne : T₁ ≠ T₂) :
    denominator a b c X = 0 ∧ numerator a b c X = 0 := by
  have h₁ := branch_equation a b c X T₁ hF₁ hR₁
  have h₂ := branch_equation a b c X T₂ hF₂ hR₂
  have hprod : denominator a b c X * (T₁ - T₂) = 0 := by
    calc
      denominator a b c X * (T₁ - T₂) =
          denominator a b c X * T₁ - denominator a b c X * T₂ := by ring
      _ = numerator a b c X - numerator a b c X := by rw [h₁, h₂]
      _ = 0 := by ring
  have hD : denominator a b c X = 0 := by
    rcases mul_eq_zero.mp hprod with hd | ht
    · exact hd
    · exact False.elim (hne (sub_eq_zero.mp ht))
  constructor
  · exact hD
  · simpa [hD] using h₁.symm

/-- When the quadratic leading coefficient is nonzero, a zero-over-zero
branch makes every root of the remainder a root of the cubic. -/
theorem indeterminate_branch_forces_cubic_on_remainder_roots
    (a b c X T : K) (ha : a ≠ 0)
    (hD : denominator a b c X = 0)
    (hN : numerator a b c X = 0)
    (hR : remainder a b c T = 0) : cubic X T = 0 := by
  have h : a * (a * cubic X T) = 0 := by
    simpa [hD, hN, hR] using (elimination_identity a b c X T).symm
  rcases mul_eq_zero.mp h with ha0 | hinner
  · exact False.elim (ha ha0)
  rcases mul_eq_zero.mp hinner with ha0 | hF
  · exact False.elim (ha ha0)
  · exact hF

/-- For two distinct roots of the quadratic remainder, both lie on the
cubic exactly when the rational branch is zero-over-zero. -/
theorem two_remainder_roots_common_iff_indeterminate
    (a b c X T₁ T₂ : K) (ha : a ≠ 0)
    (hR₁ : remainder a b c T₁ = 0)
    (hR₂ : remainder a b c T₂ = 0)
    (hne : T₁ ≠ T₂) :
    (cubic X T₁ = 0 ∧ cubic X T₂ = 0) ↔
      (denominator a b c X = 0 ∧ numerator a b c X = 0) := by
  constructor
  · rintro ⟨hF₁, hF₂⟩
    exact two_common_roots_force_indeterminacy a b c X T₁ T₂
      hF₁ hR₁ hF₂ hR₂ hne
  · rintro ⟨hD, hN⟩
    exact ⟨indeterminate_branch_forces_cubic_on_remainder_roots
             a b c X T₁ ha hD hN hR₁,
           indeterminate_branch_forces_cubic_on_remainder_roots
             a b c X T₂ ha hD hN hR₂⟩

#print axioms elimination_identity
#print axioms branch_equation
#print axioms two_common_roots_force_indeterminacy
#print axioms indeterminate_branch_forces_cubic_on_remainder_roots
#print axioms two_remainder_roots_common_iff_indeterminate

end BranchCollision
