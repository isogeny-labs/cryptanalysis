import Mathlib

/-! Reciprocal coordinates on the auxiliary curve y² = x³ + x.
The finite checks use the fifteen positive half-orbit lags modulo 31. -/
namespace M31Reciprocal

variable {F : Type*} [Field F]

def dbl (P : F × F) : F × F :=
  ((P.1^2 - P.2^2)^2, 4 * P.1 * P.2 * (P.1^2 + P.2^2))

theorem swap_double (x z : F) : dbl (z,x) = dbl (x,z) := by
  apply Prod.ext <;> dsimp [dbl] <;> ring

def repeatDouble (P : F × F) : ℕ → F × F
  | 0 => P
  | n+1 => dbl (repeatDouble P n)

theorem swap_fiber (x z : F) (n : ℕ) :
    repeatDouble (z,x) (n+1) = repeatDouble (x,z) (n+1) := by
  induction n with
  | zero => exact swap_double x z
  | succ n ih => exact congrArg dbl ih

theorem same_lag (a x y : F) (hx : x ≠ 0) (hy : y ≠ 0) (h : y = a*x) :
    x⁻¹ = a*y⁻¹ := by
  field_simp
  simpa [mul_comm] using h

theorem fixed (x y : F) (hy : y ≠ 0) : y⁻¹ = x ↔ x*y = 1 := by
  constructor
  · rintro rfl
    exact inv_mul_cancel₀ hy
  · intro h
    calc
      y⁻¹ = (x*y)*y⁻¹ := by rw [h, one_mul]
      _ = x := by rw [mul_assoc, mul_inv_cancel₀ hy, mul_one]

theorem fixed_root_exhaustion (a t x : F) (ht : a*t^2 = 1) :
    a*x^2 = 1 ↔ x = t ∨ x = -t := by
  constructor
  · intro hx
    have ha : a ≠ 0 := by
      intro h
      simp [h] at ht
    have hprod : a*((x-t)*(x+t)) = 0 := by linear_combination hx - ht
    rcases mul_eq_zero.mp ((mul_eq_zero.mp hprod).resolve_left ha) with h | h
    · exact Or.inl (sub_eq_zero.mp h)
    · exact Or.inr (eq_neg_of_add_eq_zero_left h)
  · rintro (rfl | rfl)
    · exact ht
    · simpa using ht

abbrev K := ZMod 2147483647

def eulerLoop (x : K) : Nat → K
  | 0 => 1
  | n+1 => (eulerLoop x n)^2*x

theorem eulerLoop_spec (x : K) (n : Nat) : eulerLoop x n * x = x^(2^n) := by
  induction n with
  | zero => simp [eulerLoop]
  | succ n ih =>
    rw [pow_succ (2:Nat), pow_mul, ← ih]
    simp [eulerLoop]
    ring

def lags := (List.range 15).map (·+1)
def candidate (j : Nat) : K := -(2^((31-(16*j)%31)%31))

theorem candidate_checks : lags.all (fun j => decide ((2:K)^j*(candidate j)^2=1 ∧
    eulerLoop (candidate j) 30 = -1 ∧ eulerLoop (-candidate j) 30 = 1 ∧
    eulerLoop ((candidate j)^2+1) 30 = eulerLoop (1+(2:K)^j) 30)) = true := by
  native_decide

theorem fixed_lags : lags.filter (fun j => eulerLoop (1+(2:K)^j) 30 == -1) =
    [1,2,6,7,9,10,12,14] := by native_decide

end M31Reciprocal
