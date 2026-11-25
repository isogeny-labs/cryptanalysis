import Std

namespace TraceRows

def dot : List Bool → List Bool → Bool
  | x :: xs, y :: ys => Bool.xor (x && y) (dot xs ys)
  | _, _ => false

def bilinear : List Bool → List (List Bool) → List Bool → Bool
  | a :: as, row :: rows, beta => Bool.xor (a && dot row beta) (bilinear as rows beta)
  | _, _, _ => false

/-- A row whose projected coefficients all vanish contributes zero for
every value of the right block. -/
theorem dot_zero_row (width : Nat) (beta : List Bool) :
    dot (List.replicate width false) beta = false := by
  induction width generalizing beta with
  | zero => simp [dot]
  | succ n ih =>
      cases beta with
      | nil => simp [dot]
      | cons b bs =>
          rw [List.replicate_succ]
          simp [dot, ih]

/-- Forcing a prefix of cross rows to zero removes those left variables
from the bilinear part of every trace cut. -/
theorem forced_zero_prefix
    (firstAlpha lastAlpha : List Bool) (lastRows : List (List Bool))
    (beta : List Bool) (width : Nat) :
    bilinear (firstAlpha ++ lastAlpha)
      (List.replicate firstAlpha.length (List.replicate width false) ++ lastRows) beta
      = bilinear lastAlpha lastRows beta := by
  induction firstAlpha with
  | nil => simp
  | cons a rest ih =>
      simp only [List.length_cons, List.replicate_succ, List.cons_append]
      simp [bilinear, dot_zero_row, ih]

#print axioms TraceRows.dot_zero_row
#print axioms TraceRows.forced_zero_prefix

end TraceRows
