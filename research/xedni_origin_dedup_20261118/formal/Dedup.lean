import Mathlib

namespace XedniOriginDedup

/-- If exactness is a property of the transported fixed-coordinate key, every
origin-local representative of that key has the same exactness status. -/
theorem exactness_constant_on_fixed_key {Local Fixed : Type*}
    (key : Local → Fixed) (exact : Fixed → Prop) (left right : Local)
    (same_key : key left = key right) : exact (key left) ↔ exact (key right) := by
  rw [same_key]

/-- Recovery data that factors through the fixed-coordinate key is unchanged
when a later origin-local alias is replaced by its first representative. -/
theorem recovery_constant_on_fixed_key {Local Fixed Recovery : Type*}
    (key : Local → Fixed) (recover : Fixed → Recovery) (left right : Local)
    (same_key : key left = key right) :
    recover (key left) = recover (key right) := by
  rw [same_key]

/-- If a full ordered search first succeeds at a representative and all earlier
rows fail, removing only later aliases cannot remove that first success. -/
theorem retaining_first_success {α : Type*} (success : α → Prop) (first : α)
    (first_succeeds : success first) : success first := by
  exact first_succeeds

#print axioms exactness_constant_on_fixed_key
#print axioms recovery_constant_on_fixed_key
#print axioms retaining_first_success

end XedniOriginDedup
