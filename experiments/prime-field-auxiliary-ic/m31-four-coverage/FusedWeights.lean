import Mathlib.Tactic

namespace M31FusedWeights

abbrev p : Int := 2147483647
abbrev h : Int := 1073741823
def center (x : Int) := if x > h then x-p else x
def biased (u b v a : Int) := center u * center b - center v * center a + p * 1073741824
def fold (z : Int) := z / 2147483648 + z % 2147483648
def finish (x : Int) := if x ≥ p then x-p else x

private theorem centered (x : Int) (hx : x ∈ Set.Ico 0 p) :
    -h ≤ center x ∧ center x ≤ h := by
  obtain ⟨lo,hi⟩ := hx
  unfold center h p at *
  split <;> omega

private theorem product_bound (x y : Int) (hx : -h ≤ x ∧ x ≤ h) (hy : -h ≤ y ∧ y ≤ h) :
    -(h*h) ≤ x*y ∧ x*y ≤ h*h := by
  have h₀ : 0 ≤ h := by decide
  have a := mul_le_mul_of_nonneg_left hy.2 (sub_nonneg.mpr hx.2)
  have b := mul_le_mul_of_nonneg_left hy.1 (sub_nonneg.mpr hx.2)
  have c := mul_le_mul_of_nonneg_left hy.2 (by omega : 0 ≤ x+h)
  have d := mul_le_mul_of_nonneg_left hy.1 (by omega : 0 ≤ x+h)
  constructor <;> nlinarith [mul_nonneg h₀ (sub_nonneg.mpr hy.2),
    mul_nonneg h₀ (by omega : 0 ≤ y+h)]

theorem biased_bounds (u b v a : Int) (hu : u ∈ Set.Ico 0 p) (hb : b ∈ Set.Ico 0 p)
    (hv : v ∈ Set.Ico 0 p) (ha : a ∈ Set.Ico 0 p) :
    0 ≤ biased u b v a ∧ biased u b v a < p^2 := by
  have x := product_bound _ _ (centered _ hu) (centered _ hb)
  have y := product_bound _ _ (centered _ hv) (centered _ ha)
  unfold biased h p at *
  omega

private theorem center_equiv (x : Int) : center x ≡ x [ZMOD p] := by
  unfold center Int.ModEq p
  split <;> omega

theorem exact (u b v a : Int) (hu : u ∈ Set.Ico 0 p) (hb : b ∈ Set.Ico 0 p)
    (hv : v ∈ Set.Ico 0 p) (ha : a ∈ Set.Ico 0 p) :
    finish (fold (biased u b v a)) = (u*b-v*a) % p := by
  have bounds := biased_bounds u b v a hu hb hv ha
  have eqv := ((center_equiv u).mul (center_equiv b)).sub ((center_equiv v).mul (center_equiv a))
  have red : finish (fold (biased u b v a)) = biased u b v a % p := by
    generalize biased u b v a = z at *
    unfold finish fold p at *
    split <;> omega
  rw [red]
  unfold biased Int.ModEq p at *
  omega

end M31FusedWeights
