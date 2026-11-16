import TypedPrefixProgram

namespace XedniStageHitEquivalence

open XedniSymbolicCollision XedniPrefixPatternBridge
open XedniAdaptiveProgramInvariant XedniTranscriptDeterminism

/-- A scalar is eligible exactly when evaluated equality among all old
forms is the same as symbolic form equality, including known repeats. -/
theorem eligible_iff_eval_pattern {F : Type*}
    [Fintype F] [DecidableEq F] [Field F] {n : ℕ}
    (forms : Fin n → Affine F) (w : F) :
    w ∈ eligible forms ↔
      ∀ i j, eval (forms i) w = eval (forms j) w ↔ forms i = forms j := by
  classical
  constructor
  · intro hw i j
    exact eval_eq_iff_form_eq forms w hw i j
  · intro hpattern
    unfold eligible
    simp only [Finset.mem_sdiff, Finset.mem_univ, true_and]
    intro hcollision
    unfold collisionSet at hcollision
    obtain ⟨ij, hij, heq⟩ := (Finset.mem_filter.mp hcollision).2
    have hs : (forms ij.1).slope ≠ (forms ij.2).slope :=
      (Finset.mem_filter.mp hij).2.2
    have hne : forms ij.1 ≠ forms ij.2 := by
      intro h
      exact hs (congrArg Affine.slope h)
    exact hne ((hpattern ij.1 ij.2).mp heq)

/-- New informative equalities are exactly the next-form candidate roots. -/
theorem next_hit_iff_candidates {F : Type*}
    [Fintype F] [DecidableEq F] [Field F] {n : ℕ}
    (forms : Fin n → Affine F) (newForm : Affine F) (w : F) :
    (∃ i, forms i ≠ newForm ∧ eval (forms i) w = eval newForm w) ↔
      w ∈ nextCandidates forms newForm := by
  classical
  constructor
  · rintro ⟨i, hne, heq⟩
    exact new_eq_mem_candidates forms newForm w i hne heq
  · intro hw
    unfold nextCandidates at hw
    obtain ⟨i, hi, hc⟩ := Finset.mem_image.mp hw
    have hs : (forms i).slope ≠ newForm.slope :=
      (Finset.mem_filter.mp hi).2
    have hne : forms i ≠ newForm := by
      intro h
      exact hs (congrArg Affine.slope h)
    have heq := (unequal_slope_eq_iff_candidate
      (forms i) newForm hs w).mpr hc.symm
    exact ⟨i, hne, heq⟩

