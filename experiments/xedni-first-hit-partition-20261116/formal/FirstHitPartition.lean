import StageHitEquivalence

namespace XedniFirstHitPartition

open XedniAdaptiveStageSum XedniStageHitEquivalence
open XedniPrefixPatternBridge XedniSymbolicCollision
open XedniAdaptiveProgramInvariant XedniTranscriptDeterminism

/-- The finite set of stages at which an execution has an informative hit. -/
noncomputable def hitStages {Ω : Type*} {m : ℕ}
    (hit : Fin m → Ω → Prop) (ω : Ω) : Finset (Fin m) := by
  classical
  exact Finset.univ.filter (fun i => hit i ω)

/-- The first informative hit, or `none` when the execution has none. -/
noncomputable def firstHit {Ω : Type*} {m : ℕ}
    (hit : Fin m → Ω → Prop) (ω : Ω) : Option ℕ := by
  classical
  let s := hitStages hit ω
  exact if hs : s.Nonempty then some (s.min' hs).val else none

/-- First-hit time is characterized by a hit now and no hit earlier. -/
theorem firstHit_eq_some_iff {Ω : Type*} {m : ℕ}
    (hit : Fin m → Ω → Prop) (ω : Ω) (i : Fin m) :
    firstHit hit ω = some i.val ↔
      hit i ω ∧ ∀ j : Fin m, j < i → ¬ hit j ω := by
  classical
  let s := hitStages hit ω
  have hmem (j : Fin m) : j ∈ s ↔ hit j ω := by
    simp [s, hitStages]
  constructor
  · intro h
    change (if hs : s.Nonempty then some (s.min' hs).val else none) =
      some i.val at h
    split_ifs at h with hs
    · have hmin : s.min' hs = i := Fin.ext (Option.some.inj h)
      constructor
      · exact (hmem i).mp (hmin ▸ s.min'_mem hs)
      · intro j hj hh
        have hle := s.min'_le j ((hmem j).mpr hh)
        rw [hmin] at hle
        exact (not_lt_of_ge hle) hj
  · rintro ⟨hi, hprior⟩
    have hs : s.Nonempty := ⟨i, (hmem i).mpr hi⟩
    have hle : s.min' hs ≤ i := s.min'_le i ((hmem i).mpr hi)
    have hge : i ≤ s.min' hs := by
      by_contra hn
      have hlt : s.min' hs < i := lt_of_not_ge hn
      exact hprior (s.min' hs) hlt ((hmem _).mp (s.min'_mem hs))
    have heq : s.min' hs = i := le_antisymm hle hge
    simp [firstHit, s, hs, heq]

/-- The live set at stage `k` consists exactly of executions with no
informative hit at any stage strictly before `k`. -/
theorem mem_live_iff_no_prior {Ω : Type*} [Fintype Ω]
    {m : ℕ} (hit : Fin m → Ω → Prop) (ω : Ω) (k : ℕ) :
    ω ∈ liveSet (firstHit hit) k ↔
      ∀ j : Fin m, j.val < k → ¬ hit j ω := by
  classical
  let s := hitStages hit ω
  have hmem (j : Fin m) : j ∈ s ↔ hit j ω := by
    simp [s, hitStages]
  simp only [liveSet, Finset.mem_filter, Finset.mem_univ, true_and]
  change (match firstHit hit ω with
    | none => True
    | some j => k ≤ j) ↔ _
  by_cases hs : s.Nonempty
  · have hfirst : firstHit hit ω = some (s.min' hs).val := by
      simp [firstHit, s, hs]
    rw [hfirst]
    simp only
    constructor
    · intro h j hj hh
      have hle := s.min'_le j ((hmem j).mpr hh)
      have hle' : (s.min' hs).val ≤ j.val := hle
      omega
    · intro h
      by_contra hn
      have hlt : (s.min' hs).val < k := by omega
      exact h (s.min' hs) hlt ((hmem _).mp (s.min'_mem hs))
  · have hfirst : firstHit hit ω = none := by
      simp [firstHit, s, hs]
    rw [hfirst]
    simp only
    constructor
    · intro _ j _ hj
      exact hs ⟨j, (hmem j).mpr hj⟩
    · intro _
      trivial

/-- An initial public-point equality is exactly the scalar-one case
when scalar multiplication by `G` is injective. -/
theorem initial_group_equality_iff_one {F A : Type*}
    [Field F] [AddCommGroup A] [Module F A]
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (w : F) : G = w • G ↔ w = 1 := by
  constructor
  · intro h
    have h' : (1 : F) • G = w • G := by simpa using h
    exact (hinj h').symm
  · intro h
    subst w
    simp

/-- A raw hit at position `j` is an equality with an earlier, distinct
affine form. This includes the initial equality between `G` and `Q`. -/
def rawHit {F : Type*} [Field F] {n : ℕ}
    (forms : Fin n → Affine F) (w : F) (j : Fin n) : Prop :=
  ∃ i : Fin n, i < j ∧ forms i ≠ forms j ∧
    eval (forms i) w = eval (forms j) w

/-- Eligibility of an entire old trace is equivalent to the absence of
every earlier informative raw equality, including known form repeats. -/
theorem eligible_iff_no_raw_hit {F : Type*}
    [Fintype F] [DecidableEq F] [Field F] {n : ℕ}
    (forms : Fin n → Affine F) (w : F) :
    w ∈ eligible forms ↔ ∀ j : Fin n, ¬ rawHit forms w j := by
  rw [eligible_iff_eval_pattern]
  constructor
  · intro h j
    rintro ⟨i, _, hne, heq⟩
    exact hne ((h i j).mp heq)
  · intro h i j
    constructor
    · intro heq
      by_cases hij : i = j
      · exact congrArg forms hij
      · rcases lt_or_gt_of_ne hij with hlt | hgt
        · by_contra hne
          exact h j ⟨i, hlt, hne, heq⟩
        · by_contra hne
          exact h i ⟨j, hgt, Ne.symm hne, heq.symm⟩
    · intro hforms
      rw [hforms]

/-- Eligibility of a prefix is equivalent to no raw hit before its cutoff
in the complete form list. -/
theorem eligible_prefix_iff_no_prior {F : Type*}
    [Fintype F] [DecidableEq F] [Field F] {m k : ℕ}
    (forms : Fin m → Affine F) (w : F) (hk : k ≤ m) :
    w ∈ eligible (fun i : Fin k => forms (Fin.castLE hk i)) ↔
      ∀ j : Fin m, j.val < k → ¬ rawHit forms w j := by
  rw [eligible_iff_no_raw_hit]
  constructor
  · intro h j hj
    rintro ⟨i, hij, hne, heq⟩
    let ii : Fin k := ⟨i.val, by omega⟩
    let jj : Fin k := ⟨j.val, hj⟩
    have hii : Fin.castLE hk ii = i := Fin.ext rfl
    have hjj : Fin.castLE hk jj = j := Fin.ext rfl
    apply h jj
    exact ⟨ii, by simpa [ii, jj] using hij,
      by simpa only [hii, hjj] using hne,
      by simpa only [hii, hjj] using heq⟩
  · intro h j
    rintro ⟨i, hij, hne, heq⟩
    let ii : Fin m := Fin.castLE hk i
    let jj : Fin m := Fin.castLE hk j
    have hjk : jj.val < k := j.isLt
    apply h jj hjk
    exact ⟨ii, by simpa [ii, jj] using hij, hne, heq⟩

/-- The first-hit live set is exactly the eligible prefix set, pointwise,
even when the complete form list depends on the execution. -/
theorem mem_live_raw_iff_eligible_prefix {F Ω : Type*}
    [Fintype F] [DecidableEq F] [Field F] [Fintype Ω]
    {m k : ℕ} (forms : Ω → Fin m → Affine F)
    (scalar : Ω → F) (ω : Ω) (hk : k ≤ m) :
    ω ∈ liveSet (firstHit (fun j x => rawHit (forms x) (scalar x) j)) k ↔
      scalar ω ∈ eligible
        (fun i : Fin k => forms ω (Fin.castLE hk i)) := by
  rw [mem_live_iff_no_prior]
  exact (eligible_prefix_iff_no_prior (forms ω) (scalar ω) hk).symm

/-- The group version of a raw informative hit, retaining the distinction
between a new equality and a repeat of the same affine form. -/
def groupRawHit {F A : Type*} {m : ℕ}
    (points : Fin m → A) (forms : Fin m → Affine F)
    (j : Fin m) : Prop :=
  ∃ i : Fin m, i < j ∧ forms i ≠ forms j ∧ points i = points j

/-- Scalar-to-group injectivity turns each raw group hit into exactly one
raw affine-form hit for a trace whose points evaluate those forms. -/
theorem groupRawHit_iff_rawHit {F A : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (forms : Fin m → Affine F) (points : Fin m → A)
    (w : F) (hpoints : ∀ i, points i = (eval (forms i) w) • G)
    (j : Fin m) :
    groupRawHit points forms j ↔ rawHit forms w j := by
  constructor
  · rintro ⟨i, hij, hne, heq⟩
    exact ⟨i, hij, hne, hinj (by simpa only [hpoints i, hpoints j] using heq)⟩
  · rintro ⟨i, hij, hne, heq⟩
    exact ⟨i, hij, hne, by rw [hpoints i, hpoints j, heq]⟩

/-- The raw hit in an actual adaptive public-input run agrees with the
hit of forms reconstructed from its own visible label transcript. -/
theorem dlp_group_raw_hit_iff {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (w : F) (labels : Fin m → L)
    (hlabels : ∀ i, labels i =
      enc (runGroup program enc (seedPoints G w) i))
    (j : Fin m) :
    groupRawHit (runGroup program enc (seedPoints G w))
      (formsFromTranscript program labels (seedForms (F := F))) j ↔
    rawHit (formsFromTranscript program labels (seedForms (F := F))) w j :=
  groupRawHit_iff_rawHit G hinj _ _ w
    (dlp_group_from_transcript program enc G w labels hlabels) j

/-- The complete visible labels for one scalar-and-encoding execution. -/
def executionLabels {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (ω : F × (A ≃ L)) : Fin m → L :=
  fun i => ω.2 (runGroup program ω.2 (seedPoints G ω.1) i)

/-- Forms reconstructed from the labels of that same execution. -/
def executionForms {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (ω : F × (A ≃ L)) : Fin m → Affine F :=
  formsFromTranscript program (executionLabels program G ω) seedForms

/-- The actual group hit at a specified stage of one execution. -/
def executionHit {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (j : Fin m) (ω : F × (A ≃ L)) : Prop :=
  groupRawHit (runGroup program ω.2 (seedPoints G ω.1))
    (executionForms program G ω) j

/-- In the complete scalar-and-encoding execution space, liveness at
stage `k` equals eligibility of the actual visible-trace prefix. -/
theorem execution_live_iff_eligible_prefix {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m k : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (ω : F × (A ≃ L)) (hk : k ≤ m) :
    ω ∈ liveSet (firstHit (executionHit program G)) k ↔
      ω.1 ∈ eligible
        (fun i : Fin k => executionForms program G ω (Fin.castLE hk i)) := by
  rw [mem_live_iff_no_prior]
  rw [eligible_prefix_iff_no_prior]
  have hhit (j : Fin m) : executionHit program G j ω ↔
      rawHit (executionForms program G ω) ω.1 j := by
    exact dlp_group_raw_hit_iff program ω.2 G hinj ω.1
      (executionLabels program G ω) (by intro i; rfl) j
  constructor
  · intro h j hj hraw
    exact h j hj ((hhit j).mpr hraw)
  · intro h j hj hgroup
    exact h j hj ((hhit j).mp hgroup)

/-- A raw hit at `j` is precisely membership in the candidate set
formed from all old forms at that stage. -/
theorem rawHit_iff_nextCandidates {F : Type*}
    [Fintype F] [DecidableEq F] [Field F] {m : ℕ}
    (forms : Fin m → Affine F) (w : F) (j : Fin m) :
    rawHit forms w j ↔
      w ∈ nextCandidates
        (fun i : Fin j.val => forms (Fin.castLE (Nat.le_of_lt j.isLt) i))
        (forms j) := by
  rw [← next_hit_iff_candidates]
  constructor
  · rintro ⟨i, hij, hne, heq⟩
    let ii : Fin j.val := ⟨i.val, hij⟩
    have hii : Fin.castLE (Nat.le_of_lt j.isLt) ii = i := Fin.ext rfl
    exact ⟨ii, by simpa only [hii] using hne,
      by simpa only [hii] using heq⟩
  · rintro ⟨i, hne, heq⟩
    let ii : Fin m := Fin.castLE (Nat.le_of_lt j.isLt) i
    exact ⟨ii, by change i.val < j.val; exact i.isLt, hne, heq⟩

/-- The exact first-hit event in an adaptive group execution is the
eligible next-root event for the visible old prefix. Stage one includes
the initial `G = Q` equality. -/
theorem execution_first_hit_iff_eligible_next {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (ω : F × (A ≃ L)) (j : Fin m) :
    firstHit (executionHit program G) ω = some j.val ↔
      ω.1 ∈ eligible
        (fun i : Fin j.val => executionForms program G ω
          (Fin.castLE (Nat.le_of_lt j.isLt) i)) ∩
        nextCandidates
          (fun i : Fin j.val => executionForms program G ω
            (Fin.castLE (Nat.le_of_lt j.isLt) i))
          (executionForms program G ω j) := by
  have hfirst := firstHit_eq_some_iff (executionHit program G) ω j
  have hlive := execution_live_iff_eligible_prefix program G hinj ω
    (Nat.le_of_lt j.isLt)
  have hgroup := dlp_group_raw_hit_iff program ω.2 G hinj ω.1
    (executionLabels program G ω) (by intro i; rfl) j
  have hnext := rawHit_iff_nextCandidates (executionForms program G ω) ω.1 j
  rw [hfirst]
  constructor
  · rintro ⟨hhit, hprior⟩
    apply Finset.mem_inter.mpr
    constructor
    · apply hlive.mp
      apply (mem_live_iff_no_prior (executionHit program G) ω j.val).mpr
      intro i hi
      exact hprior i (by exact hi)
    · exact hnext.mp (hgroup.mp hhit)
  · intro hw
    obtain ⟨helig, hcandidate⟩ := Finset.mem_inter.mp hw
    constructor
    · exact hgroup.mpr (hnext.mpr hcandidate)
    · intro i hi
      have hl := hlive.mpr helig
      exact (mem_live_iff_no_prior (executionHit program G) ω j.val).mp hl
        i hi

/-- Actual first-hit stages conserve execution mass at each cutoff. -/
theorem execution_stage_mass_flow {F A L : Type*}
    [Field F] [Fintype F] [Fintype A] [Fintype L]
    [Fintype (A ≃ L)] [AddCommGroup A] [Module F A]
    {m : ℕ} (program : Program L 2 m) (G : A) (k : ℕ) :
    (liveSet (firstHit (executionHit (F := F) program G)) (k+1)).card +
      (hitSet (firstHit (executionHit (F := F) program G)) k).card =
      (liveSet (firstHit (executionHit (F := F) program G)) k).card := by
  classical
  exact stop_flow (firstHit (executionHit (F := F) program G)) k

/-- Total first-hit mass plus surviving executions equals the full
scalar-and-encoding execution-space size. -/
theorem execution_total_mass_identity {F A L : Type*}
    [Field F] [Fintype F] [Fintype A] [Fintype L]
    [Fintype (A ≃ L)] [AddCommGroup A] [Module F A]
    {m : ℕ} (program : Program L 2 m) (G : A) :
    (liveSet (firstHit (executionHit (F := F) program G)) m).card +
      (∑ k ∈ Finset.range m,
        (hitSet (firstHit (executionHit (F := F) program G)) k).card) =
      Fintype.card (F × (A ≃ L)) := by
  classical
  exact stopped_mass_identity (firstHit (executionHit (F := F) program G)) m

#print axioms hitStages
#print axioms firstHit
#print axioms firstHit_eq_some_iff
#print axioms mem_live_iff_no_prior
#print axioms initial_group_equality_iff_one
#print axioms rawHit
#print axioms eligible_iff_no_raw_hit
#print axioms eligible_prefix_iff_no_prior
#print axioms mem_live_raw_iff_eligible_prefix
#print axioms groupRawHit
#print axioms groupRawHit_iff_rawHit
#print axioms dlp_group_raw_hit_iff
#print axioms executionLabels
#print axioms executionForms
#print axioms executionHit
#print axioms execution_live_iff_eligible_prefix
#print axioms rawHit_iff_nextCandidates
#print axioms execution_first_hit_iff_eligible_next
#print axioms execution_stage_mass_flow
#print axioms execution_total_mass_identity

end XedniFirstHitPartition
