import Std
import Init.Grind.Ring.Basic

namespace HomogeneousS3
open Lean.Grind

/-- The reciprocal chart S3 polynomial used by the existing N131 circuit. -/
def p3 {R : Type} [CommRing R] (a b c : R) : R :=
  (a*a+a)*(b*b+b)*(c*c+c)+(a+b+c)*(a+b+c)

/-- Numerator of z²+z when z=n/d. -/
def yNum {R : Type} [CommRing R] (n d : R) : R := n*n+n*d

theorem yNum_factored {R : Type} [CommRing R] (n d : R) :
    yNum n d = n*(n+d) := by
  dsimp [yNum]
  grind +ring

/-- Original and adjacent-image charts in one Boolean branch. -/
def bit {R : Type} [CommRing R] (branch : Bool) : R :=
  if branch then 1 else 0

def branchN {R : Type} [CommRing R] (phi : R) (branch : Bool) : R :=
  phi + bit branch * (phi*phi)

def branchD {R : Type} [CommRing R] (phi : R) (branch : Bool) : R :=
  1 + bit branch * (phi*phi+phi)

/-- The image denominator is nonzero under the exact odd-degree trace
    consequence used by the N131 source audit. -/
theorem branch_denominator_nonzero {R : Type} [Field R]
    (phi : R) (branch : Bool) (himage : 1+(phi*phi+phi) ≠ 0) :
    branchD phi branch ≠ 0 := by
  cases branch <;> dsimp [branchD, bit] <;> grind +ring

/-- Homogeneous S3 residual for three numerator/denominator chart pairs. -/
def cleared {R : Type} [CommRing R]
    (n₁ d₁ n₂ d₂ n₃ d₃ : R) : R :=
  yNum n₁ d₁ * yNum n₂ d₂ * yNum n₃ d₃ +
  (n₁*d₂*d₃+n₂*d₁*d₃+n₃*d₁*d₂)*
  (n₁*d₂*d₃+n₂*d₁*d₃+n₃*d₁*d₂)

/-- Clearing the three nonzero chart denominators preserves the exact S3
    residual. The polynomial identity itself holds over any commutative ring. -/
theorem cleared_identity {R : Type} [CommRing R]
    (n₁ d₁ z₁ n₂ d₂ z₂ n₃ d₃ z₃ : R)
    (h₁ : d₁*z₁=n₁) (h₂ : d₂*z₂=n₂) (h₃ : d₃*z₃=n₃) :
    (d₁*d₂*d₃)*(d₁*d₂*d₃)*p3 z₁ z₂ z₃ =
      cleared n₁ d₁ n₂ d₂ n₃ d₃ := by
  dsimp [p3, cleared, yNum]
  rw [← h₁, ← h₂, ← h₃]
  grind +ring

/-- With nonzero denominators, the cleared equation has exactly the same
    zeros as the original S3 equation. -/
theorem cleared_zero_iff {R : Type} [Field R]
    (n₁ d₁ z₁ n₂ d₂ z₂ n₃ d₃ z₃ : R)
    (h₁ : d₁*z₁=n₁) (h₂ : d₂*z₂=n₂) (h₃ : d₃*z₃=n₃)
    (hd₁ : d₁ ≠ 0) (hd₂ : d₂ ≠ 0) (hd₃ : d₃ ≠ 0) :
    p3 z₁ z₂ z₃ = 0 ↔ cleared n₁ d₁ n₂ d₂ n₃ d₃ = 0 := by
  have h := cleared_identity n₁ d₁ z₁ n₂ d₂ z₂ n₃ d₃ z₃ h₁ h₂ h₃
  have hd : d₁*d₂*d₃ ≠ 0 := by grind
  constructor
  · intro hz
    calc
      cleared n₁ d₁ n₂ d₂ n₃ d₃ =
          (d₁*d₂*d₃)*(d₁*d₂*d₃)*p3 z₁ z₂ z₃ := h.symm
      _ = 0 := by grind
  · intro hc
    have hz : (d₁*d₂*d₃)*(d₁*d₂*d₃)*p3 z₁ z₂ z₃ = 0 := h.trans hc
    have hh : (d₁*d₂*d₃)*(d₁*d₂*d₃) ≠ 0 := by grind
    grind

#print axioms cleared_identity
#print axioms cleared_zero_iff
#print axioms yNum_factored
#print axioms branch_denominator_nonzero

end HomogeneousS3
