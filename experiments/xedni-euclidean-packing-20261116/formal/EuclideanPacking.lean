import Mathlib.MeasureTheory.Covering.BesicovitchVectorSpace
import HeightPigeonhole

/-!
An explicit finite packing count in a finite-dimensional real normed space.
This is the geometric estimate needed for the canonical-height quotient.
-/

open Metric Set Module MeasureTheory
open scoped ENNReal Topology Function

namespace XedniEuclideanPacking

noncomputable section

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
  [FiniteDimensional ℝ E]

/-- A finite `δ`-separated subset of a radius-`R` norm ball has cardinality
bounded by the ratio of the enclosing and disjoint-ball volumes. -/
theorem card_mul_half_sep_pow_le_radius_pow
    (s : Finset E) (R δ : ℝ) (hR : 0 ≤ R) (hδ : 0 < δ)
    (hs : ∀ c ∈ s, ‖c‖ ≤ R)
    (hsep : ∀ c ∈ s, ∀ d ∈ s, c ≠ d → δ ≤ ‖c - d‖) :
    (s.card : ℝ) * (δ / 2) ^ finrank ℝ E ≤ (R + δ / 2) ^ finrank ℝ E := by
  borelize E
  let μ : Measure E := Measure.addHaar
  let η : ℝ := δ / 2
  let ρ : ℝ := R + η
  have ηpos : 0 < η := by dsimp [η]; positivity
  have ρpos : 0 < ρ := by dsimp [ρ]; positivity
  set A := ⋃ c ∈ s, ball (c : E) η with hA
  have D : Set.Pairwise (s : Set E) (Disjoint on fun c => ball (c : E) η) := by
    rintro c hc d hd hcd
    apply ball_disjoint_ball
    rw [dist_eq_norm]
    convert hsep c hc d hd hcd using 1
    dsimp [η]
    ring
  have A_subset : A ⊆ ball (0 : E) ρ := by
    refine iUnion₂_subset fun x hx => ?_
    apply ball_subset_ball'
    calc
      η + dist x 0 ≤ η + R := by rw [dist_zero_right]; exact add_le_add le_rfl (hs x hx)
      _ = ρ := by dsimp [ρ]; ring
  have I :
      (s.card : ℝ≥0∞) * ENNReal.ofReal (η ^ finrank ℝ E) * μ (ball 0 1) ≤
        ENNReal.ofReal (ρ ^ finrank ℝ E) * μ (ball 0 1) :=
    calc
      (s.card : ℝ≥0∞) * ENNReal.ofReal (η ^ finrank ℝ E) * μ (ball 0 1) = μ A := by
        rw [hA, measure_biUnion_finset D fun c _ => measurableSet_ball]
        simp only [μ.addHaar_ball_of_pos _ ηpos]
        simp only [Finset.sum_const, nsmul_eq_mul, mul_assoc]
      _ ≤ μ (ball (0 : E) ρ) := measure_mono A_subset
      _ = ENNReal.ofReal (ρ ^ finrank ℝ E) * μ (ball 0 1) := by
        simp only [μ.addHaar_ball_of_pos _ ρpos]
  have J :
      (s.card : ℝ≥0∞) * ENNReal.ofReal (η ^ finrank ℝ E) ≤
        ENNReal.ofReal (ρ ^ finrank ℝ E) :=
    (ENNReal.mul_le_mul_iff_left (measure_ball_pos _ _ zero_lt_one).ne'
      measure_ball_lt_top.ne).1 I
  have K := ENNReal.toReal_le_of_le_ofReal (pow_nonneg ρpos.le _) J
  simpa [η, ρ, ENNReal.toReal_ofReal (pow_nonneg ηpos.le _)] using K

/-- The finite packing bound, with the radius and separation retained as
independent parameters. -/
theorem card_le_radius_ratio_pow
    (s : Finset E) (R δ : ℝ) (hR : 0 ≤ R) (hδ : 0 < δ)
    (hs : ∀ c ∈ s, ‖c‖ ≤ R)
    (hsep : ∀ c ∈ s, ∀ d ∈ s, c ≠ d → δ ≤ ‖c - d‖) :
    (s.card : ℝ) ≤ (1 + 2 * R / δ) ^ finrank ℝ E := by
  have hhalf : 0 < δ / 2 := by positivity
  have hp : 0 < (δ / 2) ^ finrank ℝ E := pow_pos hhalf _
  have hpack := card_mul_half_sep_pow_le_radius_pow s R δ hR hδ hs hsep
  have hratio : (R + δ / 2) / (δ / 2) = 1 + 2 * R / δ := by
    field_simp
    ring
  calc
    (s.card : ℝ) ≤ (R + δ / 2) ^ finrank ℝ E / (δ / 2) ^ finrank ℝ E :=
      (le_div_iff₀ hp).2 hpack
    _ = ((R + δ / 2) / (δ / 2)) ^ finrank ℝ E := by simp only [div_pow]
    _ = (1 + 2 * R / δ) ^ finrank ℝ E := by rw [hratio]

