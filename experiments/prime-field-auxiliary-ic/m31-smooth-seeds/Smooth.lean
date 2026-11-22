import Mathlib

namespace M31Smooth
abbrev M31 := ZMod 2147483647

theorem powerOfTwoSquare (k : ℕ) : IsSquare ((2 : M31)^k) := by
  have h : (2 : M31) = 65536 * 65536 := by native_decide
  exact ⟨(65536 : M31)^k, by rw [h, mul_pow]⟩

/-- Compare the measured mean per distinct smooth-seeded fiber to the
independently enumerated whole-population mean. -/
theorem gapGivenCounts :
    0 < (268414441/16777216 : ℚ) - 3957125/247386 ∧
    (268414441/16777216 : ℚ) - 3957125/247386 < 3/1000 := by norm_num
end M31Smooth
