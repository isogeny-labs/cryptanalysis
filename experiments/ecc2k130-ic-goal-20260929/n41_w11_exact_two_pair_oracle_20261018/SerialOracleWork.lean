import Std

namespace SerialOracleWork

/-- Candidate checks from independent complete misses of fixed width. -/
def missScan : Nat → Nat → Nat
  | 0, _ => 0
  | n + 1, width => width + missScan n width

theorem missScan_count (n width : Nat) :
    missScan n width = n * width := by
  induction n with
  | zero => simp [missScan]
  | succ n ih =>
      simp [missScan, ih, Nat.succ_mul, Nat.add_comm]

/-- The exact candidate count for separately applying the implicit oracle
to the frozen native residual sequence. -/
theorem frozen_serial_candidate_count :
    missScan 394049 1124 + 279 = 442911355 := by
  rw [missScan_count]

#print axioms SerialOracleWork.missScan_count
#print axioms SerialOracleWork.frozen_serial_candidate_count

end SerialOracleWork
