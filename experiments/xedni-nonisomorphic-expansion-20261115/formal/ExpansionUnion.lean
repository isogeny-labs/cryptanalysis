import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.Interval
import Mathlib.Tactic

namespace XedniNonisomorphicExpansion

private def image (u : ZMod 331) : Finset (ZMod 331) :=
  (Finset.Icc (-4 : ℤ) 4).image (fun k : ℤ => (k : ZMod 331) * u)

private theorem pair_card_of_sizes {α : Type*} [DecidableEq α]
    (S T : Finset α) (hS : S.card = 9) (hT : T.card = 9)
    (hI : (S ∩ T).card = 1) :
    ((S.product S) ∪ (T.product T)).card = 161 := by
  have hinter : (S.product S) ∩ (T.product T) =
      (S ∩ T).product (S ∩ T) := by
    ext pair
    simp [and_left_comm, and_assoc]
  have hSI : (S.product S).card = 81 := by
    simp [Finset.card_product, hS]
  have hTI : (T.product T).card = 81 := by
    simp [Finset.card_product, hT]
  have hII : ((S.product S) ∩ (T.product T)).card = 1 := by
    rw [hinter]
    simp [Finset.card_product, hI]
  have hsum := Finset.card_union_add_card_inter (S.product S) (T.product T)
  rw [hSI, hTI, hII] at hsum
  omega

/-- The two radius-four generator images at subgroup order 331 contain 161 ordered pairs. -/
theorem pair_union_card_331 :
    (((image 1).product (image 1)) ∪ ((image 5).product (image 5))).card = 161 := by
  apply pair_card_of_sizes
  · decide
  · decide
  · decide

#print axioms pair_union_card_331

end XedniNonisomorphicExpansion
