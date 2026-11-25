import Mathlib

namespace SignTrace
open Matrix

variable {n m : Type*} [Fintype n] [Fintype m] [DecidableEq n]

theorem energy (H : Matrix n m ℤ) (B D : Matrix n n ℤ)
    (symm : B.transpose = B) (gram : H * H.transpose = B + D) :
    let R := (B - (7 : ℤ) • 1) * H
    (R * R.transpose).trace =
      ((B * B) * B).trace + ((B * B) * D).trace -
      14 * ((B * B).trace + (B * D).trace) + 49 * (B.trace + D.trace) := by
  let E := B - (7 : ℤ) • (1 : Matrix n n ℤ)
  have he : E.transpose = E := by simp [E, symm]
  change ((E * H) * (E * H).transpose).trace = _
  rw [transpose_mul, he, ← Matrix.mul_assoc, Matrix.mul_assoc E H, gram, trace_mul_comm,
      ← Matrix.mul_assoc]
  have square : E * E = B * B - (14 : ℤ) • B + (49 : ℤ) • 1 := by
    simp only [E, sub_mul, mul_sub, Matrix.mul_smul, Matrix.smul_mul, Matrix.one_mul, Matrix.mul_one, smul_smul]
    module
  rw [square]
  simp only [add_mul, sub_mul, Matrix.smul_mul, one_mul, mul_add, trace_add,
    trace_sub, trace_smul, smul_eq_mul]
  ring

/-- Every odd entry contributes at least one unit to the integer square energy. -/
theorem parity_floor {ι : Type*} (s : Finset ι) (v : ι → ℤ) :
    ((s.filter (fun i => v i % 2 = 1)).card : ℤ) ≤ ∑ i ∈ s, (v i)^2 := by
  classical
  rw [Finset.card_filter]
  push_cast
  apply Finset.sum_le_sum
  intro i _
  split_ifs with h
  · have hn : v i ≠ 0 := by omega
    have hp := sq_pos_of_ne_zero hn
    omega
  · exact sq_nonneg _

#print axioms energy
#print axioms parity_floor
end SignTrace
