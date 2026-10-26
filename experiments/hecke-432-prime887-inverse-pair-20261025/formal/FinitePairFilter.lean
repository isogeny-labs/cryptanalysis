import Mathlib.Data.Finset.Card

namespace P887FinitePairFilter

variable {C E : Type*} [DecidableEq (C × E)]

/-- The independently counted 864 valid resolvent pairs equal the 864
corrected source pairs once source containment is established. -/
theorem source_eq_valid
    (source valid : Finset (C × E))
    (hsource : source.card = 864)
    (hvalid : valid.card = 864)
    (hsub : source ⊆ valid) : source = valid := by
  exact Finset.eq_of_subset_of_card_le hsub (hvalid.trans hsource.symm).le

/-- Eight exceptional rational resolvent pairs complete the 872-pair screen. -/
theorem resolvent_partition_card
    (valid exceptional : Finset (C × E))
    (hvalid : valid.card = 864)
    (hexceptional : exceptional.card = 8)
    (hdisjoint : Disjoint valid exceptional) :
    (valid ∪ exceptional).card = 872 := by
  rw [Finset.card_union_of_disjoint hdisjoint, hvalid, hexceptional]

#print axioms source_eq_valid
#print axioms resolvent_partition_card

end P887FinitePairFilter
