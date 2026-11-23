import Mathlib.NumberTheory.LegendreSymbol.Basic

namespace M31BitWitnesses
abbrev p := 2147483647
abbrev F := ZMod p
instance : Fact (Nat.Prime p) := ⟨by native_decide⟩

def squareBit (v : F) : Bool := decide (v = 0 ∨ v ^ (p/2) = 1)

theorem squareBit_spec (v : F) : squareBit v = true ↔ IsSquare v := by
  by_cases h : v = 0
  · subst v; simp [squareBit]
  · simp [squareBit, h, ZMod.euler_criterion p h]

def aux (x : Nat) : Bool :=
  decide (x < p) && !squareBit (x : F) && squareBit ((x : F)^3 + x)

def label (x : Nat) : Bool := squareBit ((x : F)^3 + 2*x + 14)

/-- Pack the retained bits in order, deleting bit i. -/
def eraseBit (i x : Nat) := (x / 2^(i+1)) * 2^i + x % 2^i

private def starts : Array Nat := #[62, 20, 24, 20, 12, 131, 24, 28, 39, 24, 40, 39, 39, 3, 28, 88, 44, 22, 53, 82, 22, 28, 40, 24, 44, 45, 28, 22, 20, 22, 28]
private def left (i : Fin 31) := starts[i.val]!
private def right (i : Fin 31) := (left i) ^^^ (2^i.val)

theorem witnesses : ∀ i : Fin 31,
    aux (left i) = true ∧ aux (right i) = true ∧
    eraseBit i.val (left i) = eraseBit i.val (right i) ∧
    label (left i) ≠ label (right i) := by native_decide

theorem no_exact_lookup (i : Fin 31) (lookup : Nat → Bool) :
    ¬ ∀ x, aux x = true → lookup (eraseBit i.val x) = label x := by
  intro h
  obtain ⟨hl, hr, he, hn⟩ := witnesses i
  exact hn ((h _ hl).symm.trans ((congrArg lookup he).trans (h _ hr)))

end M31BitWitnesses
