import Std
import Init.Grind.Ring.Basic

namespace JointResidual

/-- Any five-block target relation places the first-three-block sum at
the target residual after subtracting the last two blocks. -/
theorem first_three_is_target_residual {G : Type} [AddCommGroup G]
    (z e₃ e₄ target : G)
    (relation : (z + e₃) + e₄ = target) :
    z = (target - e₄) - e₃ := by
  have first_four : z + e₃ = target - e₄ := by
    calc
      z + e₃ = ((z + e₃) + e₄) - e₄ := AddCommGroup.add_sub_cancel.symm
      _ = target - e₄ := by rw [relation]
  calc
    z = (z + e₃) - e₃ := AddCommGroup.add_sub_cancel.symm
    _ = (target - e₄) - e₃ := by rw [first_four]

/-- Applying any coordinate map and then any finite prefix map preserves
the necessary target-residual equality. -/
theorem prefix_is_necessary {G Coord Prefix : Type} [AddCommGroup G]
    (coordinate : G → Coord) (prefix : Coord → Prefix)
    (z e₃ e₄ target : G)
    (relation : (z + e₃) + e₄ = target) :
    prefix (coordinate z) =
      prefix (coordinate ((target - e₄) - e₃)) := by
  rw [first_three_is_target_residual z e₃ e₄ target relation]

#print axioms JointResidual.first_three_is_target_residual
#print axioms JointResidual.prefix_is_necessary

end JointResidual
