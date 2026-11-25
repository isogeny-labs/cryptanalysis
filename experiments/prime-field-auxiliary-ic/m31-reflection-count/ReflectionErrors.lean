import Lean

namespace ReflectionErrors

/-- One shared bit makes exactly one error on a pair of opposite labels. -/
theorem mixedPair (a b prediction : Bool) (mixed : a ≠ b) :
    (if a = prediction then 0 else 1 : Nat) +
    (if b = prediction then 0 else 1 : Nat) = 1 := by
  revert mixed
  cases a <;> cases b <;> cases prediction <;> decide

/-- Ordered equal pairs contribute +1 to the character sum and ordered
unequal pairs contribute -1. Each mixed orbit supplies two unequal inputs. -/
theorem count (equal mixed : Int)
    (size : equal + 2*mixed = 2147483647)
    (correlation : equal - 2*mixed = 105943) :
    mixed = 536844426 := by omega

end ReflectionErrors
