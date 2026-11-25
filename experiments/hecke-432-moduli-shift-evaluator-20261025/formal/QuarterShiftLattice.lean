import Mathlib.Tactic.Ring

/-! Exact equality of the two lattices behind the quarter-shift quotient. -/

namespace QuarterShiftLattice

def bridge (s : ℤ) (x y : ℚ) : Prop :=
  ∃ a b c : ℤ,
    x = (a : ℚ) + (s : ℚ) * (c : ℚ) / 4 ∧
    y = ((4 * b + c : ℤ) : ℚ)

def shifted (s : ℤ) (x y : ℚ) : Prop :=
  ∃ a c : ℤ,
    x = (a : ℚ) + (s : ℚ) * (c : ℚ) / 4 ∧
    y = (c : ℚ)

theorem bridge_iff_shifted (s : ℤ) (x y : ℚ) :
    bridge s x y ↔ shifted s x y := by
  constructor
  · rintro ⟨a, b, c, hx, hy⟩
    refine ⟨a - s * b, 4 * b + c, ?_, ?_⟩
    · rw [hx]
      push_cast
      ring
    · exact hy
  · rintro ⟨a, c, hx, hy⟩
    refine ⟨a, 0, c, ?_, ?_⟩
    · exact hx
    · simpa using hy

theorem generator_change (u sign k : ℤ) (h : u = sign + 4 * k) :
    (u : ℚ) / 4 = (sign : ℚ) / 4 + k := by
  rw [h]
  push_cast
  ring

#print axioms bridge_iff_shifted
#print axioms generator_change

end QuarterShiftLattice
