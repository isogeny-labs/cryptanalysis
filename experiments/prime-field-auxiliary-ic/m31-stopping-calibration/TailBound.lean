import Mathlib

namespace M31Tail
def hit : ℚ := 578/2147505293
def q : ℕ := 19300166
-- C(n,j) * hit^j, via a short product even for a large n.
def term (n : ℕ) : ℕ → ℚ
  | 0 => 1
  | j+1 => term n j * ((n-j : ℕ) : ℚ) * hit / (j+1 : ℕ)

def denominator : ℚ := ((List.range 17).map (term (q-14))).sum
def ratio : ℚ := ((q-14 : ℕ) : ℚ) * hit / (15*(1-hit))
theorem majorantValue :
    0 < denominator ∧ 0 ≤ ratio ∧ ratio < 1 ∧
    term q 14 / denominator / (1-ratio) < 1014 / 1000000 := by native_decide
end M31Tail
