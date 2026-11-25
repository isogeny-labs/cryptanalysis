import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

/-! The structural consequence of the enumerated image and target cardinalities. -/

namespace ExactImageGap

theorem exactly_895_missing
    {Source Target : Type*} [Fintype Source] [Fintype Target] [DecidableEq Target]
    (map : Source → Target)
    (himage : (Finset.univ.image map).card = 36)
    (htarget : Fintype.card Target = 931) :
    Fintype.card Target - (Finset.univ.image map).card = 895 := by
  omega

#print axioms exactly_895_missing

end ExactImageGap
