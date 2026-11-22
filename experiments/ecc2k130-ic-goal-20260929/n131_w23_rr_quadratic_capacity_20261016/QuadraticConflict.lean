import Std

namespace QuadraticConflict

/-- A Boolean-linear evaluation commutes with the running XOR of rows. -/
theorem eval_foldl_xor {V : Type} (xor : V → V → V) (score : V → Bool)
    (hlinear : ∀ a b, score (xor a b) = Bool.xor (score a) (score b))
    (rows : List V) (start : V) :
    score (rows.foldl xor start) =
      rows.foldl (fun bit row => Bool.xor bit (score row)) (score start) := by
  induction rows generalizing start with
  | nil => rfl
  | cons row tail ih =>
      simpa only [List.foldl_cons, hlinear] using ih (xor start row)

/-- An XOR dependency of rows with odd evaluated parity contradicts a
Boolean-linear score that vanishes on zero. -/
theorem no_score_for_odd_zero_dependency {V : Type}
    (zero : V) (xor : V → V → V) (score : V → Bool)
    (hzero : score zero = false)
    (hlinear : ∀ a b, score (xor a b) = Bool.xor (score a) (score b))
    (rows : List V)
    (hdependency : rows.foldl xor zero = zero)
    (hodd : rows.foldl (fun bit row => Bool.xor bit (score row)) false = true) :
    False := by
  have h := eval_foldl_xor xor score hlinear rows zero
  simp [hdependency, hzero, hodd] at h

#print axioms QuadraticConflict.eval_foldl_xor
#print axioms QuadraticConflict.no_score_for_odd_zero_dependency

end QuadraticConflict
