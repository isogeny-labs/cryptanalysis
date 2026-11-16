import FirstCollisionLedger

namespace XedniPrefixPatternBridge
open XedniSymbolicCollision

noncomputable def eligible {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    {n : ℕ} (forms : Fin n → Affine F) : Finset F :=
  Finset.univ \ collisionSet forms

/-- Outside informative collisions, evaluated equality is symbolic equality,
including repeated forms. -/
theorem eval_eq_iff_form_eq {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    {n : ℕ} (forms : Fin n → Affine F) (w : F)
    (hw : w ∈ eligible forms) (i j : Fin n) :
    eval (forms i) w = eval (forms j) w ↔ forms i = forms j := by
  classical
  constructor
  · intro heq
    by_contra hne
    have hs : (forms i).slope ≠ (forms j).slope := by
      intro hs
      exact (same_slope_distinct_ne (forms i) (forms j) hs hne w) heq
    have hij : i ≠ j := by
      intro h
      exact hne (congrArg forms h)
    have hord : i < j ∨ j < i := lt_or_gt_of_ne hij
    have hcoll : w ∈ collisionSet forms := by
      unfold collisionSet
      simp only [Finset.mem_filter, Finset.mem_univ, true_and]
      rcases hord with hlt | hlt
      · exact ⟨(i,j), by simp [activePairs, hlt, hs], heq⟩
      · exact ⟨(j,i), by simp [activePairs, hlt, Ne.symm hs], heq.symm⟩
    exact (Finset.mem_sdiff.mp hw).2 hcoll
  · intro h
    rw [h]

/-- At least q-n² scalars have the fixed symbolic equality pattern. -/
theorem eligible_card_lower {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    {n : ℕ} (forms : Fin n → Affine F) :
    Fintype.card F - n * n ≤ (eligible forms).card := by
  classical
  unfold eligible
  have h := symbolic_collision_bound forms
  have hle : (Finset.univ \ collisionSet forms).card +
      (collisionSet forms).card = Fintype.card F := by
    rw [Finset.card_sdiff_add_card_eq_card]
    · simp
    · exact Finset.subset_univ _
  omega

noncomputable def nextCandidates {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    {n : ℕ} (forms : Fin n → Affine F) (newForm : Affine F) : Finset F := by
  classical
  exact (Finset.univ.filter (fun i : Fin n =>
    (forms i).slope ≠ newForm.slope)).image
      (fun i => candidate (forms i) newForm)

/-- At most one distinct-slope candidate arises per old trace position. -/
theorem next_candidates_card_le {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    {n : ℕ} (forms : Fin n → Affine F) (newForm : Affine F) :
    (nextCandidates forms newForm).card ≤ n := by
  classical
  unfold nextCandidates
  exact (Finset.card_image_le).trans
    ((Finset.card_filter_le _ _).trans (by simp))

/-- A new evaluated equality is among the next symbolic candidates. -/
theorem new_eq_mem_candidates {F : Type*} [Fintype F] [DecidableEq F] [Field F]
    {n : ℕ} (forms : Fin n → Affine F) (newForm : Affine F)
    (w : F) (i : Fin n) (hne : forms i ≠ newForm)
    (heq : eval (forms i) w = eval newForm w) :
    w ∈ nextCandidates forms newForm := by
  classical
  have hs : (forms i).slope ≠ newForm.slope := by
    intro hs
    exact (same_slope_distinct_ne (forms i) newForm hs hne w) heq
  unfold nextCandidates
  apply Finset.mem_image.mpr
  exact ⟨i, by simp [hs],
    ((unequal_slope_eq_iff_candidate (forms i) newForm hs w).mp heq).symm⟩


/-- Traces with the same equality pattern are related by a permutation of
the group-label domain, even when the traces contain known repeats. -/
theorem equal_pattern_perm {G : Type*} [Finite G] {n : ℕ}
    (x y : Fin n → G)
    (hpat : ∀ i j, x i = x j ↔ y i = y j) :
    ∃ σ : Equiv.Perm G, ∀ i, σ (x i) = y i := by
  classical
  let I := {g : G // g ∈ Set.range x}
  let idx : I → Fin n := fun a => Classical.choose a.2
  have hidx (a : I) : x (idx a) = a.1 := Classical.choose_spec a.2
  let f : I → G := fun a => a.1
  let g : I → G := fun a => y (idx a)
  have hf : Function.Injective f := Subtype.val_injective
  have hg : Function.Injective g := by
    intro a b hab
    apply Subtype.ext
    calc
      a.1 = x (idx a) := (hidx a).symm
      _ = x (idx b) := (hpat (idx a) (idx b)).mpr hab
      _ = b.1 := hidx b
  obtain ⟨σ, hσ⟩ := Equiv.Perm.exists_extending_pair f g hf hg
  refine ⟨σ, ?_⟩
  intro i
  let a : I := ⟨x i, ⟨i, rfl⟩⟩
  have ha := hσ a
  change σ (x i) = y (idx a) at ha
  calc
    σ (x i) = y (idx a) := ha
    _ = y i := (hpat (idx a) i).mp (hidx a)

/-- Uniform bijections give equal label-event mass for any two traces with
the same equality pattern. -/
theorem equal_pattern_label_event_card_eq {G L : Type*}
    [Fintype G] [Fintype L] {n : ℕ}
    (x y : Fin n → G)
    (hpat : ∀ i j, x i = x j ↔ y i = y j)
    (event : (Fin n → L) → Prop) :
    XedniRandomLabelCoupling.eventCount x event =
      XedniRandomLabelCoupling.eventCount y event := by
  classical
  obtain ⟨σ, hσ⟩ := equal_pattern_perm x y hpat
  let Φ : (G ≃ L) ≃ (G ≃ L) :=
    XedniRandomLabelCoupling.relabelEquiv σ
  have hobs (enc : G ≃ L) :
      (fun i => (Φ enc) (y i)) = (fun i => enc (x i)) := by
    funext i
    change enc (σ.symm (y i)) = enc (x i)
    rw [← hσ i, σ.symm_apply_apply]
  let e : {enc : G ≃ L // event (fun i => enc (x i))} ≃
      {enc : G ≃ L // event (fun i => enc (y i))} := {
    toFun := fun ⟨enc, henc⟩ => ⟨Φ enc, by simpa [hobs enc] using henc⟩
    invFun := fun ⟨enc, henc⟩ => ⟨Φ.symm enc, by
      have h := hobs (Φ.symm enc)
      simp only [Equiv.apply_symm_apply] at h
      rw [← h]
      exact henc⟩
    left_inv := by
      intro enc
      apply Subtype.ext
      simp
    right_inv := by
      intro enc
      apply Subtype.ext
      simp
  }
  change Fintype.card {enc : G ≃ L // event (fun i => enc (x i))} =
    Fintype.card {enc : G ≃ L // event (fun i => enc (y i))}
  exact Fintype.card_congr e


/-- All eligible scalars assign the same number of bijective encodings to
any event on the visible prefix, including prefixes with known repeats. -/
theorem eligible_label_event_card_eq {F L : Type*}
    [Fintype F] [DecidableEq F] [Field F] [Fintype L]
    {n : ℕ} (forms : Fin n → Affine F)
    (w₁ w₂ : F) (h₁ : w₁ ∈ eligible forms)
    (h₂ : w₂ ∈ eligible forms)
    (event : (Fin n → L) → Prop) :
    XedniRandomLabelCoupling.eventCount
      (fun i => eval (forms i) w₁) event =
    XedniRandomLabelCoupling.eventCount
      (fun i => eval (forms i) w₂) event := by
  apply equal_pattern_label_event_card_eq
  intro i j
  rw [eval_eq_iff_form_eq forms w₁ h₁ i j]
  rw [eval_eq_iff_form_eq forms w₂ h₂ i j]


noncomputable def prefixFiber {F L : Type*}
    [Fintype F] [DecidableEq F] [Field F] [Fintype L]
    {n : ℕ} (forms : Fin n → Affine F) (w : F)
    (labels : Fin n → L) : ℕ :=
  XedniRandomLabelCoupling.eventCount
    (fun i => eval (forms i) w) (fun seen => seen = labels)

/-- For one fixed visible prefix, the encoding-weighted mass of next-hit
candidate scalars is bounded by the candidate count divided by eligible
scalar count. Known symbolic repeats are included in the prefix law. -/
theorem weighted_next_candidate_bound {F L : Type*}
    [Fintype F] [DecidableEq F] [Field F] [Fintype L]
    {n : ℕ} (forms : Fin n → Affine F) (newForm : Affine F)
    (labels : Fin n → L) :
    (Fintype.card F - n * n) *
      (∑ w ∈ eligible forms ∩ nextCandidates forms newForm,
        prefixFiber forms w labels) ≤
    n * (∑ w ∈ eligible forms, prefixFiber forms w labels) := by
  classical
  by_cases hempty : (eligible forms).Nonempty
  · obtain ⟨w₀, hw₀⟩ := hempty
    let weight := prefixFiber forms w₀ labels
    have hconst (w : F) (hw : w ∈ eligible forms) :
        prefixFiber forms w labels = weight := by
      exact eligible_label_event_card_eq forms w w₀ hw hw₀
        (fun seen => seen = labels)
    have hbad : (eligible forms ∩ nextCandidates forms newForm).card ≤ n :=
      (Finset.card_le_card Finset.inter_subset_right).trans
        (next_candidates_card_le forms newForm)
    have hgood := eligible_card_lower forms
    have hratio : (Fintype.card F - n * n) *
        (eligible forms ∩ nextCandidates forms newForm).card ≤
        n * (eligible forms).card := calc
      _ ≤ (Fintype.card F - n * n) * n :=
        Nat.mul_le_mul_left _ hbad
      _ = n * (Fintype.card F - n * n) := by ac_rfl
      _ ≤ n * (eligible forms).card := Nat.mul_le_mul_left n hgood
    have hsumBad :
        (∑ w ∈ eligible forms ∩ nextCandidates forms newForm,
          prefixFiber forms w labels) =
          (eligible forms ∩ nextCandidates forms newForm).card * weight := by
      calc
        _ = ∑ w ∈ eligible forms ∩ nextCandidates forms newForm,
              weight := by
                apply Finset.sum_congr rfl
                intro w hw
                exact hconst w (Finset.mem_inter.mp hw).1
        _ = _ := by simp
    have hsumGood :
        (∑ w ∈ eligible forms, prefixFiber forms w labels) =
          (eligible forms).card * weight := by
      calc
        _ = ∑ w ∈ eligible forms, weight := by
              apply Finset.sum_congr rfl
              intro w hw
              exact hconst w hw
        _ = _ := by simp
    rw [hsumBad, hsumGood]
    simpa [mul_assoc, mul_comm, mul_left_comm] using
      Nat.mul_le_mul_right weight hratio
  · have hzero : eligible forms = ∅ := Finset.not_nonempty_iff_eq_empty.mp hempty
    simp [hzero]


/-- Any designated first-hit set contained in the eligible next candidates
inherits the encoding-weighted one-step bound. -/
theorem weighted_first_hit_bound {F L : Type*}
    [Fintype F] [DecidableEq F] [Field F] [Fintype L]
    {n : ℕ} (forms : Fin n → Affine F) (newForm : Affine F)
    (labels : Fin n → L) (firstHit : Finset F)
    (hsubset : firstHit ⊆ eligible forms ∩ nextCandidates forms newForm) :
    (Fintype.card F - n * n) *
      (∑ w ∈ firstHit, prefixFiber forms w labels) ≤
    n * (∑ w ∈ eligible forms, prefixFiber forms w labels) := by
  exact (Nat.mul_le_mul_left _ (Finset.sum_le_sum_of_subset hsubset)).trans
    (weighted_next_candidate_bound forms newForm labels)

#print axioms weighted_first_hit_bound
#print axioms prefixFiber
#print axioms weighted_next_candidate_bound
#print axioms eligible_label_event_card_eq
#print axioms equal_pattern_perm
#print axioms equal_pattern_label_event_card_eq
#print axioms eligible
#print axioms eval_eq_iff_form_eq

#print axioms eligible_card_lower
#print axioms nextCandidates
#print axioms next_candidates_card_le
#print axioms new_eq_mem_candidates
end XedniPrefixPatternBridge
