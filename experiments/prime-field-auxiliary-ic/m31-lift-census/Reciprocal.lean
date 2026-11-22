import Mathlib

namespace M31Reciprocal

theorem liftProduct {F : Type*} [Field F] (x : F) (h : x ≠ 0) :
    (x^3+2*x+14)*(x⁻¹^3+2*x⁻¹+14) =
    14*(x+x⁻¹)^3+2*(x+x⁻¹)^2-14*(x+x⁻¹)+197 := by
  field_simp
  ring

theorem selector {F : Type*} [Field F] (x : F) (h : x ≠ 0) :
    x*(x+x⁻¹-2)=(x-1)^2 ∧ x*(x+x⁻¹+2)=(x+1)^2 ∧
    x*(x+x⁻¹)=x^2+1 := by
  refine ⟨?_, ?_, ?_⟩ <;> field_simp <;> ring

/-- From a square root of the discriminant, recover both reciprocal roots. -/
theorem recoverPair {F : Type*} [Field F] (h : (2 : F) ≠ 0)
    (t d : F) (hd : d^2 = (t-2)*(t+2)) :
    ((t+d)/2)*((t-d)/2) = 1 ∧ (t+d)/2+(t-d)/2 = t := by
  constructor
  · field_simp
    linear_combination -hd
  · field_simp
    ring

def product {R : Type*} [CommRing R] (t : R) := 14*t^3+2*t^2-14*t+197
def delta {R : Type*} [CommRing R] (t : R) := 42*t^2+46*t+2

theorem forwardDifferences {R : Type*} [CommRing R] (t : R) :
    product (t+1) = product t + delta t ∧
    delta (t+1) = delta t + (84*t+88) := by
  unfold product delta
  constructor <;> ring

/-- Given the census totals, the conditional lift fraction falls below the
marginal by less than one part per hundred thousand. -/
theorem conditionalGap :
    0 < (268414441 / 536870912 : ℚ) - 134194542 / 268414441 ∧
    (268414441 / 536870912 : ℚ) - 134194542 / 268414441 < 1 / 100000 := by
  norm_num

/-- In each observed partner state, failures form the majority. The
counts here use both orientations of every reciprocal edge. -/
theorem majorityByPartner :
    2 * 67097271 < 134219899 ∧ 134219899 < 2 * 67118286 := by
  decide

end M31Reciprocal
