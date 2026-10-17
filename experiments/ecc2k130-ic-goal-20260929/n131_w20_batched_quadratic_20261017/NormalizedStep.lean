import Std
import Init.Grind.Ring.Basic

namespace NormalizedStep
open Lean.Grind

/-- Squaring a linear expression modulo a monic quadratic in characteristic two. -/
theorem linearized_step {R : Type} [CommRing R]
    (charTwo : (2 : R) = 0)
    (b r s u v a : R) (root : b * b = r * b + s) :
    (u * b + v) * (u * b + v) + a * (u * b + v) =
      (r * (u * u) + a * u) * b + (s * (u * u) + v * v + a * v) := by
  grind

/-- The nonexceptional quadratic can be normalized once its leading
    coefficient has an inverse. The scaled coefficient equations are the
    exact obligations discharged by the field inverses in the native code. -/
theorem normalized_root {R : Type} [Field R]
    (A B E b r s : R) (charTwo : (2 : R) = 0)
    (nonzero : A ≠ 0)
    (rootEquation : A * (b * b) + B * b + E = 0)
    (scaledB : A * r = B) (scaledE : A * s = E) :
    b * b = r * b + s := by
  grind

/-- The initial normalized linear expression represents the same rational
    pair output as the denominator-carrying recurrence. -/
theorem initial_normalization {R : Type} [CommRing R]
    (E inverseE Cr Hr A B b : R)
    (inverseLaw : E * inverseE = 1) :
    E * ((Cr + Hr * A * inverseE) * b + Hr * B * inverseE) =
      (Cr * E + Hr * A) * b + Hr * B := by
  grind

/-- A reverse batch-inversion step gives the current factor inverse and
    leaves an inverse of the preceding prefix product. -/
theorem batch_inverse_step {R : Type} [CommRing R]
    (pre denominator inverseProduct : R)
    (h : inverseProduct * (pre * denominator) = 1) :
    (inverseProduct * pre) * denominator = 1 ∧
      (inverseProduct * denominator) * pre = 1 := by
  constructor <;> grind

#print axioms linearized_step
#print axioms normalized_root
#print axioms initial_normalization
#print axioms batch_inverse_step

end NormalizedStep
