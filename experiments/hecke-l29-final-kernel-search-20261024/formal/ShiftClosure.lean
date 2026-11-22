import Mathlib.Algebra.Group.Hom.Defs
import Mathlib.Algebra.Group.Basic
import Mathlib.Algebra.Field.Defs

/-!
An independently checked generator shift transports a known group log to a
previously undetermined one.  The concrete point equalities and matrix ranks
for the p=20023 instance are checked by the finite experiment.
-/

namespace ShiftClosure

theorem log_from_generator_shift {G H : Type*} [AddCommGroup G] [AddCommGroup H]
    (log : G →+ H) (unknown generator known : G) (steps : ℕ)
    (hshift : known = unknown + steps • generator) :
    log unknown = log known - steps • log generator := by
  rw [hshift, map_add, map_nsmul]
  simp

theorem shift_row_separates_residual {K : Type*} [Field K]
    (unknown anchor known step : K)
    (hunknown : unknown ≠ 0) (hanchor : anchor = 0) (hknown : known = 0) :
    unknown + step * anchor - known ≠ 0 := by
  rw [hanchor, hknown, mul_zero, add_zero, sub_zero]
  exact hunknown

#print axioms log_from_generator_shift
#print axioms shift_row_separates_residual

end ShiftClosure
