import HeightPigeonhole
import Mathlib.Topology.MetricSpace.Basic
import Mathlib.Tactic.Ring

/-!
A basis-free finite covering step for the xedni height-ball argument.
The metric separation and covering-center count are explicit inputs.
-/

namespace XedniMetricPacking

/-- A finite separated set has at most as many points as a finite collection
of radius-`ε` balls covering it, provided distinct values are farther apart
than `2ε`. -/
theorem separated_values_card_le_centers {X : Type*} [PseudoMetricSpace X]
    (values centers : Finset X) (ε : ℝ)
    (hcover : ∀ x ∈ values, ∃ c ∈ centers, dist x c ≤ ε)
    (hsep : ∀ x ∈ values, ∀ y ∈ values, x ≠ y → 2 * ε < dist x y) :
    values.card ≤ centers.card := by
  classical
  let pick : X → X := fun x =>
    if hx : x ∈ values then Classical.choose (hcover x hx) else x
  have hpick : ∀ x ∈ values, pick x ∈ centers ∧ dist x (pick x) ≤ ε := by
    intro x hx
    simpa [pick, hx] using Classical.choose_spec (hcover x hx)
  apply Finset.card_le_card_of_injOn pick
  · intro x hx
    exact (hpick x hx).1
  · intro x hx y hy hxy
    by_contra hne
    have hy' : dist (pick x) y ≤ ε := by
      rw [hxy]
      simpa [dist_comm] using (hpick y hy).2
    have hdist : dist x y ≤ 2 * ε := by
      calc
        dist x y ≤ dist x (pick x) + dist (pick x) y := dist_triangle _ _ _
        _ ≤ ε + ε := add_le_add (hpick x hx).2 hy'
        _ = 2 * ε := by ring
    exact (not_lt_of_ge hdist) (hsep x hx y hy hne)

/-- A finite label set accounts for fibers of a metric projection, such as
torsion classes above a canonical-height quotient. Equal projected points
with equal labels must be the same original value. -/
theorem labelled_values_card_le_centers
    {Y X Label : Type*} [PseudoMetricSpace X]
    (values : Finset Y) (centers : Finset X) (labels : Finset Label)
    (project : Y → X) (label : Y → Label) (ε : ℝ)
    (hlabel : ∀ y ∈ values, label y ∈ labels)
    (hfaithful : ∀ y ∈ values, ∀ z ∈ values,
      project y = project z → label y = label z → y = z)
    (hcover : ∀ y ∈ values,
      ∃ c ∈ centers, dist (project y) c ≤ ε)
    (hsep : ∀ y ∈ values, ∀ z ∈ values,
      project y ≠ project z → 2 * ε < dist (project y) (project z)) :
    values.card ≤ centers.card * labels.card := by
  classical
  let pick : Y → X := fun y =>
    if hy : y ∈ values then Classical.choose (hcover y hy) else project y
  have hpick : ∀ y ∈ values,
      pick y ∈ centers ∧ dist (project y) (pick y) ≤ ε := by
    intro y hy
    simpa [pick, hy] using Classical.choose_spec (hcover y hy)
  have hcard : values.card ≤ (centers.product labels).card := by
    apply Finset.card_le_card_of_injOn (fun y => (pick y, label y))
    · intro y hy
      exact Finset.mem_product.mpr ⟨(hpick y hy).1, hlabel y hy⟩
    · intro y hy z hz heq
      have hcenter : pick y = pick z := congrArg Prod.fst heq
      have hlabels : label y = label z := congrArg Prod.snd heq
      have hproject : project y = project z := by
        by_contra hne
        have hz' : dist (pick y) (project z) ≤ ε := by
          rw [hcenter]
          simpa [dist_comm] using (hpick z hz).2
        have hdist : dist (project y) (project z) ≤ 2 * ε := by
          calc
            dist (project y) (project z) ≤
              dist (project y) (pick y) + dist (pick y) (project z) :=
                dist_triangle _ _ _
            _ ≤ ε + ε := add_le_add (hpick y hy).2 hz'
            _ = 2 * ε := by ring
        exact (not_lt_of_ge hdist) (hsep y hy z hz hne)
      exact hfaithful y hy z hz hproject hlabels
  simpa using hcard

