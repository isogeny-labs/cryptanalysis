import Mathlib.FieldTheory.Finite.Basic
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic
import Mathlib.Tactic

namespace M31FiberLift

private instance : Fact (Nat.Prime 2147483647) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def squares {K : Type*} [Monoid K] {ι : Type*} (v : ι → K) : ℕ → ι → K
  | 0 => v
  | n+1 => fun i => (squares v n i)^2

theorem lane_power {K : Type*} [Monoid K] {ι : Type*} (v : ι → K) (n : ℕ) (i : ι) :
    squares v n i = (v i)^(2^n) := by
  induction n with
  | zero => simp [squares]
  | succ n ih =>
    change (squares v n i)^2 = _
    rw [ih, ← pow_mul, pow_succ]

/-- The post-squaring equality test accepts precisely the quadratic residues,
including zero, for any lane index and any width. -/
theorem lift_exact {ι : Type*} (v : ι → ZMod 2147483647) (i : ι) :
    (squares v 29 i)^2 = v i ↔ ∃ z, z^2 = v i := by
  constructor
  · exact fun h => ⟨_,h⟩
  · rintro ⟨z,hz⟩
    rw [lane_power, ← hz]
    calc
      ((z^2)^(2^29 : ℕ))^2 = z^((2*(2^29 : ℕ))*2) := by rw [pow_mul, pow_mul]
      _ = z^(2147483647+1 : ℕ) := by norm_num
      _ = z^2 := by rw [pow_succ, ZMod.pow_card, pow_two]

/-- A single candidate gives a root for the base or the negative twist.
Both square tests succeed simultaneously precisely for zero. -/
theorem twist_split (a : ZMod 2147483647) :
    let t := (a^(2^29 : ℕ))^2
    (t = a ∨ t = -a) ∧ ((t = a ∧ t = -a) ↔ a = 0) := by
  dsimp only
  have h : ((a^(2^29 : ℕ))^2)^2 = a^2 := by
    calc
      _ = a^((2^29 : ℕ)*2*2) := by rw [pow_mul, pow_mul]
      _ = a^(2147483647+1 : ℕ) := by norm_num
      _ = a^2 := by rw [pow_succ, ZMod.pow_card, pow_two]
  refine ⟨sq_eq_sq_iff_eq_or_eq_neg.mp h, ?_⟩
  constructor
  · rintro ⟨h₁,h₂⟩
    have hz : 2*a = 0 := by linear_combination h₂ - h₁
    exact (mul_eq_zero.mp hz).resolve_left (by decide)
  · rintro rfl
    norm_num

theorem twist_rhs {K : Type*} [CommRing K] (x a b : K) :
    (-x)^3 + a*(-x) - b = -(x^3 + a*x + b) := by ring

theorem minus_one_nonsquare : ¬ IsSquare (-1 : ZMod 2147483647) := by
  rw [FiniteField.isSquare_neg_one_iff, ZMod.card]
  decide

theorem twist_lift_exact (a : ZMod 2147483647) :
    (a^(2^29 : ℕ))^2 = -a ↔ ∃ z, z^2 = -a := by
  have h := lift_exact (fun _ : Unit => -a) ()
  rw [lane_power] at h
  have he : Even (2^29 : ℕ) := ⟨2^28, by norm_num⟩
  simpa only [he.neg_pow] using h

end M31FiberLift
