import FirstHitPartition

namespace XedniBucketFiberPartition

-- The local decidable predicate instances below fix the subtype enumeration
-- used by the exact finite-cardinality equalities.
set_option linter.style.haveILetI false

open XedniFirstHitPartition XedniTypedPrefixProgram
open XedniAdaptiveProgramInvariant XedniTranscriptDeterminism
open XedniPrefixPatternBridge XedniAdaptiveStageSum
open XedniSymbolicCollision
open XedniTranscriptFiberEquivalence

/-- Encodings at scalar `w` producing the specified visible label bucket. -/
noncomputable def encodingFiber {W E T : Type*} [Fintype E]
    (bucket : W → E → T) (w : W) (t : T) : ℕ := by
  classical
  exact Fintype.card {e : E // bucket w e = t}

/-- Count accepted scalar-and-encoding executions directly. -/
noncomputable def acceptedCount {W E T : Type*}
    [Fintype W] [Fintype E]
    (bucket : W → E → T) (good : T → W → Prop) : ℕ := by
  classical
  exact Fintype.card {p : W × E // good (bucket p.1 p.2) p.1}

/-- Sum the accepted encoding fibers over every label-and-scalar cell. -/
noncomputable def bucketMass {W E T : Type*}
    [Fintype W] [Fintype E] [Fintype T]
    (bucket : W → E → T) (good : T → W → Prop) : ℕ := by
  classical
  exact ∑ tw : T × W, Fintype.card
    {e : E // good tw.1 tw.2 ∧ bucket tw.2 e = tw.1}

/-- Every accepted execution appears in exactly one visible-label bucket
and exactly one scalar fiber within that bucket. -/
theorem accepted_count_eq_bucket_mass {W E T : Type*}
    [Fintype W] [Fintype E] [Fintype T]
    (bucket : W → E → T) (good : T → W → Prop) :
    acceptedCount bucket good = bucketMass bucket good := by
  classical
  let X := {p : W × E // good (bucket p.1 p.2) p.1}
  let f : X → T × W := fun x => (bucket x.1.1 x.1.2, x.1.1)
  have hcell (tw : T × W) :
      Fintype.card {x : X // f x = tw} =
      Fintype.card {e : E // good tw.1 tw.2 ∧ bucket tw.2 e = tw.1} := by
    let Φ : {x : X // f x = tw} ≃
        {e : E // good tw.1 tw.2 ∧ bucket tw.2 e = tw.1} := {
    toFun := fun ⟨⟨⟨w, e⟩, hgood⟩, hpair⟩ => ⟨e, by
      have hb : bucket w e = tw.1 := congrArg Prod.fst hpair
      have hw : w = tw.2 := congrArg Prod.snd hpair
      subst w
      exact ⟨by simpa only [hb] using hgood, hb⟩⟩
    invFun := fun ⟨e, h⟩ =>
      ⟨⟨(tw.2, e), by simpa only [h.2] using h.1⟩,
        by exact Prod.ext h.2 rfl⟩
    left_inv := by
      intro x
      apply Subtype.ext
      apply Subtype.ext
      apply Prod.ext
      · exact (congrArg Prod.snd x.2).symm
      · rfl
    right_inv := by
      intro x
      rfl
    }
    exact Fintype.card_congr Φ
  unfold acceptedCount bucketMass
  calc
    Fintype.card X =
        Fintype.card (Σ tw : T × W, {x : X // f x = tw}) :=
      Fintype.card_congr (Equiv.sigmaFiberEquiv f).symm
    _ = ∑ tw : T × W, Fintype.card {x : X // f x = tw} := by
      simp only [Fintype.card_sigma]
    _ = ∑ tw : T × W, Fintype.card
          {e : E // good tw.1 tw.2 ∧ bucket tw.2 e = tw.1} := by
      apply Finset.sum_congr rfl
      intro tw _
      exact hcell tw

/-- The labels visible after `k` points of one actual execution. -/
def executionPrefixBucket {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A) (hk : k ≤ m)
    (w : F) (enc : A ≃ L) : Fin k → L :=
  restrictLabels hk (executionLabels program G (w, enc))

/-- Reconstruct old forms using only the proposed visible prefix. -/
def formsInBucket {F L : Type*} [Field F] {m k : ℕ}
    (program : Program L 2 m) (h2 : 2 ≤ k) (hk : k ≤ m)
    (labels : Fin k → L) : Fin k → Affine F :=
  formsFromTranscript (takeAt program k h2 hk) labels seedForms

/-- Actual execution liveness depends on its scalar and visible prefix
through exactly the bucket eligibility predicate. -/
theorem execution_live_iff_bucket_eligible {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (h2 : 2 ≤ k) (hk : k ≤ m) (w : F) (enc : A ≃ L) :
    (w, enc) ∈ liveSet (firstHit (executionHit program G)) k ↔
      w ∈ eligible (formsInBucket (F := F) program h2 hk
        (executionPrefixBucket program G hk w enc)) := by
  have hforms : formsInBucket (F := F) program h2 hk
      (executionPrefixBucket program G hk w enc) =
      (fun i : Fin k => executionForms program G (w, enc)
        (Fin.castLE hk i)) := by
    funext i
    exact formsFromTranscript_takeAt program
      (executionLabels program G (w, enc)) seedForms k h2 hk i
  rw [hforms]
  exact execution_live_iff_eligible_prefix program G hinj (w, enc) hk

/-- The actual live-set cardinality equals the sum of exact encoding
fibers over visible label buckets and eligible scalars. -/
theorem execution_live_card_eq_bucket_mass {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (h2 : 2 ≤ k) (hk : k ≤ m) :
    (liveSet (firstHit (executionHit (F := F) program G)) k).card =
      bucketMass
        (executionPrefixBucket (F := F) program G hk)
        (fun labels w => w ∈ eligible
          (formsInBucket (F := F) program h2 hk labels)) := by
  classical
  let S := liveSet (firstHit (executionHit (F := F) program G)) k
  let bucket : F → (A ≃ L) → (Fin k → L) :=
    executionPrefixBucket (F := F) program G hk
  let good := fun labels w => w ∈ eligible
    (formsInBucket (F := F) program h2 hk labels)
  letI : DecidablePred (fun ω : F × (A ≃ L) =>
      good (bucket ω.1 ω.2) ω.1) := Classical.decPred _
  have hpred (ω : F × (A ≃ L)) :
      ω ∈ S ↔ good (bucket ω.1 ω.2) ω.1 :=
    execution_live_iff_bucket_eligible program G hinj h2 hk ω.1 ω.2
  let Φ : S ≃ {ω : F × (A ≃ L) // good (bucket ω.1 ω.2) ω.1} := {
    toFun := fun ω => ⟨ω.1, (hpred ω.1).mp ω.2⟩
    invFun := fun ω => ⟨ω.1, (hpred ω.1).mpr ω.2⟩
    left_inv := by intro ω; apply Subtype.ext; rfl
    right_inv := by intro ω; apply Subtype.ext; rfl
  }
  calc
    S.card = Fintype.card S := (Fintype.card_coe S).symm
    _ = Fintype.card {ω : F × (A ≃ L) //
          good (bucket ω.1 ω.2) ω.1} := Fintype.card_congr Φ
    _ = acceptedCount bucket good := by
      unfold acceptedCount
      rfl
    _ = bucketMass bucket good := accepted_count_eq_bucket_mass bucket good

/-- The affine form placed at position `i` uses only labels from positions
strictly earlier than `i`, even in a label-dependent program. -/
theorem form_at_depends_on_earlier_labels {F L : Type*} [Field F]
    {n m : ℕ} (program : Program L n m)
    (forms : Fin n → Affine F) (labels₁ labels₂ : Fin m → L)
    (i : Fin m)
    (hagree : ∀ j : Fin m, j < i → labels₁ j = labels₂ j) :
    formsFromTranscript program labels₁ forms i =
      formsFromTranscript program labels₂ forms i := by
  induction program with
  | done => rfl
  | @step n m choose tail ih =>
      by_cases hi : i.val < n
      · let i0 : Fin n := ⟨i.val, hi⟩
        have hcast : Fin.castLE
            (programLe (Program.step choose tail)) i0 = i := Fin.ext rfl
        calc
          formsFromTranscript (.step choose tail) labels₁ forms i =
              forms i0 := by
            rw [← hcast]
            exact formsFromTranscript_prefix (.step choose tail) labels₁ forms i0
          _ = formsFromTranscript (.step choose tail) labels₂ forms i := by
            rw [← hcast]
            exact (formsFromTranscript_prefix
              (.step choose tail) labels₂ forms i0).symm
      · have hcmd : choose (prefixLabels (.step choose tail) labels₁) =
            choose (prefixLabels (.step choose tail) labels₂) := by
          congr 1
          funext j
          apply hagree
          change j.val < i.val
          have hj : j.val < n := j.isLt
          omega
        simp only [formsFromTranscript, hcmd]
        exact ih (Fin.snoc forms
          (formOp (choose (prefixLabels (.step choose tail) labels₂)).op
            (forms (choose (prefixLabels (.step choose tail) labels₂)).lhs)
            (forms (choose (prefixLabels (.step choose tail) labels₂)).rhs)))
          labels₁ labels₂ i hagree

/-- Extend a visible prefix with any fixed label for positions not yet
observed. Causality makes the next form independent of that choice. -/
def extendBucket {L : Type*} {m k : ℕ}
    (fallback : L) (labels : Fin k → L) : Fin m → L :=
  fun i => if h : i.val < k then labels ⟨i.val, h⟩ else fallback

def nextFormInBucket {F L : Type*} [Field F] {m k : ℕ}
    (program : Program L 2 m) (hk : k < m)
    (fallback : L) (labels : Fin k → L) : Affine F :=
  formsFromTranscript program (extendBucket (m := m) fallback labels)
    seedForms ⟨k, hk⟩

/-- The next form in an actual execution equals the form reconstructed
from its visible prefix and any suffix completion. -/
theorem execution_next_form_eq_bucket {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A) (hk : k < m)
    (fallback : L) (w : F) (enc : A ≃ L) :
    executionForms program G (w, enc) ⟨k, hk⟩ =
      nextFormInBucket (F := F) program hk fallback
        (executionPrefixBucket program G (Nat.le_of_lt hk) w enc) := by
  unfold executionForms nextFormInBucket
  apply form_at_depends_on_earlier_labels
  intro j hj
  have hjk : j.val < k := hj
  simp [extendBucket, hjk, executionPrefixBucket, restrictLabels]

/-- The first-hit predicate at stage `k` is determined by the scalar and
visible prefix bucket: eligibility and one next-form candidate root. -/
theorem execution_first_hit_iff_bucket_candidates {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (h2 : 2 ≤ k) (hk : k < m) (fallback : L)
    (w : F) (enc : A ≃ L) :
    firstHit (executionHit program G) (w, enc) = some k ↔
      w ∈ eligible
          (formsInBucket (F := F) program h2 (Nat.le_of_lt hk)
            (executionPrefixBucket program G (Nat.le_of_lt hk) w enc)) ∩
        nextCandidates
          (formsInBucket (F := F) program h2 (Nat.le_of_lt hk)
            (executionPrefixBucket program G (Nat.le_of_lt hk) w enc))
          (nextFormInBucket (F := F) program hk fallback
            (executionPrefixBucket program G (Nat.le_of_lt hk) w enc)) := by
  have hforms : formsInBucket (F := F) program h2 (Nat.le_of_lt hk)
      (executionPrefixBucket program G (Nat.le_of_lt hk) w enc) =
      (fun i : Fin k => executionForms program G (w, enc)
        (Fin.castLE (Nat.le_of_lt hk) i)) := by
    funext i
    exact formsFromTranscript_takeAt program
      (executionLabels program G (w, enc)) seedForms k h2
      (Nat.le_of_lt hk) i
  have hnew := execution_next_form_eq_bucket program G hk fallback w enc
  have hfirst := execution_first_hit_iff_eligible_next program G hinj
    (w, enc) (⟨k, hk⟩ : Fin m)
  simpa only [hforms, hnew] using hfirst

/-- The actual first-hit set at a stage equals the sum of exact prefix
encoding fibers over eligible next-candidate scalars. -/
theorem execution_hit_card_eq_bucket_mass {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (h2 : 2 ≤ k) (hk : k < m) (fallback : L) :
    (hitSet (firstHit (executionHit (F := F) program G)) k).card =
      bucketMass
        (executionPrefixBucket (F := F) program G (Nat.le_of_lt hk))
        (fun labels w => w ∈ eligible
          (formsInBucket (F := F) program h2 (Nat.le_of_lt hk) labels) ∩
          nextCandidates
            (formsInBucket (F := F) program h2 (Nat.le_of_lt hk) labels)
            (nextFormInBucket (F := F) program hk fallback labels)) := by
  classical
  let S := hitSet (firstHit (executionHit (F := F) program G)) k
  let bucket : F → (A ≃ L) → (Fin k → L) :=
    executionPrefixBucket (F := F) program G (Nat.le_of_lt hk)
  let good := fun labels w => w ∈ eligible
    (formsInBucket (F := F) program h2 (Nat.le_of_lt hk) labels) ∩
    nextCandidates
      (formsInBucket (F := F) program h2 (Nat.le_of_lt hk) labels)
      (nextFormInBucket (F := F) program hk fallback labels)
  letI : DecidablePred (fun ω : F × (A ≃ L) =>
      good (bucket ω.1 ω.2) ω.1) := Classical.decPred _
  have hpred (ω : F × (A ≃ L)) :
      ω ∈ S ↔ good (bucket ω.1 ω.2) ω.1 := by
    simpa only [S, hitSet, Finset.mem_filter, Finset.mem_univ, true_and]
      using execution_first_hit_iff_bucket_candidates
        program G hinj h2 hk fallback ω.1 ω.2
  let Φ : S ≃ {ω : F × (A ≃ L) // good (bucket ω.1 ω.2) ω.1} := {
    toFun := fun ω => ⟨ω.1, (hpred ω.1).mp ω.2⟩
    invFun := fun ω => ⟨ω.1, (hpred ω.1).mpr ω.2⟩
    left_inv := by intro ω; apply Subtype.ext; rfl
    right_inv := by intro ω; apply Subtype.ext; rfl
  }
  calc
    S.card = Fintype.card S := (Fintype.card_coe S).symm
    _ = Fintype.card {ω : F × (A ≃ L) //
          good (bucket ω.1 ω.2) ω.1} := Fintype.card_congr Φ
    _ = acceptedCount bucket good := by unfold acceptedCount; rfl
    _ = bucketMass bucket good := accepted_count_eq_bucket_mass bucket good

#print axioms encodingFiber
#print axioms acceptedCount
#print axioms bucketMass
#print axioms accepted_count_eq_bucket_mass
#print axioms executionPrefixBucket
#print axioms formsInBucket
#print axioms execution_live_iff_bucket_eligible
#print axioms execution_live_card_eq_bucket_mass
#print axioms form_at_depends_on_earlier_labels
#print axioms extendBucket
#print axioms nextFormInBucket
#print axioms execution_next_form_eq_bucket
#print axioms execution_first_hit_iff_bucket_candidates
#print axioms execution_hit_card_eq_bucket_mass

end XedniBucketFiberPartition
