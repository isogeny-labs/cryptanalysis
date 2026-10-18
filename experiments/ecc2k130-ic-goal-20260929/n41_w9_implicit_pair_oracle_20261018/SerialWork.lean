import Std

namespace W9SerialOracle

/-- First-slot candidate checks on complete misses at a fixed source width. -/
def missScan : Nat → Nat → Nat
  | 0, _ => 0
  | n + 1, width => width + missScan n width

theorem missScan_count (n width : Nat) :
    missScan n width = n * width := by
  induction n with
  | zero => simp [missScan]
  | succ n ih =>
      simp [missScan, ih, Nat.succ_mul, Nat.add_comm]

/-- The minimum checks for the complete-miss calls in the frozen join order,
    given at most two hash matches among its 83,612,805 queries. -/
theorem frozen_complete_miss_checks :
    missScan 83612803 284 = 23746036052 := by
  rw [missScan_count]

#print axioms missScan_count
#print axioms frozen_complete_miss_checks

end W9SerialOracle
