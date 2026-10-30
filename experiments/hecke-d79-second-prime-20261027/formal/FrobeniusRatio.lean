/- Finite arithmetic controlling the projective degree-13 Frobenius cycle length. -/
namespace FrobeniusRatio

theorem p179_characteristic_roots :
    (2 * 2 + 179) % 13 = (20 * 2) % 13 ∧
    (5 * 5 + 179) % 13 = (20 * 5) % 13 ∧
    2 % 13 ≠ 5 % 13 := by decide

theorem p179_eigenvalue_ratio : (2 * 8) % 13 = 3 ∧ (5 * 8) % 13 = 1 := by
  decide

theorem p179_ratio_order_three :
    3 ^ 3 % 13 = 1 ∧
    (∀ k : Fin 2, 3 ^ (k.val + 1) % 13 ≠ 1) := by decide

theorem p83_characteristic_roots :
    (7 * 7 + 83) % 13 = (4 * 7) % 13 ∧
    (10 * 10 + 83) % 13 = (4 * 10) % 13 ∧
    7 % 13 ≠ 10 % 13 := by decide

theorem p83_eigenvalue_ratio : (10 * 2) % 13 = 7 ∧ (7 * 2) % 13 = 1 := by
  decide

theorem p83_ratio_order_twelve :
    7 ^ 12 % 13 = 1 ∧
    (∀ k : Fin 11, 7 ^ (k.val + 1) % 13 ≠ 1) := by decide

#print axioms p179_characteristic_roots
#print axioms p179_eigenvalue_ratio
#print axioms p179_ratio_order_three
#print axioms p83_characteristic_roots
#print axioms p83_eigenvalue_ratio
#print axioms p83_ratio_order_twelve

end FrobeniusRatio
