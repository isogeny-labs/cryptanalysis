import Std

namespace ReciprocalCubic
open Lean.Grind
variable {F : Type} [CommRing F]

/-- Reciprocal cubic with its linear factor exposed. -/
def value (b x : F) := (x+1)*(x*x+b*x+1)

/-- The same parameter b applies to both coordinates of a reciprocal pair. -/
theorem reciprocal (b x y : F) (h : x*y=1) :
    value b x = x^3 * value b y := by
  unfold value
  grind

theorem parentNorm (b x y : F) (h : x*y=1) :
    value b x * value b y = (x+y+2)*(x+y+b)^2 := by
  unfold value
  grind

#print axioms reciprocal
#print axioms parentNorm
/-- An integer-valued character taking the value -1 on x flips the sign.
Multiplicativity relates the signs of the two nonzero values. -/
theorem opposite_on_nonsquare (b x y : F) (h : x*y=1)
    (χ : F → Int) (mult : ∀ u v, χ (u*v) = χ u * χ v)
    (negative : χ x = -1) :
    χ (value b x) = -χ (value b y) := by
  rw [reciprocal b x y h, mult]
  have cube : x^3 = (x*x)*x := by grind
  rw [cube, mult, mult, negative]
  omega

theorem zero_exception {K : Type} [Field K] (b x y : K)
    (h : x*y=1) (distinct : x ≠ y) :
    value b x = 0 ↔ x+y = -b := by
  have nz : x ≠ 0 := by grind
  have ne : x+1 ≠ 0 := by
    intro hx
    apply distinct
    grind
  have eq : value b x = ((x+1)*x)*(x+y+b) := by unfold value; grind
  rw [eq]
  grind

#print axioms opposite_on_nonsquare
#print axioms zero_exception
end ReciprocalCubic
