import Std

/-!
The pair-product inverse identity over a characteristic-two commutative ring.
The application uses a binary field and products r with r ≠ 1.
-/

open Lean.Grind

namespace QuadraticInverse

def resultant {K : Type} [CommRing K] (A B D S r : K) : K :=
  (D + S * A)^2 + S * B^2 + r * B * (D + S * (A + B)) +
    r^2 * D * (A + B + D)

def norm {K : Type} [CommRing K] (A B D S r : K) : K :=
  let L := 1 + r
  let M := L * B + r * A
  let N := L * D + S * A
  L * N * N + r * N * M + S * M * M

/-- The cubic-looking inverse norm factors into the excluded factor and
    a quadratic-in-product resultant. -/
theorem norm_eq_factor_resultant {K : Type} [CommRing K]
    (h2 : (2 : K) = 0) (A B D S r : K) :
    norm A B D S r = (1 + r) * resultant A B D S r := by
  unfold norm resultant
  dsimp
  grind +ring

/-- An actual common root of the two quadratic equations passes the
    quadratic inverse filter, provided the excluded factor is cancellable. -/
theorem common_root_resultant_zero {K : Type} [CommRing K]
    (h2 : (2 : K) = 0) (A B D S r d : K)
    (hL : ∀ x : K, (1 + r) * x = 0 → x = 0)
    (hP : (1 + r) * d * d + r * d + S = 0)
    (hU : A * d * d + B * d + D = 0) :
    resultant A B D S r = 0 := by
  have hnorm : norm A B D S r = 0 := by
    unfold norm
    dsimp
    grind +ring
  rw [norm_eq_factor_resultant h2 A B D S r] at hnorm
  exact hL _ hnorm

#print axioms QuadraticInverse.norm_eq_factor_resultant
#print axioms QuadraticInverse.common_root_resultant_zero
