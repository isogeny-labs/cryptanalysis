import Std

namespace PublicArchive

variable {V : Type}

def correction [DecidableEq V] (predicted actual : V) : Option V :=
  if predicted = actual then none else some actual

theorem decode_exact [DecidableEq V] (predicted actual : V) :
    (correction predicted actual).getD predicted = actual := by
  by_cases h : predicted = actual <;> simp [correction, h]

/-- With a fixed default, every lossless decoder of this form must store
an override at each mismatch. -/
theorem override_required (predicted actual : V) (slot : Option V)
    (different : predicted ≠ actual) (exactValue : slot.getD predicted = actual) :
    slot = some actual := by
  cases slot with
  | none => exact False.elim (different exactValue)
  | some v => exact congrArg some exactValue

end PublicArchive
