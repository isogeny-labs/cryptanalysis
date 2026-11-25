import Mathlib

/-! The E2 twist over M31 has trace 22553. Its extension counts follow the
standard elliptic Frobenius trace recurrence. Modulo the E2 subgroup order
the characteristic roots are -1 and -p. -/
namespace M31E2Extension

abbrev R := ZMod 2147506201
abbrev p : R := 2147483647

/-- Frobenius power sums reduced modulo the target order. -/
def trace : ℕ → R
  | 0 => 2
  | 1 => 22553
  | d+2 => 22553 * trace (d+1) - p * trace d

theorem trace_eq (d : ℕ) : trace d = (-1 : R)^d + (-p)^d := by
  induction d using Nat.twoStepInduction with
  | zero => decide
  | one => decide
  | more d h0 h1 =>
    rw [trace, h1, h0]
    have h : (22553 : R) = -1-p := by decide
    rw [h, pow_succ (-1 : R) (d+1), pow_succ (-p) (d+1),
      pow_succ (-1 : R) d, pow_succ (-p) d]
    ring

private theorem power_certificate : (-p)^1073753100 = (-1 : R) := by
  -- Keep all intermediate residues bounded, including in the kernel.
  let step (x : R) := x*x
  have even (k : ℕ) : (-p)^(2*k) = step ((-p)^k) := by simp [step, two_mul, pow_add]
  have odd (k : ℕ) : (-p)^(2*k+1) = step ((-p)^k)*(-p) := by rw [pow_succ, even]
  rw [show 1073753100 = 2*536876550 by decide, even 536876550]
  rw [show 536876550 = 2*268438275 by decide, even 268438275]
  rw [show 268438275 = 2*134219137+1 by decide, odd 134219137]
  rw [show 134219137 = 2*67109568+1 by decide, odd 67109568]
  rw [show 67109568 = 2*33554784 by decide, even 33554784]
  rw [show 33554784 = 2*16777392 by decide, even 16777392]
  rw [show 16777392 = 2*8388696 by decide, even 8388696]
  rw [show 8388696 = 2*4194348 by decide, even 4194348]
  rw [show 4194348 = 2*2097174 by decide, even 2097174]
  rw [show 2097174 = 2*1048587 by decide, even 1048587]
  rw [show 1048587 = 2*524293+1 by decide, odd 524293]
  rw [show 524293 = 2*262146+1 by decide, odd 262146]
  rw [show 262146 = 2*131073 by decide, even 131073]
  rw [show 131073 = 2*65536+1 by decide, odd 65536]
  rw [show 65536 = 2*32768 by decide, even 32768]
  rw [show 32768 = 2*16384 by decide, even 16384]
  rw [show 16384 = 2*8192 by decide, even 8192]
  rw [show 8192 = 2*4096 by decide, even 4096]
  rw [show 4096 = 2*2048 by decide, even 2048]
  rw [show 2048 = 2*1024 by decide, even 1024]
  rw [show 1024 = 2*512 by decide, even 512]
  rw [show 512 = 2*256 by decide, even 256]
  rw [show 256 = 2*128 by decide, even 128]
  rw [show 128 = 2*64 by decide, even 64]
  rw [show 64 = 2*32 by decide, even 32]
  rw [show 32 = 2*16 by decide, even 16]
  rw [show 16 = 2*8 by decide, even 8]
  rw [show 8 = 2*4 by decide, even 4]
  rw [show 4 = 2*2 by decide, even 2]
  rw [show 2 = 2*1 by decide, even 1]
  decide

theorem noOddReturn (d : ℕ) (hd : Odd d) : (-p)^d ≠ 1 := by
  intro h
  have perm : ((-p)^1073753100)^d = ((-p)^d)^1073753100 := by
    rw [← pow_mul, ← pow_mul, Nat.mul_comm]
  rw [power_certificate, hd.neg_one_pow, h, one_pow] at perm
  exact (by decide : (-1 : R) ≠ 1) perm

/-- The extension order residue vanishes exactly in even degree. -/
theorem extensionResidue (d : ℕ) : p^d + 1 - trace d = 0 ↔ Even d := by
  rw [trace_eq]
  have fac : p^d + 1 - ((-1 : R)^d + (-p)^d) = (1-(-1 : R)^d)*(1-(-p)^d) := by
    have h : (-1 : R)^d * (-p)^d = p^d := by rw [← mul_pow, show (-1 : R)*(-p) = p by decide]
    linear_combination -h
  rw [fac]
  rcases Nat.even_or_odd d with h | h
  · simp [h.neg_one_pow,h]
  · constructor
    · intro e
      rw [h.neg_one_pow] at e
      have t := congrArg (fun z : R => 1073753101*z) e
      change 1073753101*((1-(-1))*(1-(-p)^d)) = 1073753101*0 at t
      rw [← mul_assoc, show (1073753101 : R)*(1-(-1)) = 1 by decide,
        one_mul, mul_zero, sub_eq_zero] at t
      exact False.elim (noOddReturn d h t.symm)
    · exact fun e => False.elim (Nat.not_even_iff_odd.mpr h e)

end M31E2Extension
