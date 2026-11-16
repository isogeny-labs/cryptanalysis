import FiniteFamilyCoverage
import Mathlib.Tactic


namespace XedniCoefficientOptimization

/-- Greedy family fixed by the calibration protocol. -/
def selectedInteger : Finset (ℤ × ℤ) :=
  {(1,-6), (2,-1), (6,5), (5,4), (6,1), (5,3), (4,-5),
   (6,-1), (5,-1), (6,-5), (1,5), (4,-1), (4,1)}

theorem selected_integer_card : selectedInteger.card = 13 := by decide

theorem selected_integer_effective :
    ∀ c ∈ selectedInteger, c.1 + c.2 ≠ 0 := by decide

variable {K : Type*} [Field K] [DecidableEq K]

/-- Reduction of the selected integer family by a specified ring map. -/
def selectedField (f : ℤ →+* K) : Finset (K × K) :=
  selectedInteger.image (fun c => (f c.1, f c.2))

theorem selected_field_card_le (f : ℤ →+* K) :
    (selectedField f).card ≤ 13 := by
  calc
    (selectedField f).card ≤ selectedInteger.card := Finset.card_image_le
    _ = 13 := selected_integer_card

theorem selected_coverage_bound (f : ℤ →+* K) (T : Finset K) :
    (XedniFiniteFamilyCoverage.winners (selectedField f) T).card ≤ 13 * T.card := by
  exact (XedniFiniteFamilyCoverage.card_winners_le (selectedField f) T).trans
    (Nat.mul_le_mul (selected_field_card_le f) (le_refl T.card))

#print axioms selected_integer_card
#print axioms selected_integer_effective
#print axioms selected_field_card_le
#print axioms selected_coverage_bound

end XedniCoefficientOptimization
