import Std
import Init.Grind.Ring.Basic

namespace BranchEquation
open Lean.Grind

/-- The Boolean branch uses zero for the original point and one for the
    adjacent-Frobenius image. -/
def bit {R : Type} [CommRing R] (branch : Bool) : R :=
  if branch then 1 else 0

/-- The single polynomial constraint exactly selects the original
    phi-chart or the image phi-chart. The source identity is
    `y = phi² + phi`. -/
theorem branch_equation {R : Type} [CommRing R]
    (phi y out : R) (branch : Bool) (hy : y = phi*phi + phi) :
    (1 + bit branch * y) * out = phi + bit branch * (phi*phi) ↔
      (if branch then (1 + y) * out = y else out = phi) := by
  cases branch with
  | false =>
      simp [bit]
      grind +ring
  | true =>
      simp [bit]
      rw [hy]
      grind +ring

/-- With the image chart denominator nonzero, the image output is
    uniquely determined by the branch equation. -/
theorem image_unique {R : Type} [Field R]
    (phi y out₁ out₂ : R) (hy : y = phi*phi + phi)
    (hdenom : 1 + y ≠ 0)
    (h₁ : (1 + bit true * y) * out₁ = phi + bit true * (phi*phi))
    (h₂ : (1 + bit true * y) * out₂ = phi + bit true * (phi*phi)) :
    out₁ = out₂ := by
  have a : (1+y)*out₁ = y := (branch_equation phi y out₁ true hy).mp h₁
  have b : (1+y)*out₂ = y := (branch_equation phi y out₂ true hy).mp h₂
  grind

#print axioms branch_equation
#print axioms image_unique

end BranchEquation
