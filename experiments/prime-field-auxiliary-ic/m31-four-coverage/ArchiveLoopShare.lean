import Mathlib.Tactic

namespace M31.ArchiveLoopShare

/-- Upper bounds on cold duration and lower bounds on loop duration, in
nanoseconds, from field31_s5_base0/v2_batch_seed{0,1,2}.audited.json at
9a1d8a6cf. Cold times are rounded up. Each printed loop time is reduced
by 50 microseconds to cover rounding at the least precise printed digit. -/
def bounds : List (ℚ × ℚ) :=
  [(9685107569,9676460000), (5167235505,5160030000), (11667566437,11662550000)]

/-- Even eliminating every cost outside the archived loop, including process
overhead, is insufficient to produce a 1.0014-fold speedup on any seed. -/
theorem outside_loop_cap (cold revised : ℚ) (row : ℚ × ℚ)
    (hr : row ∈ bounds) (hc : cold ≤ row.1) (hl : row.2 ≤ revised) :
    cold / revised < 10014 / 10000 := by
  have h : ∀ r ∈ bounds, 0 < r.2 ∧ r.1 < (10014 / 10000 : ℚ) * r.2 := by
    simp [bounds]
    norm_num
  obtain ⟨hp, hmax⟩ := h row hr
  apply (div_lt_iff₀ (lt_of_lt_of_le hp hl)).2
  linarith

end M31.ArchiveLoopShare
