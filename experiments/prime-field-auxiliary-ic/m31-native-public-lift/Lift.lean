import Mathlib.FieldTheory.Finite.Basic
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.Tactic

namespace PublicLift
abbrev F := ZMod 2147483647
instance : Fact (Nat.Prime 2147483647) := ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def squares (x : F) : Nat → F
  | 0 => x
  | n+1 => let y := squares x n; y*y

theorem exponent (x : F) (n : Nat) : squares x n = x^(2^n) := by
  induction n with
  | zero => simp [squares]
  | succ n ih => simp only [squares, ih, pow_succ 2 n, pow_mul, pow_two]

theorem accepts_iff (x : F) : (squares x 29)^2 = x ↔ ∃ z : F, z^2 = x := by
  refine ⟨fun h => ⟨_, h⟩, ?_⟩
  rintro ⟨z,rfl⟩
  rw [exponent]
  calc
    ((z^2)^(2^29 : Nat))^2 = z^((2*(2^29 : Nat))*2) := by simp only [pow_mul]
    _ = z^((2147483647 : Nat)+1) := congrArg (fun k : Nat => z^k) (by decide)
    _ = z^2 := by rw [pow_succ, ZMod.pow_card, pow_two]

/-- Choose the root whose canonical residue is smaller. -/
def smaller (y : F) : F := if y.val ≤ (-y).val then y else -y

theorem smaller_square (y : F) : (smaller y)^2 = y^2 := by
  unfold smaller
  split <;> simp

theorem smaller_neg (y : F) : smaller (-y) = smaller y := by
  unfold smaller
  simp only [neg_neg]
  split_ifs with h k k
  · exact ZMod.val_injective _ (Nat.le_antisymm h k)
  · rfl
  · rfl
  · omega

theorem smaller_val (y : F) : (smaller y).val = min y.val (2147483647 - y.val) := by
  by_cases zero : y = 0
  · subst y
    simp [smaller]
  · unfold smaller
    rw [ZMod.neg_val, if_neg zero]
    split_ifs with h
    · exact (min_eq_left h).symm
    · rw [ZMod.neg_val, if_neg zero, min_eq_right (by omega)]

theorem canonical_lift (rhs y : F) (hy : y^2 = rhs) :
    smaller (squares rhs 29) = smaller y := by
  have h := (accepts_iff rhs).2 ⟨y, hy⟩
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp (h.trans hy.symm) with eq | eq
  · rw [eq]
  · rw [eq, smaller_neg]

#print axioms canonical_lift
end PublicLift
