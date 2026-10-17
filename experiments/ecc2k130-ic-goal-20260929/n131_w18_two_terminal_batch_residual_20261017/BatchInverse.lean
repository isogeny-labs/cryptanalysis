import Std
import Init.Grind.Ring.Basic

open Lean.Grind

namespace BatchInverse

/-- The reverse pass of batch inversion consumes an inverse of the prefix
including `value`. Multiplying by the preceding prefix yields an inverse of
`value`; multiplying by `value` yields the inverse needed for the preceding
prefix. -/
theorem reverse_step {F : Type} [Field F]
    (pref value inverseTotal : F)
    (h : inverseTotal * (pref * value) = 1) :
    (inverseTotal * pref) * value = 1 ∧
    (inverseTotal * value) * pref = 1 := by
  constructor <;> grind

#print axioms reverse_step

end BatchInverse
