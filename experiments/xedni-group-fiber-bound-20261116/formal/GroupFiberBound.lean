import BucketFiberPartition

namespace XedniGroupFiberBound

set_option linter.style.haveILetI false

open XedniSymbolicCollision XedniPrefixPatternBridge
open XedniStageHitEquivalence XedniBucketFiberPartition
open XedniAdaptiveProgramInvariant XedniTranscriptDeterminism
open XedniTypedPrefixProgram XedniTranscriptFiberEquivalence
open XedniFirstHitPartition

/-- Exact group-encoding weight of a proposed visible label tuple. -/
noncomputable def groupPrefixFiber {F A L : Type*}
    [Field F] [Fintype A] [Fintype L]
    [AddCommGroup A] [Module F A] {n : ℕ}
    (G : A) (forms : Fin n → Affine F) (w : F)
    (labels : Fin n → L) : ℕ :=
  XedniRandomLabelCoupling.eventCount
    (fun i => (eval (forms i) w) • G) (fun seen => seen = labels)

/-- Eligible scalars have the same group-label encoding weight in one
fixed visible bucket, including known repeated forms. -/
theorem eligible_group_fiber_eq {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L]
    [AddCommGroup A] [Module F A] {n : ℕ}
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (forms : Fin n → Affine F) (labels : Fin n → L)
    (w₁ w₂ : F) (h₁ : w₁ ∈ eligible forms)
    (h₂ : w₂ ∈ eligible forms) :
    groupPrefixFiber G forms w₁ labels =
      groupPrefixFiber G forms w₂ labels := by
  apply XedniPrefixPatternBridge.equal_pattern_label_event_card_eq
  intro i j
  have hp₁ := (group_pattern_iff_eligible G hinj forms w₁).mpr h₁
  have hp₂ := (group_pattern_iff_eligible G hinj forms w₂).mpr h₂
  exact (hp₁ i j).trans (hp₂ i j).symm

/-- The weighted mass of eligible next-candidate scalars in a visible
group-label bucket obeys the candidate-count bound. -/
theorem weighted_group_next_candidate_bound {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L]
    [AddCommGroup A] [Module F A] {n : ℕ}
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (forms : Fin n → Affine F) (newForm : Affine F)
    (labels : Fin n → L) :
    (Fintype.card F - n * n) *
      (∑ w ∈ eligible forms ∩ nextCandidates forms newForm,
        groupPrefixFiber G forms w labels) ≤
    n * (∑ w ∈ eligible forms,
      groupPrefixFiber G forms w labels) := by
  classical
  by_cases hempty : (eligible forms).Nonempty
  · obtain ⟨w₀, hw₀⟩ := hempty
    let weight := groupPrefixFiber G forms w₀ labels
    have hconst (w : F) (hw : w ∈ eligible forms) :
        groupPrefixFiber G forms w labels = weight :=
      eligible_group_fiber_eq G hinj forms labels w w₀ hw hw₀
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
          groupPrefixFiber G forms w labels) =
          (eligible forms ∩ nextCandidates forms newForm).card * weight := by
      calc
        _ = ∑ w ∈ eligible forms ∩ nextCandidates forms newForm,
              weight := by
                apply Finset.sum_congr rfl
                intro w hw
                exact hconst w (Finset.mem_inter.mp hw).1
        _ = _ := by simp
    have hsumGood :
        (∑ w ∈ eligible forms, groupPrefixFiber G forms w labels) =
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

/-- The exact encoding fiber of an adaptive visible prefix is the group
prefix fiber of the affine forms reconstructed from that same prefix. -/
theorem adaptive_encoding_fiber_eq_group_fiber {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A)
    (h2 : 2 ≤ k) (hk : k ≤ m) (w : F) (labels : Fin k → L) :
    encodingFiber (executionPrefixBucket program G hk) w labels =
      groupPrefixFiber G (formsInBucket (F := F) program h2 hk labels)
        w labels := by
  classical
  have hactual (enc : A ≃ L) :
      executionPrefixBucket program G hk w enc = labels ↔
      ∀ i : Fin k, labels i = enc
        (runGroup (takeAt program k h2 hk) enc (seedPoints G w) i) := by
    constructor
    · intro h i
      have hi := congrFun h i
      simpa only [executionPrefixBucket, restrictLabels, executionLabels,
        runGroup_takeAt] using hi.symm
    · intro h
      funext i
      have hi := h i
      simpa only [executionPrefixBucket, restrictLabels, executionLabels,
        runGroup_takeAt] using hi.symm
  have hsymbolic (enc : A ≃ L) :
      (∀ i : Fin k, labels i = enc
        (runGroup (takeAt program k h2 hk) enc (seedPoints G w) i)) ↔
      (∀ i : Fin k, labels i = enc
        ((eval (formsInBucket (F := F) program h2 hk labels i) w) • G)) :=
    dlp_labels_iff_symbolic_fiber
      (takeAt program k h2 hk) enc G w labels
  have hfiber (enc : A ≃ L) :
      executionPrefixBucket program G hk w enc = labels ↔
      (fun i => enc
        ((eval (formsInBucket (F := F) program h2 hk labels i) w) • G)) =
        labels := by
    rw [hactual enc, hsymbolic enc]
    constructor
    · intro h
      funext i
      exact (h i).symm
    · intro h i
      exact (congrFun h i).symm
  let Φ : {enc : A ≃ L //
      executionPrefixBucket program G hk w enc = labels} ≃
      {enc : A ≃ L // (fun i => enc
        ((eval (formsInBucket (F := F) program h2 hk labels i) w) • G)) =
        labels} := {
    toFun := fun ⟨enc, h⟩ => ⟨enc, (hfiber enc).mp h⟩
    invFun := fun ⟨enc, h⟩ => ⟨enc, (hfiber enc).mpr h⟩
    left_inv := by intro x; apply Subtype.ext; rfl
    right_inv := by intro x; apply Subtype.ext; rfl
  }
  unfold encodingFiber groupPrefixFiber XedniRandomLabelCoupling.eventCount
  rw [Fintype.card_eq_nat_card, Fintype.card_eq_nat_card]
  exact Nat.card_congr Φ

#print axioms groupPrefixFiber
#print axioms eligible_group_fiber_eq
#print axioms weighted_group_next_candidate_bound
#print axioms adaptive_encoding_fiber_eq_group_fiber

end XedniGroupFiberBound
