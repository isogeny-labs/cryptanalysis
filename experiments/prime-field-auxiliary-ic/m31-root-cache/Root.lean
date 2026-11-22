import Mathlib
namespace M31Root
abbrev F := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) := ⟨by native_decide⟩
theorem exactRoot (v : F) : (v^(2^29 : ℕ))^2 = v ↔ IsSquare v := by
  constructor
  · intro h
    exact ⟨_, by simpa [pow_two] using h.symm⟩
  · rintro ⟨y,rfl⟩
    rw [← sq, ← pow_mul, ← pow_mul]
    change y^(2147483647+1 : ℕ) = y^2
    rw [pow_succ, ZMod.pow_card, pow_two]
theorem reflected (x : F) : (-x)^3+2*(-x)+14 = 28-(x^3+2*x+14) := by ring
end M31Root