/-- The old actual group trace has the symbolic equality pattern exactly
for eligible scalars, provided scalar multiplication by G is injective. -/
theorem group_pattern_iff_eligible {F A : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [AddCommGroup A] [Module F A] {n : ℕ}
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (forms : Fin n → Affine F) (w : F) :
    (∀ i j, (eval (forms i) w) • G = (eval (forms j) w) • G ↔
      forms i = forms j) ↔ w ∈ eligible forms := by
  rw [eligible_iff_eval_pattern]
  constructor
  · intro h i j
    exact (public_group_equality_iff G hinj (forms i) (forms j) w).symm.trans
      (h i j)
  · intro h i j
    exact (public_group_equality_iff G hinj (forms i) (forms j) w).trans
      (h i j)

/-- A newly informative actual group equality is exactly membership in
the symbolic next-candidate set. -/
theorem group_next_hit_iff_candidates {F A : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [AddCommGroup A] [Module F A] {n : ℕ}
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (forms : Fin n → Affine F) (newForm : Affine F) (w : F) :
    (∃ i, forms i ≠ newForm ∧
      (eval (forms i) w) • G = (eval newForm w) • G) ↔
      w ∈ nextCandidates forms newForm := by
  rw [← next_hit_iff_candidates]
  constructor
  · rintro ⟨i, hne, heq⟩
    exact ⟨i, hne, hinj heq⟩
  · rintro ⟨i, hne, heq⟩
    exact ⟨i, hne, by rw [heq]⟩


/-- For a public DLP execution at stage `k`, an old trace with its
symbolic equality pattern followed by a new informative group equality
is exactly an eligible next-root scalar event. -/
theorem dlp_stage_hit_iff_eligible_next {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (w : F) (labels : Fin m → L)
    (hlabels : ∀ i, labels i =
      enc (runGroup program enc (seedPoints G w) i))
    (k : ℕ) (h2 : 2 ≤ k) (hk : k < m) :
    let hle : k ≤ m := Nat.le_of_lt hk
    let oldForms : Fin k → Affine F :=
      formsFromTranscript (XedniTypedPrefixProgram.takeAt program k h2 hle)
        (XedniTypedPrefixProgram.restrictLabels hle labels) seedForms
    let oldPoints : Fin k → A :=
      runGroup (XedniTypedPrefixProgram.takeAt program k h2 hle)
        enc (seedPoints G w)
    let newForm : Affine F :=
      formsFromTranscript program labels seedForms ⟨k, hk⟩
    let newPoint : A :=
      runGroup program enc (seedPoints G w) ⟨k, hk⟩
    ((∀ i j, oldPoints i = oldPoints j ↔ oldForms i = oldForms j) ∧
      (∃ i, oldForms i ≠ newForm ∧ oldPoints i = newPoint)) ↔
      w ∈ eligible oldForms ∩ nextCandidates oldForms newForm := by
  classical
  dsimp
  let hle : k ≤ m := Nat.le_of_lt hk
  let oldForms : Fin k → Affine F :=
    formsFromTranscript (XedniTypedPrefixProgram.takeAt program k h2 hle)
      (XedniTypedPrefixProgram.restrictLabels hle labels) seedForms
  let oldPoints : Fin k → A :=
    runGroup (XedniTypedPrefixProgram.takeAt program k h2 hle)
      enc (seedPoints G w)
  let newForm : Affine F :=
    formsFromTranscript program labels seedForms ⟨k, hk⟩
  let newPoint : A :=
    runGroup program enc (seedPoints G w) ⟨k, hk⟩
  have hpoint := dlp_group_from_transcript program enc G w labels hlabels
  have hpOld (i : Fin k) :
      oldPoints i = (eval (oldForms i) w) • G := by
    dsimp [oldPoints, oldForms]
    rw [XedniTypedPrefixProgram.runGroup_takeAt]
    rw [XedniTypedPrefixProgram.formsFromTranscript_takeAt]
    exact hpoint (Fin.castLE hle i)
  have hpNew : newPoint = (eval newForm w) • G := hpoint ⟨k, hk⟩
  have hpattern :
      (∀ i j, oldPoints i = oldPoints j ↔ oldForms i = oldForms j) ↔
      w ∈ eligible oldForms := by
    constructor
    · intro hp
      apply (group_pattern_iff_eligible G hinj oldForms w).mp
      intro i j
      rw [← hpOld i, ← hpOld j]
      exact hp i j
    · intro hw i j
      rw [hpOld i, hpOld j]
      exact (group_pattern_iff_eligible G hinj oldForms w).mpr hw i j
  have hhit :
      (∃ i, oldForms i ≠ newForm ∧ oldPoints i = newPoint) ↔
      w ∈ nextCandidates oldForms newForm := by
    constructor
    · rintro ⟨i, hne, heq⟩
      apply (group_next_hit_iff_candidates G hinj oldForms newForm w).mp
      exact ⟨i, hne, by simpa only [hpOld i, hpNew] using heq⟩
    · intro hw
      obtain ⟨i, hne, heq⟩ :=
        (group_next_hit_iff_candidates G hinj oldForms newForm w).mpr hw
      exact ⟨i, hne, by simpa only [hpOld i, hpNew] using heq⟩
  constructor
  · rintro ⟨hp, hh⟩
    exact Finset.mem_inter.mpr ⟨hpattern.mp hp, hhit.mp hh⟩
  · intro hw
    obtain ⟨hp, hh⟩ := Finset.mem_inter.mp hw
    exact ⟨hpattern.mpr hp, hhit.mpr hh⟩


#print axioms dlp_stage_hit_iff_eligible_next
#print axioms eligible_iff_eval_pattern
#print axioms next_hit_iff_candidates
#print axioms group_pattern_iff_eligible
#print axioms group_next_hit_iff_candidates

end XedniStageHitEquivalence
