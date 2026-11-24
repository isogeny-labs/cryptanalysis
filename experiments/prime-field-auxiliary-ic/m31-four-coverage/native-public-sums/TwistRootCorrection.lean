import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic

namespace M31.TwistRootCorrection

private def hit (a b : ℤ) : ℤ := if 0 ≤ a ∧ 0 ≤ b then 1 else 0
private def root (a : ℤ) : ℤ := if a = 0 then 1 else 0

private theorem pair (a b : ℤ) (ha : -1 ≤ a ∧ a ≤ 1) (hb : -1 ≤ b ∧ b ≤ 1)
    (disjoint : ¬ (a = 0 ∧ b = 0)) :
    2 * (hit a b + hit (-b) (-a)) = 1 + a*b + root a + root b := by
  obtain ⟨al,au⟩ := ha
  obtain ⟨bl,bu⟩ := hb
  interval_cases a <;> interval_cases b <;> norm_num [hit,root] at *

/-- The two character labels swap and negate under the permutation. Each
zero of the first label then contributes two units to four times the count. -/
theorem four_lifts {ι : Type*} [Fintype ι] (e : ι ≃ ι) (a b : ι → ℤ)
    (ha : ∀ i, -1 ≤ a i ∧ a i ≤ 1) (hb : ∀ i, -1 ≤ b i ∧ b i ≤ 1)
    (disjoint : ∀ i, ¬ (a i = 0 ∧ b i = 0))
    (sa : ∀ i, a (e i) = -(b i)) (sb : ∀ i, b (e i) = -(a i)) :
    4 * (∑ i, if 0 ≤ a i ∧ 0 ≤ b i then (1 : ℤ) else 0) =
      Fintype.card ι + (∑ i, a i*b i) + 2 * (∑ i, if a i = 0 then (1 : ℤ) else 0) := by
  have hits := Equiv.sum_comp e (fun i => hit (a i) (b i))
  simp_rw [sa, sb] at hits
  have roots := Equiv.sum_comp e (fun i => root (a i))
  simp only [sa, root, neg_eq_zero] at roots
  have h := Finset.sum_congr (s₁ := Finset.univ) rfl
    (fun i _ => pair (a i) (b i) (ha i) (hb i) (disjoint i))
  simp only [← Finset.mul_sum, Finset.sum_add_distrib, Finset.sum_const,
    Finset.card_univ, nsmul_eq_mul, mul_one, hits] at h
  unfold hit root at h
  linarith

/-- Apply the paired count to the two twist cubics, including their zeros. -/
theorem cubic_lifts {F : Type*} [Field F] [Fintype F] [DecidableEq F]
    [DecidablePred (IsSquare : F → Prop)] (A B : F) (disjoint : B+B ≠ 0)
    (minusOne : quadraticChar F (-1) = -1) :
    4 * (∑ x : F, if IsSquare (x^3+A*x+B) ∧ IsSquare (x^3+A*x-B) then (1:ℤ) else 0) =
    Fintype.card F + (∑ x : F, quadraticChar F ((x^3+A*x+B)*(x^3+A*x-B))) +
      2 * (∑ x : F, if x^3+A*x+B = 0 then (1:ℤ) else 0) := by
  let f (x : F) := x^3+A*x+B
  let g (x : F) := x^3+A*x-B
  have bounds (v : F) : -1 ≤ quadraticChar F v ∧ quadraticChar F v ≤ 1 := by
    by_cases h : v = 0
    · simp [h]
    · rcases quadraticChar_dichotomy h with h | h <;> omega
  have neg (v : F) : quadraticChar F (-v) = -quadraticChar F v := by
    rw [← neg_one_mul v, map_mul, minusOne, neg_one_mul]
  have roots (x : F) : ¬(quadraticChar F (f x) = 0 ∧ quadraticChar F (g x) = 0) := by
    simp only [quadraticChar_eq_zero_iff]
    rintro ⟨l,r⟩
    apply disjoint
    dsimp [f,g] at l r
    linear_combination l-r
  have h := four_lifts (Equiv.neg F) (fun x => quadraticChar F (f x))
    (fun x => quadraticChar F (g x)) (fun _ => bounds _) (fun _ => bounds _) roots
    (fun x => by rw [← neg]; apply congrArg (quadraticChar F); change (-x)^3+A*(-x)+B = -(x^3+A*x-B); ring)
    (fun x => by rw [← neg]; apply congrArg (quadraticChar F); change (-x)^3+A*(-x)-B = -(x^3+A*x+B); ring)
  have square (v : F) : 0 ≤ quadraticChar F v ↔ IsSquare v := by
    by_cases hv : v = 0
    · simp [hv]
    · rw [← quadraticChar_one_iff_isSquare hv]
      rcases quadraticChar_dichotomy hv with h | h <;> omega
  simpa only [f, g, square, quadraticChar_eq_zero_iff, map_mul] using h

end M31.TwistRootCorrection
