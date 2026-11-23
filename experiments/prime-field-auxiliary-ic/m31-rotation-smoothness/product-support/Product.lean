import Mathlib.NumberTheory.LucasLehmer
import Mathlib.RingTheory.RootsOfUnity.PrimitiveRoots

namespace M31ProductSupport

abbrev F := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

/-- An integer factorization supports reciprocal M31 orbit keys exactly
when its product reduces to one of the 31 powers of two. -/
theorem product_criterion (a b : ℕ) :
    (a : F)^31 * (b : F)^31 = 1 ↔
      ∃ j < 31, ((a*b : ℕ) : F) = 2^j := by
  letI : Fact (Nat.Prime 31) := ⟨by decide⟩
  have h : IsPrimitiveRoot (2 : F) 31 := by
    apply IsPrimitiveRoot.iff_orderOf.mpr
    apply orderOf_eq_prime <;> decide
  rw [Nat.cast_mul, ← mul_pow]
  constructor
  · intro hab
    obtain ⟨j, hj, he⟩ := h.eq_pow_of_pow_eq_one hab
    exact ⟨j, hj, he.symm⟩
  · rintro ⟨j, _, hj⟩
    rw [hj, ← pow_mul, Nat.mul_comm j 31, pow_mul, h.pow_eq_one, one_pow]

end M31ProductSupport
