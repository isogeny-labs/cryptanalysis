module

public import Mathlib.Algebra.Field.Basic

/-! A nonscalar repeated-root Frobenius action on a two-dimensional
11-torsion model has exactly one eigenline. The bridge from an actual
elliptic curve to this normal form remains external. -/
namespace JordanLine

public theorem eigenvector_second_coordinate_zero {F : Type*} [Field F]
    (lam c a b : F)
    (h : (lam * a + b, lam * b) = (c * a, c * b)) : b = 0 := by
  have hfirst : lam * a + b = c * a := congrArg Prod.fst h
  have hsecond : lam * b = c * b := congrArg Prod.snd h
  by_cases hb : b = 0
  · exact hb
  · have hc : lam = c := mul_right_cancel₀ hb hsecond
    rw [hc] at hfirst
    have hsub := congrArg (fun z : F => z - c * a) hfirst
    simpa [add_comm, add_left_comm, add_assoc] using hsub

public theorem horizontal_line_is_eigenline {F : Type*} [Field F] (lam a : F) :
    (lam * a + (0 : F), lam * (0 : F)) =
      (lam * a, lam * (0 : F)) := by
  simp

end JordanLine

#print axioms JordanLine.eigenvector_second_coordinate_zero
#print axioms JordanLine.horizontal_line_is_eigenline
