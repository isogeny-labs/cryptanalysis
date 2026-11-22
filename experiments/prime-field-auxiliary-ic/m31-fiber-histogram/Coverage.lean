import Mathlib

namespace M31FiberHistogram
/-- Odd residues modulo 2^26, up to sign, have unique odd representatives
2*i+1 indexed from zero to 2^24-1. -/
theorem covers (r : ℕ) (hr : r < 2^26) (ho : r%2=1) :
    ∃! i : ℕ, i < 2^24 ∧ (2*i+1=r ∨ 2*i+1+r=2^26) := by
  by_cases low : r < 2^25
  · use r/2
    constructor
    · omega
    · intro j hj
      omega
  · use (2^26-r)/2
    constructor
    · omega
    · intro j hj
      omega
end M31FiberHistogram
