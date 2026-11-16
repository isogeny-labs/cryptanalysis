import Std.Tactic
set_option autoImplicit false

/-! Faithful conditional arithmetic and functional implications. Actual
abelian/Picard objects, exact torsion sequence, etale kernel cardinalities,
finite-abelian classification and polarization interpretation remain written.
No holes, custom axioms or native evaluation. -/
namespace ChainKernels223

theorem kernel_type_from_order_and_two_torsion (a b d : Nat)
    (order : 2*a+b=6) (twoTorsion : a+b=3+d) :
    a=3-d ∧ b=2*d ∧ d≤3 := by omega

theorem free_four_kernel_iff_disjoint (a b d : Nat)
    (order : 2*a+b=6) (twoTorsion : a+b=3+d) :
    (a=3 ∧ b=0) ↔ d=0 := by omega

theorem same_product_two_steps_collapse {A J B C : Type}
    (normOld : J → A) (phiB : A → B) (normB : B → A)
    (phiC : A → C) (normC : C → A) (doubleA : A → A) (doubleC : C → C)
    (pairB : ∀ a, normB (phiB a) = doubleA a)
    (pairCA : ∀ a, normC (phiC a) = doubleA a)
    (pairCC : ∀ y, phiC (normC y) = doubleC y) :
    ∀ x, phiC (normB (phiB (normOld x))) = doubleC (phiC (normOld x)) := by
  intro x
  rw [pairB, ← pairCA (normOld x), pairCC]

end ChainKernels223
