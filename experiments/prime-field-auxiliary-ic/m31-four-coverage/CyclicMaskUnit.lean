import Mathlib

namespace M31CyclicMaskUnit

abbrev Ring32 := AddMonoidAlgebra (ZMod 2) (ZMod 32)

private instance : CharP Ring32 2 :=
  charP_of_injective_algebraMap (algebraMap (ZMod 2) Ring32).injective 2

/-- Binary incidence vector, with multiplication given by cyclic convolution. -/
noncomputable def mask (s : Finset (ZMod 32)) : Ring32 :=
  ∑ i ∈ s, AddMonoidAlgebra.single i 1

private theorem basis_pow (i : ZMod 32) :
    (AddMonoidAlgebra.single i 1 : Ring32)^32 = 1 := by
  rw [AddMonoidAlgebra.single_pow]
  have h : (32 : ℕ) • i = 0 := by rw [nsmul_eq_mul, ZMod.natCast_self, zero_mul]
  rw [h, one_pow]
  rfl

theorem convolution_pow (s : Finset (ZMod 32)) : mask s ^ 32 = (s.card : Ring32) := by
  have h := sum_pow_char_pow 2 5 s (fun i => (AddMonoidAlgebra.single i 1 : Ring32))
  simp only [show (2^5 : ℕ) = 32 by decide, basis_pow] at h
  simpa [mask] using h

/-- Every weight-17 selection has inverse equal to its 31st convolution power. -/
theorem inverse_of_seventeen (s : Finset (ZMod 32)) (h : s.card = 17) :
    mask s ^ 31 * mask s = 1 := by
  rw [← pow_succ, convolution_pow, h]
  have two : (2 : Ring32) = 0 := CharP.cast_eq_zero Ring32 2
  linear_combination 8 * two

theorem injective_convolution (s : Finset (ZMod 32)) (h : s.card = 17) :
    Function.Injective (fun a : Ring32 => a * mask s) := by
  intro a b eq
  have cancel := congrArg (fun z : Ring32 => z * mask s ^ 31) eq
  simpa [mul_assoc, mul_comm (mask s) (mask s ^ 31), inverse_of_seventeen s h] using cancel

end M31CyclicMaskUnit
