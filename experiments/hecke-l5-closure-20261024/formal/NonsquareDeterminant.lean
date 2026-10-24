module

public import Init

/-! Arithmetic obstruction for scalar Frobenius on 5-torsion at p = 20023. -/
namespace NonsquareDeterminant

public theorem three_not_square_mod_five :
    ∀ s : Fin 5, (s.val * s.val) % 5 ≠ 3 := by
  decide

public theorem determinant_three_excludes_scalar
    (det : Nat) (scalar : Fin 5)
    (hdet : det % 5 = 3)
    (hscalar : det % 5 = (scalar.val * scalar.val) % 5) : False := by
  exact three_not_square_mod_five scalar (hscalar ▸ hdet)

end NonsquareDeterminant

#print axioms NonsquareDeterminant.three_not_square_mod_five
#print axioms NonsquareDeterminant.determinant_three_excludes_scalar
