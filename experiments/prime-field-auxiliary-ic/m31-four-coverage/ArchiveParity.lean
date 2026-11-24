import Mathlib.Tactic

namespace M31ArchiveParity

-- Times are in nanoseconds. The assumptions round the IC total down,
-- and round both the observed rho total and removable loop time up.
theorem seed_zero (total loop rho futureLoop : ℚ)
    (ht : 9685107568 ≤ total) (hl : loop ≤ 9676515000)
    (hr : rho ≤ 7091596) (hf : 0 ≤ futureLoop) :
    rho + 1500000 < total - loop + futureLoop := by linarith

private theorem insufficient (total loop rho speed : ℚ) (k : ℕ)
    (hk : 1 ≤ (k : ℚ)) (hs : 0 < speed) (cap : speed ≤ k) (hl : 0 ≤ loop)
    (gap : (k : ℚ) * (total - rho) > (k-1 : ℚ) * loop) :
    rho < total - loop + loop / speed := by
  have pos : (0 : ℚ) < k := by linarith
  have fraction := div_le_div_of_nonneg_left hl hs cap
  have base : rho - (total-loop) < loop / k := by
    apply (lt_div_iff₀ pos).2
    linarith only [show (k : ℚ)*(total-rho) > ((k : ℚ)-1)*loop from gap]
  linarith

theorem seed_one (total loop rho speed : ℚ)
    (ht : 5167235504 ≤ total) (hl : loop ≤ 5160085000)
    (hr : rho ≤ 21868217) (nonneg : 0 ≤ loop) (hs : 0 < speed) (cap : speed ≤ 350) :
    rho < total - loop + loop / speed := by
  apply insufficient total loop rho speed 350 (by norm_num) hs cap nonneg
  norm_num
  linarith

theorem seed_two (total loop rho speed : ℚ)
    (ht : 11667566436 ≤ total) (hl : loop ≤ 11662650000)
    (hr : rho ≤ 18318453) (nonneg : 0 ≤ loop) (hs : 0 < speed) (cap : speed ≤ 870) :
    rho < total - loop + loop / speed := by
  apply insufficient total loop rho speed 870 (by norm_num) hs cap nonneg
  norm_num
  linarith

end M31ArchiveParity
