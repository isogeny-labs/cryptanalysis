import Mathlib.Algebra.Field.Basic

namespace BatchInverse

variable {F : Type*} [Field F] [DecidableEq F]

def factor (x : F) := if x = 0 then 1 else x

/-- Walk to the final product, invert once, then recover the input inverses
and the inverse of the incoming product on the way back. -/
def recover (p : F) : List F → F × List F
  | [] => (p⁻¹, [])
  | x :: xs =>
    let (r, rest) := recover (p * factor x) xs
    (r * factor x, (if x = 0 then 0 else r * p) :: rest)

theorem recover_correct (xs : List F) (p : F) (hp : p ≠ 0) :
    recover p xs = (p⁻¹, xs.map Inv.inv) := by
  induction xs generalizing p with
  | nil => rfl
  | cons x xs ih =>
    have hf : factor x ≠ 0 := by by_cases hx : x = 0 <;> simp [factor,hx]
    rw [recover, ih _ (mul_ne_zero hp hf)]
    by_cases hx : x = 0
    · simp [factor,hx]
    · simp [factor,hx,hp,mul_inv_rev, mul_comm]

omit [DecidableEq F] in
/-- A product inverse can be passed independently down both subtrees. -/
theorem distribute (a b : F) (ha : a ≠ 0) (hb : b ≠ 0) :
    ((a*b)⁻¹*b, (a*b)⁻¹*a) = (a⁻¹,b⁻¹) := by
  simp [ha,hb,mul_inv_rev,mul_comm]

#print axioms recover_correct
#print axioms distribute
end BatchInverse
