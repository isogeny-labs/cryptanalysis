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

theorem extension_totient_bound (d : ℕ) : ∀ m : ℕ, (d*m).totient ≤ d*m.totient := by
  induction d using Nat.recOnMul with
  | zero => simp
  | one => simp
  | prime p hp =>
    intro m
    by_cases h : p ∣ m
    · rw [Nat.totient_mul_of_prime_of_dvd hp h]
    · rw [Nat.totient_mul_of_prime_of_not_dvd hp h]
      exact Nat.mul_le_mul_right _ (Nat.sub_le _ _)
  | mul a b ha hb =>
    intro m
    rw [Nat.mul_assoc, Nat.mul_assoc]
    exact (ha _).trans (Nat.mul_le_mul_left _ (hb _))

open Polynomial in
theorem extension_cyclotomic_bound {R : Type*} [CommRing R] (x : R)
    {d m : ℕ} (hd : 0 < d) (hm : 0 < m) (h : (cyclotomic m R).IsRoot (x^d)) :
    (orderOf x).totient ≤ d * m.totient := by
  have hx := h.dvd (cyclotomic.dvd_X_pow_sub_one m R)
  have he : x^(d*m) = 1 := by simpa [IsRoot, pow_mul, sub_eq_zero] using hx
  exact (Nat.le_of_dvd (Nat.totient_pos.mpr (Nat.mul_pos hd hm))
    (Nat.totient_dvd_of_dvd (orderOf_dvd_of_pow_eq_one he))).trans (extension_totient_bound d m)

theorem extensionDimension {d m : ℕ} (hd : 0 < d) (hm : 0 < m)
    (h : (cyclotomic m R).IsRoot (a ^ d)) : 536213520 ≤ d * m.totient := by
  simpa only [exactOrder, phiOrder] using extension_cyclotomic_bound a hd hm h

/-- A product of cyclotomic factors, including repetitions, as in a torus point count. -/
theorem extensionProductDimension {d : ℕ} (hd : 0 < d) (indices : List ℕ)
    (pos : ∀ m ∈ indices, 0 < m)
    (vanishes : (indices.map (fun m => (cyclotomic m R).eval (a ^ d))).prod = 0) :
    536213520 ≤ d * (indices.map Nat.totient).sum := by
  induction indices with
  | nil => simp at vanishes
  | cons m ms ih =>
    simp only [List.map_cons, List.prod_cons, mul_eq_zero] at vanishes
    simp only [List.map_cons, List.sum_cons, Nat.mul_add]
    rcases vanishes with h | h
    · have hb := extensionDimension hd (pos m (by simp)) h
      omega
    · have hb := ih (fun k hk => pos k (List.mem_cons_of_mem _ hk)) h
      omega

end M31Torus
