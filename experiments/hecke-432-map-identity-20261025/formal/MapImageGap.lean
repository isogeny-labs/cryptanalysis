import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

namespace MapImageGap

theorem exactly_894_missing
    {Source Target : Type*} [Fintype Source] [Fintype Target] [DecidableEq Target]
    (map : Source → Target)
    (himage : (Finset.univ.image map).card = 37)
    (htarget : Fintype.card Target = 931) :
    Fintype.card Target - (Finset.univ.image map).card = 894 := by
  omega

#print axioms exactly_894_missing

end MapImageGap
