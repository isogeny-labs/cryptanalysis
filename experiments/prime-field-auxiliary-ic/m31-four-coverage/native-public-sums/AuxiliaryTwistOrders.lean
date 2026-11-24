import M31Overlap

namespace M31.AuxiliaryTwistOrders

open TwistQuotients
open TwistRootCertificate (p F)

private instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

abbrev twist (f : F → F) (x : F) := -(f (-x))

theorem twist_total (f : F → F) :
    Fintype.card (CurvePoints f) + Fintype.card (CurvePoints (twist f)) = 4294967296 := by
  have oddChar : ringChar F ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide
  have negOne : quadraticChar F (-1) = -1 := by
    rw [quadraticChar_neg_one oddChar, ZMod.card]; decide
  have row (x : F) : quadraticChar F (twist f x) = -quadraticChar F (f (-x)) := by
    unfold twist
    rw [← neg_one_mul (f (-x)), map_mul, negOne, neg_one_mul]
  have perm := Equiv.sum_comp (Equiv.neg F) (fun x => quadraticChar F (f x))
  change (∑ x : F, quadraticChar F (f (-x))) = _ at perm
  have tr : pointTrace f + pointTrace (twist f) = 0 := by
    rw [trace_eq oddChar, trace_eq oddChar]
    simp_rw [row]
    rw [Finset.sum_neg_distrib, perm]
    ring
  simp only [pointTrace, ZMod.card, p] at tr
  omega

/-- A divisor above half the curve-plus-twist total determines the entire
twist order. Positivity follows from its point at infinity. -/
theorem order_from_large_divisor (f : F → F) (d : ℕ) (large : 2147483648 < d)
    (divides : d ∣ Fintype.card (CurvePoints (twist f))) :
    Fintype.card (CurvePoints f) = 4294967296 - d := by
  have total := twist_total f
  have pos : 0 < Fintype.card (CurvePoints (twist f)) := Fintype.card_pos
  obtain ⟨k,h⟩ := divides
  have one : k = 1 := by
    by_contra hk
    have two : 2 ≤ k := by
      by_cases hz : k = 0
      · simp [hz] at h
      · omega
    have twice := Nat.mul_le_mul_left d two
    omega
  rw [one, Nat.mul_one] at h
  omega

abbrev first (x : F) := x^3 + 4*x^2 + 4*x - 196
abbrev second (x : F) := x^3 + 4*x^2 - 784*x + 196^2

theorem census_of_twist_divisors
    (h₁ : 2147552589 ∣ Fintype.card (CurvePoints (twist first)))
    (h₂ : 2147520649 ∣ Fintype.card (CurvePoints (twist second))) :
    Nat.card {x : F // IsSquare (x^3 + 2*x + 14) ∧ IsSquare (x^3 + 2*x - 14)} =
      536844426 := by
  apply Overlap.census_of_orders
  · exact order_from_large_divisor first _ (by decide) h₁
  · exact order_from_large_divisor second _ (by decide) h₂

end M31.AuxiliaryTwistOrders
