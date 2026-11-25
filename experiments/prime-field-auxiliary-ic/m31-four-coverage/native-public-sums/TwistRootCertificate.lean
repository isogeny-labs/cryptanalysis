import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic
import Mathlib.Tactic

namespace M31.TwistRootCertificate

abbrev p : ℕ := 2147483647
abbrev F := ZMod p
private instance : Fact (Nat.Prime p) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

private abbrev Triple := F × F × F

private def eval (x : F) (t : Triple) := t.1 + t.2.1*x + t.2.2*x^2

/-- Square a quadratic remainder and multiply by X modulo X³ + 2X + 14. -/
private def step : Triple → Triple
  | (c,b,a) =>
    let z := 2*c*a + b^2 - 2*a^2
    (-14*z, c^2 - 28*a*b - 2*z, 2*c*b - 4*a*b - 14*a^2)

private theorem step_eval (x : F) (h : x^3+2*x+14=0) (t : Triple) :
    eval x (step t) = (eval x t)^2 * x := by
  rcases t with ⟨c,b,a⟩
  dsimp [eval,step]
  linear_combination -(a^2*x^2+2*a*b*x+2*c*a+b^2-2*a^2)*h

private def remAt : ℕ → Triple
  | 0 => (1,0,0)
  | n+1 => step (remAt n)

private def exponent : ℕ → ℕ
  | 0 => 0
  | n+1 => exponent n * 2 + 1

private theorem rem_eval (x : F) (h : x^3+2*x+14=0) (n : ℕ) :
    eval x (remAt n) = x^(exponent n) := by
  induction n with
  | zero => simp [eval, remAt, exponent]
  | succ n ih => rw [remAt, step_eval x h, ih, exponent, ← pow_mul, ← pow_succ]

theorem no_plus_root (x : F) : x^3+2*x+14 ≠ 0 := by
  intro h
  have h0 : remAt 0 = (1,0,0) := rfl
  have h3 : remAt 3 = (2147483591,188,56) := by
    rw [remAt, remAt, remAt, h0]; decide
  have h6 : remAt 6 = (287997321,187163505,1024043359) := by
    rw [remAt, remAt, remAt, h3]; decide
  have h9 : remAt 9 = (451195146,1045306002,1428587628) := by
    rw [remAt, remAt, remAt, h6]; decide
  have h12 : remAt 12 = (1960045820,1868732356,1249716909) := by
    rw [remAt, remAt, remAt, h9]; decide
  have h15 : remAt 15 = (624148369,1674369068,556153959) := by
    rw [remAt, remAt, remAt, h12]; decide
  have h18 : remAt 18 = (1537489774,1796622096,2112366482) := by
    rw [remAt, remAt, remAt, h15]; decide
  have h21 : remAt 21 = (722964431,952989742,869812270) := by
    rw [remAt, remAt, remAt, h18]; decide
  have h24 : remAt 24 = (1331363844,1527957742,1114921255) := by
    rw [remAt, remAt, remAt, h21]; decide
  have h27 : remAt 27 = (105461245,1792916438,1995712167) := by
    rw [remAt, remAt, remAt, h24]; decide
  have h30 : remAt 30 = (21404514,444808042,280435294) := by
    rw [remAt, remAt, remAt, h27]; decide
  have h31 : remAt 31 = (1097082803,1829455705,1359683014) := by
    rw [remAt, h30]; decide
  have hf := rem_eval x h 31
  rw [h31, show exponent 31 = p by decide] at hf
  have xp : x^p = x := by simp
  rw [xp] at hf
  dsimp [eval] at hf
  have hp : (2147483647 : F) = 0 := by decide
  have bad : (1053118941 : F) = 0 := by
    linear_combination (1889091025*x+1987489675)*h +
      (1931024232*x^2+1588381504*x+1858157426)*hf -
      (949275021+2394431628*x+3516148858*x^2+2650738997*x^3+1222631359*x^4)*hp
  exact (by decide : (1053118941 : F) ≠ 0) bad

theorem no_minus_root (x : F) : x^3+2*x-14 ≠ 0 := by
  intro h
  apply no_plus_root (-x)
  linear_combination -h

end M31.TwistRootCertificate
