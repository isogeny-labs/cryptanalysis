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

/-- A scale hits the orbit of y at x exactly when its key is the quotient
of the orbit keys. Each candidate scale is itself tracked up to rotation. -/
theorem scale_hits_orbit (s x y : F) (hx : x ≠ 0) :
    (∃ i < 31, s*x = 2^i*y) ↔ s^31 = y^31 / x^31 := by
  rw [← orbitKey_eq_iff, eq_div_iff (pow_ne_zero _ hx), mul_pow, eq_comm]

/-- An inversion-closed coordinate set gives the same hits for reciprocal
rescaling at s and ordinary rescaling at its inverse. -/
theorem reciprocal_scale_hits (S : Set F) (closed : ∀ z, z ∈ S ↔ z⁻¹ ∈ S)
    (s x : F) : s/x ∈ S ↔ s⁻¹*x ∈ S := by
  simpa [div_eq_mul_inv, mul_comm] using closed (s/x)

theorem orbitKey_extend (x q : F) :
    ((x * q) ^ 31, ((x * q) ^ 31)⁻¹) =
      (x ^ 31 * q ^ 31, (x ^ 31)⁻¹ * (q ^ 31)⁻¹) := by
  simp [mul_pow, mul_comm]

/-- Squaring the rotation key merges exactly an orbit and its negative. -/
theorem signedOrbitKey_eq_iff (x y : F) :
    x^62 = y^62 ↔ (∃ i < 31, y = 2^i*x) ∨ (∃ i < 31, -y = 2^i*x) := by
  rw [← orbitKey_eq_iff, ← orbitKey_eq_iff]
  change x^(31*2 : ℕ) = y^(31*2 : ℕ) ↔ _
  rw [pow_mul, pow_mul, sq_eq_sq_iff_eq_or_eq_neg]
  rw [(by decide : Odd 31).neg_pow]

/-- The signed Euler value used for a lift is unchanged by rotation and
changes sign under negation. This also includes the zero field element. -/
theorem rotationEuler (x : F) (i : ℕ) :
    (2^i*x)^1073741823 = x^1073741823 ∧
    (-(2^i*x))^1073741823 = -x^1073741823 := by
  have unit : (2 : F)^1073741823 = 1 := by
    change (2 : F)^(31*34636833 : ℕ) = 1
    rw [pow_mul, two_primitive.pow_eq_one, one_pow]
  have same : ((2 : F)^i*x)^1073741823 = x^1073741823 := by
    rw [mul_pow, ← pow_mul, Nat.mul_comm i, pow_mul, unit, one_pow, one_mul]
  exact ⟨same, by rw [(by decide : Odd 1073741823).neg_pow, same]⟩

end M31Rotation
