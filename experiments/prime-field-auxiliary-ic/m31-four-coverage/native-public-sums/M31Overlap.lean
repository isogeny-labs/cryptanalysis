import TwistQuotients
import TwistRootCertificate

namespace M31.Overlap

open TwistQuotients
open TwistRootCertificate (p F)

private instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private theorem odd_char : ringChar F ≠ 2 := by rw [ZMod.ringChar_zmod_n]; decide

private def plus (x : F) := x^3 + 2*x + 14
private def minus (x : F) := x^3 + 2*x - 14

theorem cancel_traces : pointTrace plus + pointTrace minus = 0 := by
  have negOne : quadraticChar F (-1) = -1 := by
    rw [quadraticChar_neg_one odd_char, ZMod.card]
    decide
  have swap (x : F) : quadraticChar F (plus (-x)) = -(quadraticChar F (minus x)) := by
    have h : plus (-x) = (-1) * minus x := by unfold plus minus; ring
    rw [h, map_mul, negOne, neg_one_mul]
  have perm := Equiv.sum_comp (Equiv.neg F) (fun x => quadraticChar F (plus x))
  change (∑ x : F, quadraticChar F (plus (-x))) = _ at perm
  simp_rw [swap] at perm
  rw [Finset.sum_neg_distrib] at perm
  rw [trace_eq odd_char, trace_eq odd_char]
  linarith

/-- Conditional only on the two auxiliary point counts, expressed as one
point at infinity and the affine pairs of the monic GP models. -/
theorem census_of_orders
    (first : Fintype.card (CurvePoints (fun u : F => u^3 + 4*u^2 + 4*u - 196)) = 2147414707)
    (second : Fintype.card (CurvePoints (fun u : F => u^3 + 4*u^2 - 784*u + 196^2)) = 2147446647) :
    Nat.card {x : F // IsSquare (x^3 + 2*x + 14) ∧ IsSquare (x^3 + 2*x - 14)} =
      536844426 := by
  classical
  have count := four_common odd_char plus minus
    TwistRootCertificate.no_plus_root TwistRootCertificate.no_minus_root
  have corr := correlation_traces odd_char (by decide : (-196 : F) ≠ 0)
  change (∑ x : F, quadraticChar F (plus x * minus x)) = _ at corr
  simp only [pointTrace, first, second, ZMod.card] at corr
  rw [corr, ZMod.card] at count
  have cancel := cancel_traces
  change Nat.card {x // IsSquare (plus x) ∧ IsSquare (minus x)} = _
  rw [Nat.card_eq_fintype_card]
  unfold p at count
  omega

end M31.Overlap
