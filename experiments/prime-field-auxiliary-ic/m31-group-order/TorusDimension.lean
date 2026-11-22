import Mathlib
/-!
The residue of the M31 base-field size modulo the target subgroup order has
multiplicative order 1073752646. Any cyclotomic polynomial vanishing there
has degree at least 536213520. The application to algebraic tori uses the
character-lattice formula for the order of the group of rational points.
-/

namespace M31Torus
abbrev R := ZMod 2147505293
abbrev a : R := 2147483647
theorem exactOrder : orderOf a = 1073752646 := by
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide) (by native_decide)
  intro r hr hd
  change r ∣ (2 * 811 * 661993) at hd
  rcases hr.dvd_mul.mp hd with h | h
  · rcases hr.dvd_mul.mp h with h | h
    · have := (Nat.dvd_prime (by decide : Nat.Prime 2)).mp h
      rcases this with e | e
      · exact (hr.ne_one e).elim
      · subst r; native_decide
    · have := (Nat.dvd_prime (by native_decide : Nat.Prime 811)).mp h
      rcases this with e | e
      · exact (hr.ne_one e).elim
      · subst r; native_decide
  · have := (Nat.dvd_prime (by native_decide : Nat.Prime 661993)).mp h
    rcases this with e | e
    · exact (hr.ne_one e).elim
    · subst r; native_decide

theorem splitCriterion (d : ℕ) : a ^ d = 1 ↔ 1073752646 ∣ d := by
  rw [← exactOrder, orderOf_dvd_iff_pow_eq_one]

theorem firstMinus : a ^ (536876323 : ℕ) = -1 := by native_decide

theorem minusBound {d : ℕ} (hd : 0 < d) (h : a ^ d = -1) : 536876323 ≤ d := by
  have h2 : a ^ (d * 2) = 1 := by rw [pow_mul, h]; norm_num
  have dv := (splitCriterion _).mp h2
  have := Nat.le_of_dvd (by omega : 0 < d * 2) dv
  omega
open Polynomial
theorem phiOrder : Nat.totient 1073752646 = 536213520 := by
  change Nat.totient ((2 * 811) * 661993) = _
  rw [Nat.totient_mul (by decide : Nat.Coprime (2 * 811) 661993),
    Nat.totient_mul (by decide : Nat.Coprime 2 811),
    Nat.totient_prime Nat.prime_two,
    Nat.totient_prime (by native_decide : Nat.Prime 811),
    Nat.totient_prime (by native_decide : Nat.Prime 661993)]
theorem cyclotomicBound (m : ℕ) (hm : 0 < m) (h : (cyclotomic m R).IsRoot a) :
    536213520 ≤ Nat.totient m := by
  have hx := h.dvd (cyclotomic.dvd_X_pow_sub_one m R)
  have he : a ^ m = 1 := by simpa [Polynomial.IsRoot, sub_eq_zero] using hx
  rw [← phiOrder]
  exact Nat.le_of_dvd (Nat.totient_pos.mpr hm) (Nat.totient_dvd_of_dvd ((splitCriterion m).mp he))
instance : Fact (Nat.Prime 2147505293) := ⟨by native_decide⟩

theorem attained : (cyclotomic 1073752646 R).IsRoot a := by
  have h : IsPrimitiveRoot a 1073752646 :=
    ⟨(splitCriterion _).mpr dvd_rfl, fun d hd => (splitCriterion d).mp hd⟩
  exact h.isRoot_cyclotomic (by decide)

end M31Torus
