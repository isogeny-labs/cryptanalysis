import Std.Tactic
set_option autoImplicit false
namespace NonsquareResidues

/-- Every canonical residue modulo223 fails to square to either observed
discriminant. This is exact residue arithmetic, not a field-extension theorem.
The proof uses kernel reduction, not native_decide or an execution oracle. -/
theorem base_square_nonroots :
    ∀ x : Fin 223, (x.val * x.val) % 223 ≠ 12 ∧
      (x.val * x.val) % 223 ≠ 24 := by
  decide

end NonsquareResidues
