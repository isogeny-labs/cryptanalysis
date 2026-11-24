import TriangleBudget
import SignParity
import SignTrace

namespace CycleTrace
open PointTriangles TriangleBudget Matrix

/-- The off-diagonal signed Gram matrix. -/
def off (H : Matrix P L ℤ) : Matrix P P ℤ := fun i j =>
  if i = j then 0 else (H * H.transpose) i j

private theorem symmetric (H : Matrix P L ℤ) (i j : P) : off H i j = off H j i := by
  by_cases h : i = j
  · subst j; rfl
  · simp only [off, if_neg h, if_neg (Ne.symm h), Matrix.mul_apply, Matrix.transpose_apply]
    apply Finset.sum_congr rfl
    intro _ _
    apply mul_comm

attribute [local irreducible] classify joinLine

theorem cubic (f : P → L → Bool) :
    let H := SignParity.signed f
    let B := off H
    (B * B * B).trace = 12 * (positive H : ℤ) - 165312 := by
  let H := SignParity.signed f
  change (off H * off H * off H).trace = _
  have outside (a : P) (l : L) (h : onLine a l = false) : H a l = 0 := by
    simp [H, SignParity.signed, SignParity.unsigned, onLine] at h ⊢
    split <;> simp_all
  have unit (a : P) (l : L) (h : onLine a l = true) : H a l ^ 2 = 1 := by
    simp [H, SignParity.signed, SignParity.unsigned, onLine] at h ⊢
    exact h
  have bridge : TriangleTrace.total (TriangleTrace.increasing (off H)) =
      ∑ t ∈ Finset.univ.filter (fun t : Triple => t.1 < t.2.1 ∧ t.2.1 < t.2.2), weight H t := by
    simp only [TriangleTrace.total, Finset.sum_filter, Fintype.sum_prod_type]
    apply Finset.sum_congr rfl
    intro a _
    apply Finset.sum_congr rfl
    intro b _
    apply Finset.sum_congr rfl
    intro c _
    by_cases h : a < b ∧ b < c
    · simp [TriangleTrace.increasing, h, off, weight, h.1.ne, h.2.ne, (h.1.trans h.2).ne.symm]
    · simp [TriangleTrace.increasing, h]
  rw [TriangleTrace.cubic_trace _ (symmetric H) (by simp [off]), bridge, ordered_budget H outside unit]
  ring

/-- The Frobenius energy of the actual residual is bounded below for every signing. -/
theorem residual_energy (f : P → L → Bool) :
    let R := SignParity.residual (SignParity.signed f)
    1792 ≤ (R * R.transpose).trace := by
  let R := SignParity.residual (SignParity.signed f)
  have h := SignTrace.parity_floor (Finset.univ : Finset (P × L)) (fun t => R t.1 t.2)
  change ((SignParity.oddCount (SignParity.signed f) : ℕ) : ℤ) ≤ _ at h
  rw [SignParity.signed_count] at h
  simpa only [Matrix.trace, Matrix.diag, Matrix.mul_apply, Matrix.transpose_apply,
    Fintype.sum_prod_type, pow_two, R] using h

#print axioms cubic
#print axioms residual_energy
end CycleTrace
