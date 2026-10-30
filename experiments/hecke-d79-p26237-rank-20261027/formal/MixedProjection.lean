module

public import Init

namespace MixedProjection

public def allowed (x : Fin 5) : Prop := x = 0 ∨ x = 1 ∨ x = 4

public theorem triple_zero_characterization :
    ∀ a b c : Fin 5, allowed a → allowed b → allowed c →
      (a + b + c = 0 ↔
        (a = 0 ∧ b = 0 ∧ c = 0) ∨
        (a = 0 ∧ ((b = 1 ∧ c = 4) ∨ (b = 4 ∧ c = 1))) ∨
        (b = 0 ∧ ((a = 1 ∧ c = 4) ∨ (a = 4 ∧ c = 1))) ∨
        (c = 0 ∧ ((a = 1 ∧ b = 4) ∨ (a = 4 ∧ b = 1)))) := by
  intro a b c ha hb hc
  change a = 0 ∨ a = 1 ∨ a = 4 at ha
  change b = 0 ∨ b = 1 ∨ b = 4 at hb
  change c = 0 ∨ c = 1 ∨ c = 4 at hc
  rcases ha with ha | ha | ha <;> rcases hb with hb | hb | hb <;>
    rcases hc with hc | hc | hc <;> simp [ha, hb, hc]

public theorem frozen_support_three_count_arithmetic :
    4 * 1140 + 2 * 20 * 190 = 12160 := by decide

public theorem frozen_support_four_count_arithmetic :
    8 * 4845 + 4 * 36100 + 3 * 4845 = 197695 := by decide

#print axioms triple_zero_characterization
#print axioms frozen_support_three_count_arithmetic
#print axioms frozen_support_four_count_arithmetic

end MixedProjection
