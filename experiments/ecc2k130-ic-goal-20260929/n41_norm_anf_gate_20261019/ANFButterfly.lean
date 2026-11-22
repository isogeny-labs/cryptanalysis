import Std

namespace ANFButterfly

/-- One Boolean zeta/ANF butterfly keeps the first value and XORs it into
    the second.  Applying the same butterfly twice restores both values. -/
def butterfly (a b : Bool) : Bool × Bool := (a, Bool.xor a b)

theorem butterfly_involutive (a b : Bool) :
    butterfly (butterfly a b).1 (butterfly a b).2 = (a, b) := by
  cases a <;> cases b <;> decide

#print axioms butterfly_involutive
end ANFButterfly
