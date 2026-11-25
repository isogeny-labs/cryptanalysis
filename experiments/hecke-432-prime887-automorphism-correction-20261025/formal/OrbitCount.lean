import Mathlib.Data.Finset.Card
import Mathlib.Tactic.NormNum

namespace P887OrbitCount

variable {α : Type*} [DecidableEq α]

/-- Four base-model orbits and four distinct twist-model orbits give eight
special source points. The geometric orbit and disjointness hypotheses are
checked by the kernel-polynomial replay. -/
theorem special_source_card
    (base twist : Finset α)
    (hbase : base.card = 4) (htwist : twist.card = 4)
    (hdisjoint : Disjoint base twist) :
    (base ∪ twist).card = 8 := by
  rw [Finset.card_union_of_disjoint hdisjoint, hbase, htwist]

/-- The corrected noncuspidal source partition has 872 points. -/
theorem corrected_source_card
    (generic j0 base twist : Finset α)
    (hgeneric : generic.card = 856) (hj0 : j0.card = 8)
    (hbase : base.card = 4) (htwist : twist.card = 4)
    (hgj : Disjoint generic j0)
    (hgb : Disjoint generic base) (hgt : Disjoint generic twist)
    (hjb : Disjoint j0 base) (hjt : Disjoint j0 twist)
    (hbt : Disjoint base twist) :
    ((generic ∪ j0) ∪ (base ∪ twist)).card = 872 := by
  have hspecial : (base ∪ twist).card = 8 :=
    special_source_card base twist hbase htwist hbt
  have hg : Disjoint generic (base ∪ twist) :=
    Finset.disjoint_union_right.mpr ⟨hgb, hgt⟩
  have hj : Disjoint j0 (base ∪ twist) :=
    Finset.disjoint_union_right.mpr ⟨hjb, hjt⟩
  have hall : Disjoint (generic ∪ j0) (base ∪ twist) :=
    Finset.disjoint_union_left.mpr ⟨hg, hj⟩
  rw [Finset.card_union_of_disjoint hall,
      Finset.card_union_of_disjoint hgj,
      hgeneric, hj0, hspecial]

#print axioms special_source_card
#print axioms corrected_source_card

end P887OrbitCount
