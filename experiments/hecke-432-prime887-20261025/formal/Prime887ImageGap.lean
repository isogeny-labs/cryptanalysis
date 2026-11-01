import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Image
import Mathlib.Tactic.Linarith

namespace Prime887ImageGap

theorem exactly_778_missing
    {Source Target : Type*} [Fintype Source] [Fintype Target] [DecidableEq Target]
    (map : Source → Target)
    (himage : (Finset.univ.image map).card = 110)
    (htarget : Fintype.card Target = 888) :
    Fintype.card Target - (Finset.univ.image map).card = 778 := by
  omega

theorem fiber_distribution_total : 6*1 + 7*2 + 8*102 + 9*4 = 872 := by
  norm_num

#print axioms exactly_778_missing
#print axioms fiber_distribution_total

end Prime887ImageGap