/-- A finite label set accounts for fibers of a projection onto the normed
space. In the Mordell--Weil application the labels are torsion classes. -/
theorem labelled_card_le_radius_ratio_pow
    {Y Label : Type*} (values : Finset Y) (labels : Finset Label)
    (project : Y → E) (label : Y → Label) (R δ : ℝ)
    (hR : 0 ≤ R) (hδ : 0 < δ)
    (hlabel : ∀ y ∈ values, label y ∈ labels)
    (hfaithful : ∀ y ∈ values, ∀ z ∈ values,
      project y = project z → label y = label z → y = z)
    (hradius : ∀ y ∈ values, ‖project y‖ ≤ R)
    (hsep : ∀ y ∈ values, ∀ z ∈ values,
      project y ≠ project z → δ ≤ ‖project y - project z‖) :
    (values.card : ℝ) ≤
      (labels.card : ℝ) * (1 + 2 * R / δ) ^ finrank ℝ E := by
  classical
  let projected := values.image project
  have hcard : values.card ≤ (labels.product projected).card := by
    apply Finset.card_le_card_of_injOn (fun y => (label y, project y))
    · intro y hy
      exact Finset.mem_product.mpr ⟨hlabel y hy, Finset.mem_image.mpr ⟨y, hy, rfl⟩⟩
    · intro y hy z hz heq
      exact hfaithful y hy z hz (congrArg Prod.snd heq) (congrArg Prod.fst heq)
  have hcardR : (values.card : ℝ) ≤
      (labels.card : ℝ) * (projected.card : ℝ) := by
    simpa using (Nat.cast_le.mpr (by simpa using hcard) :
      (values.card : ℝ) ≤ ((labels.product projected).card : ℝ))
  have hpack : (projected.card : ℝ) ≤
      (1 + 2 * R / δ) ^ finrank ℝ E :=
    card_le_radius_ratio_pow projected R δ hR hδ
      (by
        intro x hx
        obtain ⟨y, hy, rfl⟩ := Finset.mem_image.mp hx
        exact hradius y hy)
      (by
        intro x hx z hz hne
        obtain ⟨y, hy, rfl⟩ := Finset.mem_image.mp hx
        obtain ⟨w, hw, rfl⟩ := Finset.mem_image.mp hz
        exact hsep y hy w hw hne)
  calc
    (values.card : ℝ) ≤ (labels.card : ℝ) * (projected.card : ℝ) := hcardR
    _ ≤ (labels.card : ℝ) * (1 + 2 * R / δ) ^ finrank ℝ E :=
      mul_le_mul_of_nonneg_left hpack (Nat.cast_nonneg _)

/-- All distinct lifted sums from the full coefficient box. -/
noncomputable def liftedSums {H : Type*} [AddCommGroup H] {r : ℕ}
    (points : Fin r → H) (K : ℕ) : Finset H := by
  classical
  exact (XedniHeightPigeonhole.coefficientBox r K).image
    (fun coeff => ∑ i, coeff i • points i)

/-- A canonical-height-style Euclidean projection with a finite torsion
label, minimum separation, and radius bound forces a bounded relation once
the explicit packing count is below the full coefficient box. -/
theorem bounded_relation_of_euclidean_packing
    {H Label : Type*} [AddCommGroup H]
    {r : ℕ} (points : Fin r → H) (K : ℕ)
    (labels : Finset Label) (project : H → E) (label : H → Label)
    (R δ : ℝ) (hR : 0 ≤ R) (hδ : 0 < δ)
    (hlabel : ∀ y ∈ liftedSums points K, label y ∈ labels)
    (hfaithful : ∀ y ∈ liftedSums points K,
      ∀ z ∈ liftedSums points K,
      project y = project z → label y = label z → y = z)
    (hradius : ∀ y ∈ liftedSums points K, ‖project y‖ ≤ R)
    (hsep : ∀ y ∈ liftedSums points K,
      ∀ z ∈ liftedSums points K,
      project y ≠ project z → δ ≤ ‖project y - project z‖)
    (hsmall : (labels.card : ℝ) *
      (1 + 2 * R / δ) ^ finrank ℝ E < ((2 * K + 1) ^ r : ℝ)) :
    ∃ coeff, XedniHeightPigeonhole.Nontrivial coeff ∧
      XedniHeightPigeonhole.Bounded (2 * K) coeff ∧
      XedniHeightPigeonhole.Relation points coeff := by
  classical
  have hcardR : ((liftedSums points K).card : ℝ) < ((2 * K + 1) ^ r : ℝ) :=
    (labelled_card_le_radius_ratio_pow (liftedSums points K) labels
      project label R δ hR hδ hlabel hfaithful hradius hsep).trans_lt hsmall
  have hcard : (liftedSums points K).card < (2 * K + 1) ^ r := by
    exact_mod_cast hcardR
  apply XedniHeightPigeonhole.bounded_relation_of_height_ball_count points
    (liftedSums points K) hcard
  intro coeff hc
  unfold liftedSums
  exact Finset.mem_image.mpr ⟨coeff, hc, rfl⟩

end

end XedniEuclideanPacking

#print axioms XedniEuclideanPacking.card_mul_half_sep_pow_le_radius_pow
#print axioms XedniEuclideanPacking.card_le_radius_ratio_pow
#print axioms XedniEuclideanPacking.labelled_card_le_radius_ratio_pow
#print axioms XedniEuclideanPacking.bounded_relation_of_euclidean_packing
