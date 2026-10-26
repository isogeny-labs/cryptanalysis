import Mathlib.Data.Finset.Card

namespace InversePair

variable {C E : Type*}

/-- A complete 1800-element root screen equals the 1800 recorded source pairs
once every source pair passes the resolvent. -/
theorem source_pairs_eq_resolvent_pairs
    (source roots : Finset (C × E))
    (hsource : source.card = 1800)
    (hroots : roots.card = 1800)
    (hsource_valid : source ⊆ roots) :
    source = roots := by
  exact Finset.eq_of_subset_of_card_le hsource_valid (hroots.trans hsource.symm).le

#print axioms source_pairs_eq_resolvent_pairs

end InversePair
