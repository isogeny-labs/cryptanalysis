import Mathlib.NumberTheory.LucasLehmer
import Mathlib.RingTheory.RootsOfUnity.PrimitiveRoots
import Mathlib.Tactic.ReduceModChar

namespace M31Rotation

abbrev F := ZMod 2147483647

local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private theorem two_primitive : IsPrimitiveRoot (2 : F) 31 := by
  letI : Fact (Nat.Prime 31) := ⟨by decide⟩
  apply IsPrimitiveRoot.iff_orderOf.mpr
  apply orderOf_eq_prime <;> decide

/-- Equality of keys detects precisely the orbit of cyclic bit rotation
(multiplication by two modulo the Mersenne prime), including zero. -/
theorem orbitKey_eq_iff (x y : F) :
    x ^ 31 = y ^ 31 ↔ ∃ i < 31, y = 2 ^ i * x := by
  constructor
  · intro h
    by_cases hx : x = 0
    · subst x
      have hy : y = 0 := by simpa using h.symm
      exact ⟨0, by decide, by simpa using hy⟩
    · have hr : (y / x) ^ 31 = 1 := by
        rw [div_pow, ← h, div_self (pow_ne_zero _ hx)]
      obtain ⟨i, hi, he⟩ := two_primitive.eq_pow_of_pow_eq_one hr
      exact ⟨i, hi, (div_eq_iff hx).mp he.symm⟩
  · rintro ⟨i, _, rfl⟩
    rw [mul_pow, ← pow_mul, Nat.mul_comm i 31, pow_mul, two_primitive.pow_eq_one,
      one_pow, one_mul]

theorem orbitKey_extend (x q : F) :
    ((x * q) ^ 31, ((x * q) ^ 31)⁻¹) =
      (x ^ 31 * q ^ 31, (x ^ 31)⁻¹ * (q ^ 31)⁻¹) := by
  simp [mul_pow, mul_comm]

end M31Rotation
