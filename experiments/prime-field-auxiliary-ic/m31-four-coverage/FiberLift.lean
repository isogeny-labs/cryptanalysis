import Mathlib.FieldTheory.Finite.Basic
import Mathlib.NumberTheory.LucasLehmer
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

end M31FiberLift
