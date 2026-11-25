import CycleTrace

namespace CycleFloor
open PointTriangles Matrix CycleTrace

def degree (i : P) : ℤ := ∑ l : L, if onLine i l then 1 else 0
def adjacent (i j : P) : ℤ := if i ≠ j ∧ (joinLine i j).isSome then 1 else 0
def neighbors (i : P) : ℤ := ∑ j, adjacent i j

private theorem fixed :
    (∑ i, degree i) = 544 ∧ (∑ i, neighbors i) = 3808 ∧
      (∑ i, neighbors i * degree i) = 32480 := by native_decide

private theorem entry_sq (f : P → L → Bool) (i : P) (l : L) :
    SignParity.signed f i l ^ 2 = if onLine i l then 1 else 0 := by
  unfold SignParity.signed SignParity.unsigned onLine
  split <;> split <;> decide

attribute [local irreducible] joinLine

theorem floor_bound (f : P → L → Bool) :
    13440 ≤ TriangleBudget.positive (SignParity.signed f) := by
  let H := SignParity.signed f
  let B := off H
  let D := Matrix.diagonal degree
  have hz (i l) (h : onLine i l = false) : H i l = 0 := by
    simp [H, SignParity.signed, SignParity.unsigned, onLine] at h ⊢
    split <;> simp_all
  have symm : B.transpose = B := by
    ext i j
    by_cases h : i = j
    · subst j; rfl
    · simp only [B, off, transpose_apply, if_neg h, if_neg (Ne.symm h), mul_apply]
      apply Finset.sum_congr rfl
      intro _ _
      apply mul_comm
  have diagG (i : P) : (H * H.transpose) i i = degree i := by
    simp only [mul_apply, transpose_apply, degree, ← pow_two, H, entry_sq]
  have gram : H * H.transpose = B + D := by
    ext i j
    by_cases h : i = j
    · subst j; simp [B, off, D, diagG]
    · simp [B, off, D, h]
  have sq (i j : P) : B i j ^ 2 = adjacent i j := by
    by_cases h : i = j
    · subst j; simp [B, off, adjacent]
    · simp only [B, off, overlap H hz h, adjacent, h]
      cases he : joinLine i j with
      | none => simp
      | some l =>
        obtain ⟨hi,hj⟩ := (join_exact i j h l).mp he
        simp [H, mul_pow, entry_sq, hi, hj, h]
  have diagB (i : P) : (B*B) i i = neighbors i := by
    rw [mul_apply]
    apply Finset.sum_congr rfl
    intro j _
    have e : B j i = B i j := congrFun (congrFun symm i) j
    rw [e, ← pow_two, sq]
  have shift : B - (7 : ℤ) • 1 = SignParity.shifted H := by
    ext i j
    simp only [Matrix.sub_apply, Matrix.smul_apply, smul_eq_mul]
    by_cases h : i = j
    · subst j; simp [B, off, SignParity.shifted]
    · simp [B, off, SignParity.shifted, h]
  have E := SignTrace.energy H B D symm gram
  dsimp only at E
  rw [shift] at E
  have bound := CycleTrace.residual_energy f
  change 1792 ≤ ((SignParity.shifted H * H) * (SignParity.shifted H * H).transpose).trace at bound
  have cubic := CycleTrace.cubic f
  change (B*B*B).trace = _ at cubic
  have bb : (B*B).trace = 3808 := by simpa only [trace, Matrix.diag, diagB] using fixed.2.1
  have bbd : (B*B*D).trace = 32480 := by
    simpa only [trace, Matrix.diag, D, Matrix.mul_diagonal, diagB] using fixed.2.2
  have bd : (B*D).trace = 0 := by simp [D, trace, Matrix.diag, Matrix.mul_diagonal, B, off]
  have b : B.trace = 0 := by simp [B, off, trace, Matrix.diag]
  have dd : D.trace = 544 := by simpa [D] using fixed.1
  rw [cubic, bb, bbd, bd, b, dd] at E
  omega

#print axioms floor_bound
end CycleFloor
