import Mathlib.Tactic

namespace ControlSixRows

/-- Sum of the six weighted signed rows from control basis 0, walk seed 2.
The coordinate index is the public basis index. -/
def column {F : Type*} [Field F] (a b c d e f : F) : ℕ → F
  | 0 => b + e + f
  | 6 => d - e
  | 7 => a
  | 10 => c
  | 17 => -d - f
  | 25 => c
  | 28 => -a
  | 31 => -b
  | _ => 0

/-- In arrival order, the complete coefficient kernel is (0,0,0,t,t,-t). -/
theorem kernel_iff {F : Type*} [Field F] (a b c d e f : F) :
    (∀ j, column a b c d e f j = 0) ↔
      a = 0 ∧ b = 0 ∧ c = 0 ∧ e = d ∧ f = -d := by
  constructor
  · intro h
    have ha := h 7
    have hb := h 31
    have hc := h 10
    have he := h 6
    have hf := h 17
    simp [column] at ha hb hc he hf
    exact ⟨ha, hb, hc, (sub_eq_zero.mp he).symm, (sub_eq_zero.mp hf).symm⟩
  · rintro ⟨rfl, rfl, rfl, rfl, rfl⟩ j
    unfold column
    split <;> simp

#print axioms kernel_iff
end ControlSixRows