variable {r K : ℕ} {H : Type*} [AddCommGroup H] [PseudoMetricSpace H]

/-- The distinct lifted sums from the full radius-`K` coefficient box. -/
noncomputable def liftedSums (points : Fin r → H) (K : ℕ) : Finset H := by
  classical
  exact (XedniHeightPigeonhole.coefficientBox r K).image
    (fun coeff => ∑ i, coeff i • points i)

/-- A finite metric cover smaller than the coefficient box forces a
nontrivial bounded relation. This route counts height-ball values without
choosing an integer lattice basis. -/
theorem bounded_relation_of_metric_cover
    (points : Fin r → H) (K : ℕ)
    (centers : Finset H) (ε : ℝ)
    (hcover : ∀ x ∈ liftedSums points K,
      ∃ c ∈ centers, dist x c ≤ ε)
    (hsep : ∀ x ∈ liftedSums points K,
      ∀ y ∈ liftedSums points K,
        x ≠ y → 2 * ε < dist x y)
    (hcenters : centers.card < (2 * K + 1) ^ r) :
    ∃ coeff, XedniHeightPigeonhole.Nontrivial coeff ∧
      XedniHeightPigeonhole.Bounded (2 * K) coeff ∧
      XedniHeightPigeonhole.Relation points coeff := by
  classical
  apply XedniHeightPigeonhole.bounded_relation_of_height_ball_count
    points (liftedSums points K)
  · exact (separated_values_card_le_centers
      (liftedSums points K) centers ε hcover hsep).trans_lt hcenters
  · intro coeff hc
    unfold liftedSums
    exact Finset.mem_image.mpr ⟨coeff, hc, rfl⟩

/-- The torsion-aware metric-cover version. A finite label distinguishes
values in the same metric projection fiber, so the count charges the number
of labels as well as covering centers. -/
theorem bounded_relation_of_labelled_metric_cover
    {X Label : Type*} [PseudoMetricSpace X]
    (points : Fin r → H) (K : ℕ)
    (centers : Finset X) (labels : Finset Label)
    (project : H → X) (label : H → Label) (ε : ℝ)
    (hlabel : ∀ y ∈ liftedSums points K, label y ∈ labels)
    (hfaithful : ∀ y ∈ liftedSums points K,
      ∀ z ∈ liftedSums points K,
        project y = project z → label y = label z → y = z)
    (hcover : ∀ y ∈ liftedSums points K,
      ∃ c ∈ centers, dist (project y) c ≤ ε)
    (hsep : ∀ y ∈ liftedSums points K,
      ∀ z ∈ liftedSums points K,
        project y ≠ project z →
          2 * ε < dist (project y) (project z))
    (hcount : centers.card * labels.card < (2 * K + 1) ^ r) :
    ∃ coeff, XedniHeightPigeonhole.Nontrivial coeff ∧
      XedniHeightPigeonhole.Bounded (2 * K) coeff ∧
      XedniHeightPigeonhole.Relation points coeff := by
  classical
  apply XedniHeightPigeonhole.bounded_relation_of_height_ball_count
    points (liftedSums points K)
  · exact (labelled_values_card_le_centers
      (liftedSums points K) centers labels project label ε
      hlabel hfaithful hcover hsep).trans_lt hcount
  · intro coeff hc
    unfold liftedSums
    exact Finset.mem_image.mpr ⟨coeff, hc, rfl⟩

end XedniMetricPacking

#print axioms XedniMetricPacking.separated_values_card_le_centers
#print axioms XedniMetricPacking.bounded_relation_of_metric_cover
#print axioms XedniMetricPacking.labelled_values_card_le_centers
#print axioms XedniMetricPacking.bounded_relation_of_labelled_metric_cover
