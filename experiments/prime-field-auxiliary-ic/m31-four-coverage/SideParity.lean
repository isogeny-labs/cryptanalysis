import FiberLift
import Mathlib.NumberTheory.LegendreSymbol.JacobiSymbol

namespace M31SideParity

abbrev p := 2147483647
abbrev F := ZMod p
private instance : Fact (Nat.Prime p) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

theorem reciprocity_label (a : ℤ) :
    jacobiSym a p ≠ -1 ↔ ∃ y : F, y^2 = a := by
  rw [← jacobiSym.legendreSym.to_jacobiSym, ne_eq, legendreSym.eq_neg_one_iff, not_not]
  simp only [IsSquare, pow_two, eq_comm]

-- Reduce a signed representative from [-p,p) by adding p if negative.
-- Since p is odd, doing so toggles the low bit.
theorem signed_parity (t : Int) (lo : -(p:Int) ≤ t) (hi : t < (p:Int)) :
    (t % p) % 2 = (t + (if t < 0 then 1 else 0)) % 2 := by
  unfold p at *
  split <;> omega

theorem parity_label (a : F) :
    (((a^(2^29 : Nat))^2).val % 2 = a.val % 2) ↔ ∃ y : F, y^2 = a := by
  have exactLabel := M31FiberLift.lift_exact (fun _ : Unit => a) ()
  rw [M31FiberLift.lane_power] at exactLabel
  change ((a^(2^29 : Nat))^2 = a ↔ _) at exactLabel
  rw [← exactLabel]
  constructor
  · intro same
    rcases (M31FiberLift.twist_split a).1 with h | h
    · exact h
    · by_cases zero : a = 0
      · simp [zero]
      · let _ : NeZero a := ⟨zero⟩
        rw [h, ZMod.val_neg_of_ne_zero] at same
        have bound := a.val_lt
        change a.val < 2147483647 at bound
        change (2147483647 - a.val) % 2 = a.val % 2 at same
        omega
  · intro eq
    rw [eq]

end M31SideParity
