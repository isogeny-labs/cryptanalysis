import CubicPairFold
import Mathlib.Data.ZMod.Basic

namespace M31FusedChord
open M31CubicPairFold

abbrev F := ZMod p

/-- Applies to the x bias 2p-a-b and the y bias p-y. -/
theorem word_bounds {u v bias : ℕ} (hu : u < p) (hv : v < p) (hb : bias ≤ 2*p) :
    u*v+bias ≤ p^2+1 ∧ u*v+bias < 2^64 ∧
    (u*v+bias) % (p+1) + (u*v+bias) / (p+1) < 2^32 ∧
    fold (u*v+bias) = (u*v+bias) % p := by
  have h := Nat.mul_le_mul (show u ≤ p-1 by omega) (show v ≤ p-1 by omega)
  have bound : u*v+bias ≤ p^2+1 := by unfold p at *; omega
  exact ⟨bound, reduce _ (by omega)⟩

theorem bit_parts (t : ℕ) : (t &&& (2^31-1)) + (t >>> 31) = t % (p+1) + t / (p+1) := by
  rw [Nat.and_two_pow_sub_one_eq_mod, Nat.shiftRight_eq_div_pow]

theorem x_chord {s a b : ℕ} (hs : s < p) (ha : a < p) (hb : b < p) :
    b ≤ 2*p-a ∧ (fold (s*s + (2*p-a-b)) : F) = (s : F)*(s : F)-a-b := by
  have h₁ : a ≤ 2*p := by omega
  have h₂ : b ≤ 2*p-a := by omega
  refine ⟨h₂, ?_⟩
  rw [(word_bounds hs hs (show 2*p-a-b ≤ 2*p by omega)).2.2.2]
  simp [ZMod.natCast_mod, Nat.cast_sub h₁, Nat.cast_sub h₂]
  rw [show (2147483647 : F) = 0 by decide]
  ring

/-- d is the canonical difference used by the scalar y formula. -/
theorem y_chord {s d y : ℕ} (hs : s < p) (hd : d < p) (hy : y < p) :
    y ≤ p ∧ (fold (s*d+(p-y)) : F) = (s : F)*(d : F)-y := by
  refine ⟨hy.le, ?_⟩
  rw [(word_bounds hs hd (show p-y ≤ 2*p by omega)).2.2.2]
  simp [ZMod.natCast_mod, Nat.cast_sub hy.le, sub_eq_add_neg]
  decide

#print axioms word_bounds
#print axioms x_chord
#print axioms y_chord
end M31FusedChord
