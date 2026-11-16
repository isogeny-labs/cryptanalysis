import Mathlib.Tactic

namespace XedniRankOneCoordinate

/-- For two centered lifts in one cyclic rational generator, the full
radius-`L` sum box has minimum slope `m(q-1)`. That slope cannot satisfy
the rank-one count threshold while the reduced witness box is below `q`. -/
theorem no_rank_gap_at_centered_slope
    (q m L c : ℕ) (hq : 3 ≤ q) (hm : 1 ≤ m)
    (hcoord : m * (q - 1) ≤ c)
    (hlarge : 2 * c + 1 < L)
    (hbudget : (4 * L + 1) ^ 2 - 1 < q) : False := by
  have hq1 : 1 ≤ q := by omega
  have hqsub : q - 1 + 1 = q := Nat.sub_add_cancel hq1
  have hc : q - 1 ≤ c := by
    calc
      q - 1 = 1 * (q - 1) := by omega
      _ ≤ m * (q - 1) := Nat.mul_le_mul_right (q - 1) hm
      _ ≤ c := hcoord
  have hL : 1 ≤ L := by omega
  have hpow : 1 ≤ (4 * L + 1) ^ 2 := by
    have hpos : 0 < (4 * L + 1) ^ 2 := pow_pos (by omega) 2
    omega
  have hsub : ((4 * L + 1) ^ 2 - 1) + 1 =
      (4 * L + 1) ^ 2 := Nat.sub_add_cancel hpow
  have hbox : 4 * L < (4 * L + 1) ^ 2 - 1 := by
    nlinarith
  have hqgt : 4 * L < q := lt_trans hbox hbudget
  omega

#print axioms no_rank_gap_at_centered_slope

end XedniRankOneCoordinate
