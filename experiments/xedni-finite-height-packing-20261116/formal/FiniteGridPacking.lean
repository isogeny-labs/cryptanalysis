import MetricPacking

/-!
An explicit finite grid count for a projected height ball. The geometric
quantization estimate is retained as a hypothesis; this module checks the
cardinality and bounded-relation implications.
-/

namespace XedniFiniteGridPacking

open XedniHeightPigeonhole XedniMetricPacking

/-- If equal grid cells have diameter at most `ε`, an `ε`-separated finite
set in a coordinate box has at most `(2M+1)^d` members. -/
theorem separated_grid_card_le
    {X : Type*} [PseudoMetricSpace X] {d : ℕ}
    (values : Finset X) (cell : X → Fin d → ℤ) (M : ℕ) (ε : ℝ)
    (hbounded : ∀ x ∈ values, cell x ∈ coefficientBox d M)
    (hdiam : ∀ x ∈ values, ∀ y ∈ values,
      cell x = cell y → dist x y ≤ ε)
    (hsep : ∀ x ∈ values, ∀ y ∈ values,
      x ≠ y → ε < dist x y) :
    values.card ≤ (2 * M + 1) ^ d := by
  classical
  have hcard : values.card ≤ (coefficientBox d M).card := by
    apply Finset.card_le_card_of_injOn cell
    · exact hbounded
    · intro x hx y hy heq
      by_contra hne
      exact (not_lt_of_ge (hdiam x hx y hy heq)) (hsep x hx y hy hne)
  simpa [coefficientBox_card] using hcard

/-- A torsion label distinguishes values occupying the same projected cell. -/
theorem labelled_grid_card_le
    {Y X Label : Type*} [PseudoMetricSpace X] {d : ℕ}
    (values : Finset Y) (labels : Finset Label)
    (project : Y → X) (label : Y → Label)
    (cell : X → Fin d → ℤ) (M : ℕ) (ε : ℝ)
    (hlabel : ∀ y ∈ values, label y ∈ labels)
    (hfaithful : ∀ y ∈ values, ∀ z ∈ values,
      project y = project z → label y = label z → y = z)
    (hbounded : ∀ y ∈ values, cell (project y) ∈ coefficientBox d M)
    (hdiam : ∀ y ∈ values, ∀ z ∈ values,
      cell (project y) = cell (project z) →
        dist (project y) (project z) ≤ ε)
    (hsep : ∀ y ∈ values, ∀ z ∈ values,
      project y ≠ project z → ε < dist (project y) (project z)) :
    values.card ≤ labels.card * (2 * M + 1) ^ d := by
  classical
  have hcard : values.card ≤ (labels.product (coefficientBox d M)).card := by
    apply Finset.card_le_card_of_injOn (fun y => (label y, cell (project y)))
    · intro y hy
      exact Finset.mem_product.mpr ⟨hlabel y hy, hbounded y hy⟩
    · intro y hy z hz heq
      have hl : label y = label z := congrArg Prod.fst heq
      have hc : cell (project y) = cell (project z) := congrArg Prod.snd heq
      have hp : project y = project z := by
        by_contra hne
        exact (not_lt_of_ge (hdiam y hy z hz hc)) (hsep y hy z hz hne)
      exact hfaithful y hy z hz hp hl
  simpa [coefficientBox_card] using hcard

/-- An explicit quantized height-ball count below the coefficient-box
threshold gives a nonzero relation with coefficient size at most `2K`. -/
theorem bounded_relation_of_labelled_grid
    {H X Label : Type*} [AddCommGroup H] [PseudoMetricSpace X]
    {r d : ℕ} (points : Fin r → H) (K M : ℕ)
    (labels : Finset Label) (project : H → X) (label : H → Label)
    (cell : X → Fin d → ℤ) (ε : ℝ)
    (hlabel : ∀ y ∈ liftedSums points K, label y ∈ labels)
    (hfaithful : ∀ y ∈ liftedSums points K,
      ∀ z ∈ liftedSums points K,
      project y = project z → label y = label z → y = z)
    (hbounded : ∀ y ∈ liftedSums points K,
      cell (project y) ∈ coefficientBox d M)
    (hdiam : ∀ y ∈ liftedSums points K,
      ∀ z ∈ liftedSums points K,
      cell (project y) = cell (project z) →
        dist (project y) (project z) ≤ ε)
    (hsep : ∀ y ∈ liftedSums points K,
      ∀ z ∈ liftedSums points K,
      project y ≠ project z → ε < dist (project y) (project z))
    (hcount : labels.card * (2 * M + 1) ^ d < (2 * K + 1) ^ r) :
    ∃ coeff, XedniHeightPigeonhole.Nontrivial coeff ∧ Bounded (2 * K) coeff ∧
      Relation points coeff := by
  classical
  apply bounded_relation_of_height_ball_count points (liftedSums points K)
  · exact (labelled_grid_card_le (liftedSums points K) labels
      project label cell M ε hlabel hfaithful hbounded hdiam hsep).trans_lt hcount
  · intro coeff hc
    unfold liftedSums
    exact Finset.mem_image.mpr ⟨coeff, hc, rfl⟩

end XedniFiniteGridPacking

#print axioms XedniFiniteGridPacking.separated_grid_card_le
#print axioms XedniFiniteGridPacking.labelled_grid_card_le
#print axioms XedniFiniteGridPacking.bounded_relation_of_labelled_grid
