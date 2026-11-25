import Std

namespace M31.TranslateCount

/-- Translation of a complete finite group enumeration permutes it.
Deleting a forbidden partner set therefore subtracts exactly the hits
in its translate, even when the permitted rows are dependent. -/
theorem translated_partition {α : Type} (test : α → Bool) (translate : α → α)
    (allowed forbidden : List α)
    (perm : ((allowed ++ forbidden).map translate).Perm (allowed ++ forbidden)) :
    allowed.countP (test ∘ translate) + forbidden.countP (test ∘ translate) =
      (allowed ++ forbidden).countP test := by
  have h := perm.countP_eq test
  rwa [List.countP_map, List.countP_append] at h

/-- Summing the partition identity across an arbitrary fixed basis. -/
theorem basis_partition {α : Type} (test : α → Bool) (shift : α → α → α)
    (allowed forbidden basis : List α)
    (perm : ∀ a, ((allowed ++ forbidden).map (shift a)).Perm (allowed ++ forbidden)) :
    (basis.map fun a => allowed.countP (test ∘ shift a)).sum +
    (basis.map fun a => forbidden.countP (test ∘ shift a)).sum =
    basis.length * (allowed ++ forbidden).countP test := by
  induction basis with
  | nil => simp
  | cons a xs ih =>
    have row := translated_partition test (shift a) allowed forbidden (perm a)
    simp only [List.map_cons, List.sum_cons, List.length_cons, Nat.succ_mul]
    omega

end M31.TranslateCount
