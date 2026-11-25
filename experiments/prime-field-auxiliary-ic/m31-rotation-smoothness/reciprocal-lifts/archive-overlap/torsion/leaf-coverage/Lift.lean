import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic
import Mathlib.Tactic.ReduceModChar

namespace LeafCoverage

abbrev F := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def hit (x : F) : Prop :=
  x + x⁻¹ - 2 = 1632618911 ∨ x + x⁻¹ - 2 = 1700263893

private theorem children (x a b u : F) (hx : x ≠ 0) (hs : a+b = u+2)
    (hp : a*b = 1) : x+x⁻¹-2 = u ↔ x = a ∨ x = b := by
  have id : (x+x⁻¹-2-u)*x = (x-a)*(x-b) := by
    calc
      _ = x^2 - (u+2)*x + 1 := by field_simp; ring
      _ = (x-a)*(x-b) := by rw [← hs, ← hp]; ring
  have iff0 : (x+x⁻¹-2-u)*x = 0 ↔ (x-a)*(x-b) = 0 := by rw [id]
  simpa only [mul_eq_zero, hx, or_false, sub_eq_zero] using iff0

theorem four_leaves (x : F) (hx : x ≠ 0) : hit x ↔
    (x = 98625645 ∨ x = 1533993268) ∨ (x = 80168778 ∨ x = 1620095117) := by
  unfold hit
  rw [children x 98625645 1533993268 1632618911 hx (by decide) (by decide),
      children x 80168778 1620095117 1700263893 hx (by decide) (by decide)]

def rhs (x : F) := x^3+2*x+14

private theorem nonsquare (a : F) (hn : a ≠ 0) (h : a^1073741823 = -1) :
    ¬ IsSquare a := by
  intro sq
  have h1 := (FiniteField.isSquare_iff (by rw [ZMod.ringChar_zmod_n]; decide : ringChar F ≠ 2) hn).mp sq
  have card : Fintype.card F = 2147483647 := ZMod.card _
  rw [card] at h1
  change a^1073741823 = 1 at h1
  exact (by decide : (-1:F) ≠ 1) (h.symm.trans h1)

theorem lifted_leaf (x : F) (hx : x ≠ 0) (h : hit x) :
    IsSquare (rhs x) ↔ x = 98625645 := by
  rcases (four_leaves x hx).mp h with (rfl|rfl)|(rfl|rfl)
  · exact iff_of_true ⟨439352624, by decide⟩ rfl
  all_goals
    apply iff_of_false (nonsquare _ (by decide) ?_) (by decide)
    unfold rhs F
    reduce_mod_char

end LeafCoverage
#print axioms LeafCoverage.lifted_leaf
