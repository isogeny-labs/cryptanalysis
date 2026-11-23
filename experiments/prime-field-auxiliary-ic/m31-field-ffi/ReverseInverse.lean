import Mathlib

namespace ReverseInverse
abbrev F := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def reciprocal (y : F) : F :=
  let r := (BitVec.ofNat 32 y.val).reverse
  (((r &&& 2147483647) ||| (r >>> 31)).toNat : F)

private theorem order62 : IsPrimitiveRoot (-2 : F) 62 := by
  apply IsPrimitiveRoot.iff_orderOf.mpr
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide)
  · decide
  intro q prime dvd
  change q ∣ 2 * 31 at dvd
  rcases prime.dvd_mul.mp dvd with h | h
  · obtain rfl := (Nat.prime_dvd_prime_iff_eq prime (by decide)).mp h
    decide
  · obtain rfl := (Nat.prime_dvd_prime_iff_eq prime (by decide)).mp h
    decide

/-- Each block performs five squarings, then multiplies by the input. -/
def blocks (x : F) : Nat → F
  | 0 => x
  | n+1 => (blocks x n)^32 * x

private def blockExponent : Nat → Nat
  | 0 => 1
  | n+1 => blockExponent n * 32 + 1

private theorem blocks_pow (x : F) (n : Nat) : blocks x n = x^(blockExponent n) := by
  induction n with
  | zero => simp [blocks, blockExponent]
  | succ n ih => rw [blocks, ih, ← pow_mul, ← pow_succ, blockExponent]

theorem correct (x : F) (hx : x ≠ 0) :
    x^34636832 * reciprocal (x^34636833) = x⁻¹ := by
  have hpow : (x^34636833)^62 = 1 := by
    rw [← pow_mul]
    simpa only [ZMod.card] using FiniteField.pow_card_sub_one_eq_one x hx
  obtain ⟨i, hi, eq⟩ := order62.eq_pow_of_pow_eq_one hpow
  have allKeys : ∀ j : Fin 62, reciprocal ((-2 : F)^j.val) * ((-2 : F)^j.val) = 1 := by
    native_decide
  have hk := allKeys ⟨i,hi⟩
  change reciprocal ((-2 : F)^i) * ((-2 : F)^i) = 1 at hk
  rw [eq] at hk
  apply (mul_left_inj' hx).mp
  calc
    x ^ 34636832 * reciprocal (x ^ 34636833) * x =
      reciprocal (x ^ 34636833) * (x ^ 34636832 * x) := by rw [mul_right_comm, mul_comm (x^34636832 * x)]
    _ = 1 := by rwa [← pow_succ]
    _ = x⁻¹ * x := (inv_mul_cancel₀ hx).symm

theorem schedule (x : F) (hx : x ≠ 0) :
    let t := (blocks x 4)^32
    t * reciprocal (t*x) = x⁻¹ := by
  dsimp only
  rw [blocks_pow, ← pow_mul, show blockExponent 4 * 32 = 34636832 by decide, ← pow_succ]
  exact correct x hx

end ReverseInverse
