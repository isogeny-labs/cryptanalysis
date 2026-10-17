import Std
import Init.Grind.Ring.Basic

namespace S3Inverse
open Lean.Grind

/-- The reciprocal-coordinate S3 equation is quadratic in the second
    coordinate when the first coordinate and target are fixed. -/
theorem s3_second_quadratic {F : Type} [Field F] (a b t : F) :
    (a * b * t) * (a * b * t) + a * b * t + a * a + b * b + t * t =
      (1 + (a * t) * (a * t)) * (b * b) + (a * t) * b + (a * a + t * t) := by
  grind +ring

/-- A half-trace solution of the normalized Artin–Schreier equation
    reconstructs a root of the S3 quadratic. Inverses and characteristic
    two are explicit assumptions. -/
theorem halftrace_root_sound {F : Type} [Field F]
    (A B D invA invB v : F)
    (char_two : ∀ x : F, x + x = 0)
    (hA : A * invA = 1)
    (hB : B * invB = 1)
    (hAS : v * v + v = A * D * invB * invB) :
    let b := B * invA * v
    A * b * b + B * b + D = 0 := by
  dsimp
  have htwo := char_two (1 : F)
  grind +ring

/-- The second source product recovered from a nonzero second output
    satisfies the fixed-seed pair equation. -/
theorem recover_second_product {F : Type} [Field F]
    (C H b invB : F)
    (char_two : ∀ x : F, x + x = 0)
    (hinv : b * invB = 1) :
    let q := (C * b * b + H) * invB
    C * b * b + q * b + H = 0 := by
  dsimp
  have htwo := char_two (1 : F)
  grind +ring

/-- The normalized S3 Artin–Schreier right-hand side separates into
    the reciprocal-square expressions of its two known coordinates. -/
theorem normalized_rhs_separates {F : Type} [Field F]
    (a t ia it : F)
    (char_two : ∀ x : F, x + x = 0)
    (ha : a * ia = 1) (ht : t * it = 1) :
    (1 + (a * t) * (a * t)) * (a * a + t * t) *
      ((ia * it) * (ia * it)) =
    a * a + ia * ia + t * t + it * it := by
  have htwo := char_two (1 : F)
  grind +ring

/-- For a trace-like additive map invariant under squaring, the S3
    solvability trace vanishes whenever both known coordinates satisfy
    the binary-curve reciprocal-x trace criterion. -/
theorem normalized_rhs_trace_zero {F K : Type}
    [Field F] [AddCommGroup K]
    (a t ia it : F) (tr : F → K)
    (char_two : ∀ x : F, x + x = 0)
    (ha : a * ia = 1) (ht : t * it = 1)
    (hadd : ∀ x y, tr (x + y) = tr x + tr y)
    (hsquare : ∀ x, tr (x * x) = tr x)
    (hcurvea : tr (a * a + ia) = 0)
    (hcurvet : tr (t * t + it) = 0) :
    tr ((1 + (a * t) * (a * t)) * (a * a + t * t) *
      ((ia * it) * (ia * it))) = 0 := by
  rw [normalized_rhs_separates a t ia it char_two ha ht]
  have hsplit : a * a + ia * ia + t * t + it * it =
      (a * a + ia * ia) + (t * t + it * it) := by grind +ring
  rw [hsplit, hadd, hadd, hadd, hsquare ia, hsquare it]
  have hca : tr (a * a) + tr ia = 0 := by
    rw [← hadd]
    exact hcurvea
  have hct : tr (t * t) + tr it = 0 := by
    rw [← hadd]
    exact hcurvet
  rw [hca, hct]
  exact AddCommMonoid.add_zero 0

/-- The reciprocal-x trace condition follows from the Artin–Schreier
    coordinate equation for a curve point. -/
theorem reciprocal_curve_trace_zero {F K : Type}
    [Field F] [AddCommGroup K]
    (a ia v : F) (tr : F → K)
    (hcoordinate : v * v + v = a * a + ia)
    (hadd : ∀ x y, tr (x + y) = tr x + tr y)
    (hsquare : ∀ x, tr (x * x) = tr x)
    (char_two_target : ∀ x : K, x + x = 0) :
    tr (a * a + ia) = 0 := by
  rw [← hcoordinate, hadd, hsquare]
  exact char_two_target (tr v)

#print axioms s3_second_quadratic
#print axioms halftrace_root_sound
#print axioms recover_second_product
#print axioms normalized_rhs_separates
#print axioms normalized_rhs_trace_zero
#print axioms reciprocal_curve_trace_zero

end S3Inverse
