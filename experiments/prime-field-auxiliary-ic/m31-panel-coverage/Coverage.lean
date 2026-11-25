import Mathlib.Data.Finset.Sym
import Mathlib.Tactic

namespace PanelCoverage

def pairSum {G : Type*} [AddCommGroup G] : Sym2 G → G :=
  Sym2.lift ⟨(· + ·), add_comm⟩

theorem sum_bound {G : Type*} [AddCommGroup G] [DecidableEq G] (s : Finset G) :
    (s.sym2.image pairSum).card ≤ (s.card + 1).choose 2 := by
  exact (Finset.card_image_le).trans_eq (Finset.card_sym2 s)

-- Union bound for 16 queries and two bases, expressed as integer counts
-- per uniform finite target. Includes pairs summing to infinity.
theorem miss_floor :
    32 * (4050 + 1).choose 2 * 1000 < 123 * (2147505293 - 1) := by
  decide +kernel

end PanelCoverage
