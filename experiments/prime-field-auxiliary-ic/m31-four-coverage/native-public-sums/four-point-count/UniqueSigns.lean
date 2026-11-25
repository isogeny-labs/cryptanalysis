import Mathlib.Tactic

namespace M31FourSigns

def orient {F : Type*} [Neg F] (flip : Bool) (x : F) : F :=
  if flip then -x else x

/-- Orient the four classes so their sum vanishes. Normalize a second
choice of signs by keeping the first sign positive. No other choice works
when the entries are nonzero, their sign classes distinct, and 2 nonzero. -/
theorem unique_normalized {F : Type*} [Field F] (h2 : (2 : F) ≠ 0)
    {a b c d : F} (ha : a ≠ 0) (hb : b ≠ 0) (hc : c ≠ 0) (hd : d ≠ 0)
    (hbc : b + c ≠ 0) (hbd : b + d ≠ 0) (hcd : c + d ≠ 0)
    (h : a+b+c+d = 0) (i j k : Bool)
    (other : a + orient i b + orient j c + orient k d = 0) :
    i = false ∧ j = false ∧ k = false := by
  cases i <;> cases j <;> cases k <;> simp only [orient, Bool.false_eq_true,
    if_false, if_true] at other
  · exact ⟨rfl, rfl, rfl⟩
  · exact False.elim (mul_ne_zero h2 hd (by linear_combination h - other))
  · exact False.elim (mul_ne_zero h2 hc (by linear_combination h - other))
  · exact False.elim (mul_ne_zero h2 hcd (by linear_combination h - other))
  · exact False.elim (mul_ne_zero h2 hb (by linear_combination h - other))
  · exact False.elim (mul_ne_zero h2 hbd (by linear_combination h - other))
  · exact False.elim (mul_ne_zero h2 hbc (by linear_combination h - other))
  · exact False.elim (mul_ne_zero h2 ha (by linear_combination h + other))

#print axioms unique_normalized
end M31FourSigns
