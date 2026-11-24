import Mathlib.NumberTheory.LucasLehmer
import Mathlib.GroupTheory.OrderOfElement
import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic

namespace M31.ResidueClasses
abbrev p : ℕ := 2147483647
abbrev F := ZMod p
private instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private def exponent : List Bool → ℕ
  | [] => 0
  | b :: bs => exponent bs * 2 + (if b then 1 else 0)

private def value : List Bool → F
  | [] => 1
  | b :: bs => (value bs)^2 * (if b then 7 else 1)

private theorem powers (bs : List Bool) : (7 : F)^exponent bs = value bs := by
  induction bs with
  | nil => simp [exponent,value]
  | cons b bs ih => cases b <;> simp [exponent,value,pow_add,pow_mul,ih]

private theorem pow_1 : (7 : F)^2147483646 = 1 := by
  let bits := [false, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true]
  rw [show 2147483646 = exponent bits by decide, powers]
  decide +kernel

private theorem pow_2 : (7 : F)^1073741823 = 2147483646 := by
  let bits := [true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true, true]
  rw [show 1073741823 = exponent bits by decide, powers]
  decide +kernel

private theorem pow_3 : (7 : F)^715827882 = 1513477735 := by
  let bits := [false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true, false, true]
  rw [show 715827882 = exponent bits by decide, powers]
  decide +kernel

private theorem pow_7 : (7 : F)^306783378 = 1205362885 := by
  let bits := [false, true, false, false, true, false, false, true, false, false, true, false, false, true, false, false, true, false, false, true, false, false, true, false, false, true, false, false, true]
  rw [show 306783378 = exponent bits by decide, powers]
  decide +kernel

private theorem pow_11 : (7 : F)^195225786 = 1969212174 := by
  let bits := [false, true, false, true, true, true, false, true, false, false, false, true, false, true, true, true, false, true, false, false, false, true, false, true, true, true, false, true]
  rw [show 195225786 = exponent bits by decide, powers]
  decide +kernel

private theorem pow_31 : (7 : F)^69273666 = 512 := by
  let bits := [false, true, false, false, false, false, true, false, false, false, false, true, false, false, false, false, true, false, false, false, false, true, false, false, false, false, true]
  rw [show 69273666 = exponent bits by decide, powers]
  decide +kernel

private theorem pow_151 : (7 : F)^14221746 = 535044134 := by
  let bits := [false, true, false, false, true, true, false, true, true, false, false, false, false, false, false, false, true, false, false, true, true, false, true, true]
  rw [show 14221746 = exponent bits by decide, powers]
  decide +kernel

private theorem pow_331 : (7 : F)^6487866 = 1761855083 := by
  let bits := [false, true, false, true, true, true, false, false, true, true, true, true, true, true, true, true, false, true, false, false, false, true, true]
  rw [show 6487866 = exponent bits by decide, powers]
  decide +kernel

theorem generator_order : orderOf (7 : F) = 2147483646 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) pow_1
  intro q hq hd
  change q ∣ 2 * 3 * 3 * 7 * 11 * 31 * 151 * 331 at hd
  simp only [hq.dvd_mul] at hd
  rcases hd with (((((((h | h) | h) | h) | h) | h) | h) | h)
  all_goals first
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 2)).mp h
      subst q; rw [pow_2]; decide
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 3)).mp h
      subst q; rw [pow_3]; decide
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 7)).mp h
      subst q; rw [pow_7]; decide
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 11)).mp h
      subst q; rw [pow_11]; decide
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 31)).mp h
      subst q; rw [pow_31]; decide
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 151)).mp h
      subst q; rw [pow_151]; decide
    | have eq := (Nat.prime_dvd_prime_iff_eq hq (by norm_num : Nat.Prime 331)).mp h
      subst q; rw [pow_331]; decide

theorem within_class_period : orderOf ((7 : F)^462) = 4648233 := by
  rw [orderOf_pow' (x := (7 : F)) (n := 462) (by decide), generator_order]
  decide

theorem exponent_partition (k i : ℕ) (hk : k < 462) :
    (k + 462*i) % 462 = k ∧ (k + 462*i) / 462 = i := by
  omega

theorem negative_representative (e : ℕ) :
    -((7 : F)^e) = 7^(e + 1073741823) := by
  rw [pow_add, pow_2, show (2147483646 : F) = -1 by decide]
  simp

theorem opposite_class (e : ℕ) :
    (e + 1073741823) % 462 = (e + 231) % 462 := by omega

theorem negative_polynomials (x : F) :
    ((-x)^3 + 2*(-x) + 14 = -(x^3 + 2*x - 14)) ∧
    ((-x)^3 + 2*(-x) - 14 = -(x^3 + 2*x + 14)) := by
  constructor <;> ring

theorem negation_flips_square (x : F) (hx : x ≠ 0) : IsSquare (-x) ↔ ¬IsSquare x := by
  have hm : ¬ IsSquare (-1 : F) := by
    rw [FiniteField.isSquare_neg_one_iff, ZMod.card]
    decide
  rw [← quadraticChar_one_iff_isSquare (neg_ne_zero.mpr hx),
      ← quadraticChar_neg_one_iff_not_isSquare, ← neg_one_mul x,
      map_mul, quadraticChar_neg_one_iff_not_isSquare.mpr hm]
  constructor <;> intro h <;> linarith

/-- Indices of the reflected bit in the 2^31-bit square table. -/
theorem mirror_word (z : ℕ) (hz : z < p) :
    (p - z) / 64 = 33554431 - z / 64 ∧
    (p - z) % 64 = 63 - z % 64 := by
  unfold p at *
  omega

end M31.ResidueClasses
