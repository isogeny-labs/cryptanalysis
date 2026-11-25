import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic

namespace M31TwistLift
abbrev p := 2147483647
abbrev F := ZMod p
local instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

theorem reflected_rhs (x : F) : (-x)^3 + 2*(-x) - 14 = -(x^3 + 2*x + 14) := by ring

/-- A single ordinate candidate covers both signs, even when the input is zero. -/
theorem covers (v : F) :
    (v^(2^29 : ℕ))^2 = v ∨ (v^(2^29 : ℕ))^2 = -v := by
  apply sq_eq_sq_iff_eq_or_eq_neg.mp
  rw [← pow_mul, ← pow_mul]
  change v^(2147483647+1 : ℕ) = v^2
  rw [pow_succ, ZMod.pow_card, pow_two]

theorem same_candidate (v : F) : (-v)^(2^29 : ℕ) = v^(2^29 : ℕ) := by
  exact Even.neg_pow (by decide : Even (2^29 : ℕ)) v

end M31TwistLift
