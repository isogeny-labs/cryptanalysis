import Mathlib.Tactic.Ring

namespace BranchElimination

variable {R : Type*} [CommRing R]

def cubic (X T : R) : R := T ^ 3 - X * T ^ 2 - 64
def remainder (a b c T : R) : R := a * T ^ 2 + b * T + c
def denominator (a b c X : R) : R := b * (a * X + b) - a * c
def numerator (a b c X : R) : R := 64 * a ^ 2 - c * (a * X + b)

/-- Exact elimination identity used to extract the selected cubic root. -/
theorem elimination_identity (a b c X T : R) :
    denominator a b c X * T - numerator a b c X =
      a * (a * cubic X T - T * remainder a b c T) +
      (a * X + b) * remainder a b c T := by
  unfold denominator numerator cubic remainder
  ring

/-- A common root of the cubic and quadratic remainder satisfies the
linear branch equation, without assuming that equation. -/
theorem branch_equation (a b c X T : R)
    (hF : cubic X T = 0) (hR : remainder a b c T = 0) :
    denominator a b c X * T = numerator a b c X := by
  have h : denominator a b c X * T - numerator a b c X = 0 := by
    simpa [hF, hR] using elimination_identity a b c X T
  exact sub_eq_zero.mp h

#print axioms elimination_identity
#print axioms branch_equation

end BranchElimination
