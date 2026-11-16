import Std.Tactic

/-! Faithful structural implications. Actual geometric maps, abelian group
objects, V4 correspondence, halving on the odd subgroup and polarization
degree interpretation remain separate written/native bridges. -/
set_option autoImplicit false
namespace GluingChain223

theorem two_dual_pairs_give_both_four {A J L : Type}
    (phi : A → J) (norm : J → A) (phiPrime : A → L) (normPrime : L → A)
    (doubleA : A → A) (doubleJ : J → J) (doubleL : L → L)
    (oldA : ∀ a, norm (phi a) = doubleA a)
    (oldJ : ∀ x, phi (norm x) = doubleJ x)
    (newA : ∀ a, normPrime (phiPrime a) = doubleA a)
    (newL : ∀ y, phiPrime (normPrime y) = doubleL y) :
    (∀ x, phi (normPrime (phiPrime (norm x))) = doubleJ (doubleJ x)) ∧
    (∀ y, phiPrime (norm (phi (normPrime y))) = doubleL (doubleL y)) := by
  constructor
  · intro x
    rw [newA, ← oldA (norm x), oldJ, oldJ]
  · intro y
    rw [oldA, ← newA (normPrime y), newL, newL]

theorem pullback_injective_from_actual_double_inverse {A J : Type}
    (phi : A → J) (norm : J → A) (double half : A → A)
    (composition : ∀ a, norm (phi a) = double a)
    (inverseOnDomain : ∀ a, half (double a) = a) :
    ∀ a b, phi a = phi b → a = b := by
  intro a b equal
  have h := congrArg (fun x => half (norm x)) equal
  simpa only [composition, inverseOnDomain] using h

theorem polarized_product_degree_one_column (x y z : Nat)
    (degree : x+y+z=1) :
    (x=1 ∧ y=0 ∧ z=0) ∨ (x=0 ∧ y=1 ∧ z=0) ∨ (x=0 ∧ y=0 ∧ z=1) := by
  omega

end GluingChain223
