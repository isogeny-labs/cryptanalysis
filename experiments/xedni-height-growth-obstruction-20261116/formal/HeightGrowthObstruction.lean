import Mathlib

/-!
Rank deficiency alone does not bound the coefficients of a relation: for
an infinite-order point `P`, the pair `P, nP` has a relation whose first
nonzero coefficient has magnitude at least `n`.
-/

namespace XedniHeightGrowthObstruction

/-- The integer model of the coefficient lower bound. -/
theorem integer_pair_relation_lower_bound
    (n : ℕ) (a b : ℤ)
    (hrel : a + b * (n : ℤ) = 0)
    (hnontrivial : a ≠ 0 ∨ b ≠ 0) :
    n ≤ a.natAbs := by
  have hb : b ≠ 0 := by
    intro hb
    subst b
    simp only [zero_mul, add_zero] at hrel
    rcases hnontrivial with ha | hb
    · exact ha hrel
    · exact hb rfl
  have ha : a = -(b * (n : ℤ)) := by omega
  have hbpos : 0 < b.natAbs := Int.natAbs_pos.mpr hb
  have hmul : n ≤ b.natAbs * n := by
    simpa using Nat.mul_le_mul_right n (Nat.succ_le_iff.mpr hbpos)
  rw [ha, Int.natAbs_neg, Int.natAbs_mul, Int.natAbs_natCast]
  exact hmul

/-- If `P` has infinite order, every nontrivial relation among `P` and
`nP` needs a coefficient of magnitude at least `n`. -/
theorem group_pair_relation_lower_bound
    {H : Type*} [AddCommGroup H] (P : H)
    (hinfinite : ∀ z : ℤ, z • P = 0 → z = 0)
    (n : ℕ) (a b : ℤ)
    (hrel : a • P + b • ((n : ℤ) • P) = 0)
    (hnontrivial : a ≠ 0 ∨ b ≠ 0) :
    n ≤ a.natAbs := by
  have hz : (a + b * (n : ℤ)) • P = 0 := by
    simpa only [add_smul, mul_smul] using hrel
  exact integer_pair_relation_lower_bound n a b (hinfinite _ hz) hnontrivial

/-- The pair has a relation attaining the lower bound. -/
theorem group_pair_relation_attained
    {H : Type*} [AddCommGroup H] (P : H) (n : ℕ) :
    (-(n : ℤ)) • P + (1 : ℤ) • ((n : ℤ) • P) = 0 := by
  simp

/-- With `B/δ=n`, `r=2`, `d=T=1`, the finite packing test becomes
`1+4nK < (2K+1)^2`. For positive `K` it holds exactly when `K≥n`. -/
theorem packing_criterion_iff
    (n K : ℕ) (hK : 0 < K) :
    1 + 4 * n * K < (2 * K + 1) ^ 2 ↔ n ≤ K := by
  constructor
  · intro h
    by_contra hnot
    have hn : K + 1 ≤ n := by omega
    have hmul := Nat.mul_le_mul_right (4 * K) hn
    nlinarith
  · intro hn
    have hmul := Nat.mul_le_mul_right (4 * K) hn
    nlinarith

/-- The coefficient-box difference radius `2K` cannot hold a relation
for the pair `P,nP` when `2K<n`. -/
theorem no_relation_below_half
    {H : Type*} [AddCommGroup H] (P : H)
    (hinfinite : ∀ z : ℤ, z • P = 0 → z = 0)
    (n K : ℕ) (hsmall : 2 * K < n) (a b : ℤ)
    (ha : a.natAbs ≤ 2 * K)
    (hrel : a • P + b • ((n : ℤ) • P) = 0)
    (hnontrivial : a ≠ 0 ∨ b ≠ 0) : False := by
  have h := group_pair_relation_lower_bound P hinfinite n a b hrel hnontrivial
  omega

/-- For a positive coefficient-box radius, the scalar map on the pair
`(1,n)` collides exactly when the box can contain the difference `(-n,1)`. -/
theorem integer_pair_box_collision_iff
    (n K : ℕ) (hK : 0 < K) :
    (∃ a₁ b₁ a₂ b₂ : ℤ,
      a₁.natAbs ≤ K ∧ b₁.natAbs ≤ K ∧
      a₂.natAbs ≤ K ∧ b₂.natAbs ≤ K ∧
      (a₁, b₁) ≠ (a₂, b₂) ∧
      a₁ + b₁ * (n : ℤ) = a₂ + b₂ * (n : ℤ)) ↔ n ≤ 2 * K := by
  constructor
  · rintro ⟨a₁, b₁, a₂, b₂, ha₁, hb₁, ha₂, hb₂, hne, heq⟩
    have hrel : (a₁ - a₂) + (b₁ - b₂) * (n : ℤ) = 0 := by
      nlinarith
    have hnontrivial : a₁ - a₂ ≠ 0 ∨ b₁ - b₂ ≠ 0 := by
      by_contra h
      push_neg at h
      apply hne
      exact Prod.ext (sub_eq_zero.mp h.1) (sub_eq_zero.mp h.2)
    have hlow := integer_pair_relation_lower_bound n
      (a₁ - a₂) (b₁ - b₂) hrel hnontrivial
    have hbound : (a₁ - a₂).natAbs ≤ 2 * K := by
      calc
        (a₁ - a₂).natAbs ≤ a₁.natAbs + a₂.natAbs := Int.natAbs_sub_le _ _
        _ ≤ K + K := Nat.add_le_add ha₁ ha₂
        _ = 2 * K := by omega
    omega
  · intro hn
    refine ⟨(K : ℤ), 0, (K : ℤ) - (n : ℤ), 1, ?_, ?_, ?_, ?_, ?_, ?_⟩
    · simp
    · simp
    · omega
    · omega
    · intro heq
      have : (0 : ℤ) = 1 := congrArg Prod.snd heq
      omega
    · ring

end XedniHeightGrowthObstruction

#print axioms XedniHeightGrowthObstruction.integer_pair_relation_lower_bound
#print axioms XedniHeightGrowthObstruction.group_pair_relation_lower_bound
#print axioms XedniHeightGrowthObstruction.group_pair_relation_attained
#print axioms XedniHeightGrowthObstruction.packing_criterion_iff
#print axioms XedniHeightGrowthObstruction.no_relation_below_half
#print axioms XedniHeightGrowthObstruction.integer_pair_box_collision_iff
