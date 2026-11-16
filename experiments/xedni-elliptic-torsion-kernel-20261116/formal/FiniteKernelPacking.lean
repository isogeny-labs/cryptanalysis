import EuclideanPacking

/-!
The torsion multiplier in finite height-ball packing can be obtained from
the finite kernel of the projection. A representative of each occupied fiber
provides a canonical-for-the-proof kernel difference label.
-/

open XedniEuclideanPacking
open Module

namespace XedniFiniteKernelPacking

noncomputable section

variable {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
  [FiniteDimensional ℝ E]

noncomputable def projectedValues {H : Type*} [AddCommGroup H]
    (values : Finset H) (project : H →+ E) : Finset E := by
  classical
  exact values.image project

/-- A homomorphism with a kernel contained in a finite recorded set has at
most that many points in each fiber of a finite value set. -/
theorem finite_kernel_card_le_projected_card
    {H : Type*} [AddCommGroup H]
    (values kernel : Finset H) (project : H →+ E)
    (hkernel : ∀ z : H, project z = 0 → z ∈ kernel) :
    values.card ≤ (projectedValues values project).card * kernel.card := by
  classical
  let projected := projectedValues values project
  let repr : E → H := fun x =>
    if hx : x ∈ projected then Classical.choose (Finset.mem_image.mp hx) else 0
  have hrepr : ∀ x ∈ projected, repr x ∈ values ∧ project (repr x) = x := by
    intro x hx
    simpa [repr, hx] using Classical.choose_spec (Finset.mem_image.mp hx)
  have hcard : values.card ≤ (projected.product kernel).card := by
    apply Finset.card_le_card_of_injOn
      (fun y => (project y, y - repr (project y)))
    · intro y hy
      have hp : project y ∈ projected := Finset.mem_image.mpr ⟨y, hy, rfl⟩
      apply Finset.mem_product.mpr
      refine ⟨hp, hkernel _ ?_⟩
      simp [map_sub, (hrepr (project y) hp).2]
    · intro y hy z hz heq
      have hp : project y = project z := congrArg Prod.fst heq
      have hl : y - repr (project y) = z - repr (project z) :=
        congrArg Prod.snd heq
      have hl' : y - repr (project y) = z - repr (project y) := by
        simpa [hp] using hl
      exact add_right_cancel (by simpa only [sub_eq_add_neg] using hl')
  simpa [projected] using hcard

/-- The Euclidean packing count with the finite kernel charged directly,
without a separately supplied torsion-label function. -/
theorem finite_kernel_card_le_radius_ratio_pow
    {H : Type*} [AddCommGroup H]
    (values kernel : Finset H) (project : H →+ E) (R δ : ℝ)
    (hR : 0 ≤ R) (hδ : 0 < δ)
    (hkernel : ∀ z : H, project z = 0 → z ∈ kernel)
    (hradius : ∀ y ∈ values, ‖project y‖ ≤ R)
    (hsep : ∀ y ∈ values, ∀ z ∈ values,
      project y ≠ project z → δ ≤ ‖project y - project z‖) :
    (values.card : ℝ) ≤
      (kernel.card : ℝ) * (1 + 2 * R / δ) ^ finrank ℝ E := by
  classical
  let projected := projectedValues values project
  have hfiber : (values.card : ℝ) ≤
      (kernel.card : ℝ) * (projected.card : ℝ) := by
    have h := finite_kernel_card_le_projected_card values kernel project hkernel
    exact_mod_cast (by simpa [projected, mul_comm] using h)
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
    (values.card : ℝ) ≤ (kernel.card : ℝ) * (projected.card : ℝ) := hfiber
    _ ≤ (kernel.card : ℝ) * (1 + 2 * R / δ) ^ finrank ℝ E :=
      mul_le_mul_of_nonneg_left hpack (Nat.cast_nonneg _)

/-- A finite projection kernel and a uniform norm gap yield a bounded
integer relation whenever the explicit packing count is smaller than the
coefficient box. -/
theorem bounded_relation_of_finite_kernel_norm_gap
    {H : Type*} [AddCommGroup H]
    {r : ℕ} (points : Fin r → H) (K : ℕ)
    (kernel : Finset H) (project : H →+ E)
    (B δ : ℝ) (hB : 0 ≤ B) (hδ : 0 < δ)
    (hkernel : ∀ z : H, project z = 0 → z ∈ kernel)
    (hpoint : ∀ i, ‖project (points i)‖ ≤ B)
    (hmin : ∀ z : H, project z ≠ 0 → δ ≤ ‖project z‖)
    (hsmall : (kernel.card : ℝ) *
      (1 + 2 * ((r : ℝ) * (K : ℝ) * B) / δ) ^ finrank ℝ E <
        ((2 * K + 1) ^ r : ℝ)) :
    ∃ coeff, XedniHeightPigeonhole.Nontrivial coeff ∧
      XedniHeightPigeonhole.Bounded (2 * K) coeff ∧
      XedniHeightPigeonhole.Relation points coeff := by
  classical
  let values := liftedSums points K
  have hR : 0 ≤ (r : ℝ) * (K : ℝ) * B := by positivity
  have hradius : ∀ y ∈ values,
      ‖project y‖ ≤ (r : ℝ) * (K : ℝ) * B := by
    intro y hy
    obtain ⟨coeff, hc, rfl⟩ := Finset.mem_image.mp hy
    have hcoeff := XedniHeightPigeonhole.coefficientBox_bounded hc
    simpa only [map_sum, map_zsmul] using
      (norm_coeff_sum_le (fun i => project (points i)) coeff K B hB hcoeff hpoint)
  have hsep : ∀ y ∈ values, ∀ z ∈ values,
      project y ≠ project z → δ ≤ ‖project y - project z‖ := by
    intro y hy z hz hne
    have hdiff : project (y - z) ≠ 0 := by
      simpa only [map_sub] using (sub_ne_zero.mpr hne)
    simpa only [map_sub] using hmin (y - z) hdiff
  have hbound := finite_kernel_card_le_radius_ratio_pow values kernel project
    ((r : ℝ) * (K : ℝ) * B) δ hR hδ hkernel hradius hsep
  have hcardR : (values.card : ℝ) < ((2 * K + 1) ^ r : ℝ) :=
    hbound.trans_lt hsmall
  have hcard : values.card < (2 * K + 1) ^ r := by exact_mod_cast hcardR
  apply XedniHeightPigeonhole.bounded_relation_of_height_ball_count points values hcard
  intro coeff hc
  unfold values liftedSums
  exact Finset.mem_image.mpr ⟨coeff, hc, rfl⟩

end

end XedniFiniteKernelPacking

#print axioms XedniFiniteKernelPacking.finite_kernel_card_le_projected_card
#print axioms XedniFiniteKernelPacking.finite_kernel_card_le_radius_ratio_pow
#print axioms XedniFiniteKernelPacking.bounded_relation_of_finite_kernel_norm_gap
