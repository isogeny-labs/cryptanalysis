import Mathlib.Algebra.Ring.Defs
import Mathlib.Tactic.LinearCombination

namespace J1728P23LocalReplay

variable {R : Type*} [CommRing R] (u : R)

theorem left_taylor_discriminant
    (h23 : (23 : R) = 0) (hu : u ^ 2 + 2 * u + 17 = 0) :
    (5 * u + 2) ^ 2 - 4 * 5 * (7 * u + 21) = 14 * u + 10 := by
  linear_combination 25 * hu - (8 * u + 37) * h23

theorem right_taylor_discriminant
    (h23 : (23 : R) = 0) (hu : u ^ 2 + 2 * u + 17 = 0) :
    (13 * u + 8) ^ 2 - 4 * 5 * (2 * u + 12) = 14 * u + 10 := by
  linear_combination 169 * hu - (8 * u + 133) * h23

theorem normalized_discriminant_square
    (h23 : (23 : R) = 0) (hu : u ^ 2 + 2 * u + 17 = 0) :
    (10 + 13 * u) ^ 2 = 14 * u + 10 := by
  linear_combination 169 * hu - (4 * u + 121) * h23

#print axioms left_taylor_discriminant
#print axioms right_taylor_discriminant
#print axioms normalized_discriminant_square

end J1728P23LocalReplay
