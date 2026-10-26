import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.IntervalCases
import Mathlib.Tactic.NormNum
import Mathlib.Data.Int.ModEq

/-! Matrix congruences for the shifts by ±1/4 on Γ₀(432). -/

namespace ShiftSubgroup

private theorem sameResidue (a b c d k : ℤ)
    (hc : c = 432 * k) (hdet : a * d - b * c = 1) : (d - a) % 4 = 0 := by
  have hbc : 4 ∣ b * c := by
    rw [hc]
    refine ⟨108 * b * k, ?_⟩
    ring
  have hprod : (a * d) % 4 = 1 := by
    obtain ⟨z, hz⟩ := hbc
    rw [hz] at hdet
    omega
  have hres : ((a % 4) * (d % 4)) % 4 = 1 := by
    rw [← Int.mul_emod]
    exact hprod
  have ha : 0 ≤ a % 4 ∧ a % 4 < 4 := by omega
  have hd : 0 ≤ d % 4 ∧ d % 4 < 4 := by omega
  rcases ha with ⟨ha0, ha4⟩
  rcases hd with ⟨hd0, hd4⟩
  interval_cases h₁ : a % 4 <;> interval_cases h₂ : d % 4 <;>
    norm_num [h₁, h₂] at hres <;> omega

theorem shiftedMatrix (a b c d k : ℤ)
    (hc : c = 432 * k) (hdet : a * d - b * c = 1) :
    ∃ e : ℤ, d - a = 4 * e ∧
      (4 * b + d - a - 108 * k) % 4 = 0 ∧ 27 ∣ c := by
  have hmod := sameResidue a b c d k hc hdet
  have hdiv : 4 ∣ d - a := Int.dvd_of_emod_eq_zero hmod
  obtain ⟨e, he⟩ := hdiv
  refine ⟨e, he, ?_, ?_⟩
  · omega
  · rw [hc]
    refine ⟨16 * k, ?_⟩
    ring

theorem bothConjugates (a b c d k : ℤ)
    (hc : c = 432 * k) (hdet : a * d - b * c = 1) :
    ∃ e : ℤ, d - a = 4 * e ∧
      (a + 108 * k) * (d - 108 * k) - (b + e - 27 * k) * c = 1 ∧
      (a - 108 * k) * (d + 108 * k) - (b - e - 27 * k) * c = 1 ∧
      27 ∣ c := by
  obtain ⟨e, he, _, hc27⟩ := shiftedMatrix a b c d k hc hdet
  have hd : d = a + 4 * e := by omega
  refine ⟨e, he, ?_, ?_, hc27⟩
  · have h : (a + 108 * k) * (d - 108 * k) - (b + e - 27 * k) * c =
        a * d - b * c := by rw [hd, hc]; ring
    rw [h, hdet]
  · have h : (a - 108 * k) * (d + 108 * k) - (b - e - 27 * k) * c =
        a * d - b * c := by rw [hd, hc]; ring
    rw [h, hdet]

theorem conjugateTwistY {K : Type*} [Field K] [CharZero K] (i y : K) :
    -8 * (-i) * ((-y - 1) + 1 / 2) = -8 * i * (y + 1 / 2) := by
  field_simp
  ring

theorem commonLevel (N : ℤ) (h16 : 16 ∣ N) (h27 : 27 ∣ N) : 432 ∣ N := by
  obtain ⟨u, hu⟩ := h16
  obtain ⟨v, hv⟩ := h27
  refine ⟨22 * v - 13 * u, ?_⟩
  omega

#print axioms shiftedMatrix
#print axioms bothConjugates
#print axioms conjugateTwistY
#print axioms commonLevel

end ShiftSubgroup
