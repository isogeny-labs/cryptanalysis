import Mathlib.Tactic

namespace M31ExactBucket

inductive Cell where
  | empty
  | one (key : Nat)
  | multiple

def insert (s : Cell) (x : Nat) : Cell :=
  match s with
  | .empty => .one x
  | .one k => if x = k then .one k else .multiple
  | .multiple => .multiple

def accepts (s : Cell) (q : Nat) (fallback : Prop) : Prop :=
  match s with
  | .empty => False
  | .one k => q = k
  | .multiple => fallback

/-- For any hash, exact fallback membership suffices even if every key collides. -/
theorem exact (hash : Nat → Nat) (keys : List Nat) (q : Nat) :
    accepts ((keys.filter (fun x => hash x == hash q)).foldr (fun x s => insert s x) .empty)
      q (q ∈ keys) ↔ q ∈ keys := by
  induction keys with
  | nil => simp [accepts]
  | cons x xs ih =>
    by_cases h : hash x = hash q
    · simp only [List.filter_cons, beq_iff_eq.mpr h, ite_true, List.foldr_cons, List.mem_cons]
      generalize hs : List.foldr _ _ _ = s at ih ⊢
      cases s <;> simp_all [insert, accepts]
      split_ifs <;> simp_all
    · have ne : q ≠ x := fun e => h (e ▸ rfl)
      simpa [h, ne] using ih

end M31ExactBucket
