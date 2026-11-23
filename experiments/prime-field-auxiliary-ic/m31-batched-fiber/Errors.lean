import Std.Tactic.BVDecide

namespace M31BatchedFiber
abbrev W := BitVec 32

theorem word_clear (badEncoding equalSiblings : Bool) (product expected : W) :
    ((if badEncoding then (1 : W) else 0) ||| (if equalSiblings then 1 else 0) |||
      (product ^^^ expected)) = 0 ↔
      badEncoding = false ∧ equalSiblings = false ∧ product = expected := by bv_decide

theorem row_clear (flags : List W) (initial : W) :
    flags.foldl (· ||| ·) initial = 0 ↔ initial = 0 ∧ ∀ x ∈ flags, x = 0 := by
  induction flags generalizing initial with
  | nil => simp
  | cons x xs ih =>
    rw [List.foldl_cons, ih, show initial ||| x = 0 ↔ initial = 0 ∧ x = 0 by bv_decide]
    simp [and_assoc]

end M31BatchedFiber
