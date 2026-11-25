import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic

namespace M31Ordinate

abbrev p := 2147483647
abbrev F := ZMod p
local instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def root (v : F) := v^(2^29 : ℕ)
def canonical (y : F) := min y.val (p-y.val)
def encode (v : F) := if (root v)^2 = v then canonical (root v) else p

private theorem test (v : F) : (root v)^2 = v ↔ IsSquare v := by
  constructor
  · intro h
    exact ⟨_, by simpa [pow_two] using h.symm⟩
  · rintro ⟨y,rfl⟩
    unfold root
    rw [← sq, ← pow_mul, ← pow_mul]
    change y^(2147483647+1 : ℕ) = y^2
    rw [pow_succ, ZMod.pow_card, pow_two]

private theorem canonical_neg (y : F) : canonical (-y) = canonical y := by
  by_cases h : y = 0
  · simp [h]
  · unfold canonical
    simp only [ZMod.neg_val, h, ↓reduceIte]
    rw [ Nat.sub_sub_self (Nat.le_of_lt y.val_lt), min_comm]

/-- The same smaller ordinate is returned for either square root. -/
theorem success (y : F) : encode (y^2) = canonical y := by
  have h := (test (y^2)).mpr ⟨y, pow_two y⟩
  simp only [encode, h, ↓reduceIte]
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp h with e | e
  · rw [e]
  · rw [e, canonical_neg]

/-- The reserved word is emitted exactly for a nonsquare. -/
theorem sentinel (v : F) : encode v = p ↔ ¬ IsSquare v := by
  by_cases h : IsSquare v
  · simp only [encode, (test v).mpr h, ↓reduceIte]
    exact iff_of_false (Nat.ne_of_lt (lt_of_le_of_lt (min_le_left _ _) (root v).val_lt)) (not_not_intro h)
  · simp [encode, (test v).not.mpr h, h]

end M31Ordinate
#print axioms M31Ordinate.success
#print axioms M31Ordinate.sentinel
