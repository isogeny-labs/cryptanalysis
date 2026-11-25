import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic.ReduceModChar

namespace M31ProjectionLabel

abbrev K := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

abbrev generator : K := 1251907261

theorem generator_order : IsPrimitiveRoot generator 65534 := by
  apply IsPrimitiveRoot.iff_orderOf.mpr
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide)
  · unfold generator K; reduce_mod_char
  intro q prime dvd
  change q ∣ 2 * 7 * 31 * 151 at dvd
  rw [prime.dvd_mul, prime.dvd_mul, prime.dvd_mul] at dvd
  rcases dvd with ((h | h) | h) | h <;>
    (obtain rfl := (Nat.prime_dvd_prime_iff_eq prime (by decide)).mp h
     unfold generator K
     reduce_mod_char
     decide)

theorem covered (x : K) (hx : x ≠ 0) :
    ∃ i < 65534, generator ^ i = x ^ 32769 := by
  apply generator_order.eq_pow_of_pow_eq_one
  rw [← pow_mul]
  simpa only [ZMod.card] using FiniteField.pow_card_sub_one_eq_one x hx

theorem label (x : K) (hx : x ≠ 0) (i : Nat) (key : generator^i = x^32769) :
    IsSquare x ↔ Even i := by
  have hchar : ringChar K ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide
  rw [FiniteField.isSquare_iff hchar hx, ZMod.card]
  have power : x^(2147483647/2 : Nat) = (-1 : K)^i := calc
    _ = (x^32769)^32767 := by rw [← pow_mul]
    _ = (generator^32767)^i := by rw [← key, ← pow_mul, Nat.mul_comm, pow_mul]
    _ = _ := by rw [show generator^32767 = -1 by unfold generator K; reduce_mod_char]
  rw [power]
  exact neg_one_pow_eq_one_iff_even (by decide : (-1 : K) ≠ 1)

/-- Exhaustive agreement on the finite table domain suffices for every nonzero input. -/
theorem lookup_correct (lookup : K → Bool)
    (checked : ∀ i < 65534, lookup (generator^i) = true ↔ Even i)
    (x : K) (hx : x ≠ 0) : lookup (x^32769) = true ↔ IsSquare x := by
  obtain ⟨i, hi, key⟩ := covered x hx
  exact (key ▸ checked i hi).trans (label x hx i key).symm

/-- Zero is a square and lies outside the multiplicative table domain. -/
theorem lookup_correct_all (lookup : K → Bool)
    (checked : ∀ i < 65534, lookup (generator^i) = true ↔ Even i) (x : K) :
    (if x = 0 then true else lookup (x^32769)) = true ↔ IsSquare x := by
  by_cases hx : x = 0
  · simp [hx, IsSquare.zero]
  · simpa [hx] using lookup_correct lookup checked x hx

end M31ProjectionLabel
