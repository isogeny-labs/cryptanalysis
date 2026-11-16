import Mathlib.Data.Finset.Card
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace XedniFamilyAdmission

/-- Integer translation of the fixed short Weierstrass polynomial. -/
theorem translated_polynomial (a x : ℤ) :
    (x + a) ^ 3 - 3 * a * (x + a) ^ 2 +
      (3 * a ^ 2 - 1) * (x + a) + (-a ^ 3 + a - 2) =
      x ^ 3 - x - 2 := by
  ring

theorem translated_coefficients_reduce {p : ℕ} (a : ℤ)
    (ha : (a : ZMod p) = 0) :
    ((-3 * a : ℤ) : ZMod p) = 0 ∧
    ((3 * a ^ 2 - 1 : ℤ) : ZMod p) = -1 ∧
    ((-a ^ 3 + a - 2 : ℤ) : ZMod p) = -2 := by
  simp [ha]

theorem multiple_shift_reduces (p : ℕ) (j : ℤ) :
    ((j * (p : ℤ) : ℤ) : ZMod p) = 0 := by
  simp

/-- Selected ordered pairs admitted by a finite family of reduction images
are bounded by the sum of the squared image sizes. -/
theorem family_pair_capacity {ι β : Type*} [DecidableEq ι] [DecidableEq β]
    (models : Finset ι) (image : ι → Finset β) (A : Finset (β × β))
    (hadmit : ∀ pair ∈ A, ∃ i ∈ models,
      pair.1 ∈ image i ∧ pair.2 ∈ image i) :
    A.card ≤ ∑ i ∈ models, (image i).card ^ 2 := by
  let cover := models.biUnion (fun i => (image i).product (image i))
  have hsub : A ⊆ cover := by
    intro pair hp
    obtain ⟨i, hi, hfirst, hsecond⟩ := hadmit pair hp
    exact Finset.mem_biUnion.mpr ⟨i, hi,
      Finset.mem_product.mpr ⟨hfirst, hsecond⟩⟩
  have hcard := Finset.card_le_card hsub
  have hsum : cover.card ≤
      ∑ i ∈ models, ((image i).product (image i)).card := by
    dsimp [cover]
    exact Finset.card_biUnion_le
  calc
    A.card ≤ cover.card := hcard
    _ ≤ ∑ i ∈ models, ((image i).product (image i)).card := hsum
    _ = ∑ i ∈ models, (image i).card ^ 2 := by
      simp [pow_two]

#print axioms family_pair_capacity
#print axioms translated_polynomial
#print axioms translated_coefficients_reduce
#print axioms multiple_shift_reduces

end XedniFamilyAdmission
