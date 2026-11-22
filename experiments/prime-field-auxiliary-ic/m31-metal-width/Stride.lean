import Mathlib

namespace MetalWidth
theorem coverage (n w stride k : ℕ) (hk : k < n) (hs : 0 < stride)
    (hcap : n ≤ w * stride) :
    k % stride < stride ∧ k / stride < w ∧
    k % stride + (k / stride) * stride = k := by
  refine ⟨Nat.mod_lt _ hs, (Nat.div_lt_iff_lt_mul hs).mpr (lt_of_lt_of_le hk hcap), ?_⟩
  rw [Nat.mul_comm, Nat.mod_add_div]

theorem addressUnique (s i j : ℕ) (hi : i < s) :
    (i+j*s)%s = i ∧ (i+j*s)/s = j := by
  have hs : 0 < s := by omega
  simp [Nat.add_mul_div_right, Nat.mod_eq_of_lt hi, Nat.div_eq_of_lt hi, hs]
end MetalWidth
