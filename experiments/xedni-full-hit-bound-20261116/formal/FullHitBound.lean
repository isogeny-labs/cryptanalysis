import AdaptiveTotalBound

namespace XedniFullHitBound

open XedniAdaptiveProgramInvariant XedniAdaptiveStageSum
open XedniFirstHitPartition XedniTranscriptDeterminism
open XedniTranscriptFiberEquivalence XedniSymbolicCollision
open XedniAdaptiveTotalBound

set_option linter.style.haveILetI false

/-- An informative group equality cannot first arise at the initial point. -/
theorem execution_hit_zero_false {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (ω : F × (A ≃ L)) :
    ¬ executionHit program G
      (Fin.castLE (programLe program) (0 : Fin 2)) ω := by
  intro ⟨i, hi, _, _⟩
  change (i : ℕ) < (Fin.castLE (programLe program) (0 : Fin 2)).val at hi
  simp only [Fin.val_castLE] at hi
  norm_num at hi

/-- The informative equality of the two seed points is precisely
the scalar `1`, independently of the encoding and later program. -/
theorem execution_hit_seed_iff {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (ω : F × (A ≃ L)) :
    executionHit program G
      (Fin.castLE (programLe program) (1 : Fin 2)) ω ↔ ω.1 = 1 := by
  let j0 : Fin m := Fin.castLE (programLe program) (0 : Fin 2)
  let j1 : Fin m := Fin.castLE (programLe program) (1 : Fin 2)
  have hp0 : runGroup program ω.2 (seedPoints G ω.1) j0 = G := by
    simpa [j0, seedPoints] using
      runGroup_prefix program ω.2 (seedPoints G ω.1) (0 : Fin 2)
  have hp1 : runGroup program ω.2 (seedPoints G ω.1) j1 = ω.1 • G := by
    simpa [j1, seedPoints] using
      runGroup_prefix program ω.2 (seedPoints G ω.1) (1 : Fin 2)
  have hf0 : executionForms program G ω j0 = seedForms (F := F) (0 : Fin 2) := by
    exact formsFromTranscript_prefix program (executionLabels program G ω)
      seedForms (0 : Fin 2)
  have hf1 : executionForms program G ω j1 = seedForms (F := F) (1 : Fin 2) := by
    exact formsFromTranscript_prefix program (executionLabels program G ω)
      seedForms (1 : Fin 2)
  have hforms : executionForms program G ω j0 ≠ executionForms program G ω j1 := by
    rw [hf0, hf1]
    intro h
    have hs := congrArg Affine.slope h
    simpa [seedForms] using hs
  have h01 : j0 < j1 := by
    change (0 : ℕ) < 1
    omega
  have hearlier (i : Fin m) (hi : i < j1) : i = j0 := by
    change (i : ℕ) < j1.val at hi
    simp only [j1, Fin.val_castLE] at hi
    norm_num at hi
    apply Fin.ext
    change (i : ℕ) = 0
    omega
  change groupRawHit (runGroup program ω.2 (seedPoints G ω.1))
    (executionForms program G ω) j1 ↔ ω.1 = 1
  constructor
  · rintro ⟨i, hi, _, hp⟩
    have hidx := hearlier i hi
    subst i
    rw [hp0, hp1] at hp
    apply hinj
    simpa using hp.symm
  · intro hw
    refine ⟨j0, h01, hforms, ?_⟩
    rw [hp0, hp1, hw]
    simp

/-- The first informative hit is at the second seed point exactly when
the public point is `G` itself. -/
theorem execution_first_hit_seed_iff {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (ω : F × (A ≃ L)) :
    firstHit (executionHit program G) ω = some 1 ↔ ω.1 = 1 := by
  let j0 : Fin m := Fin.castLE (programLe program) (0 : Fin 2)
  let j1 : Fin m := Fin.castLE (programLe program) (1 : Fin 2)
  have hprior (j : Fin m) (hj : j < j1) :
      ¬ executionHit program G j ω := by
    have hval : (j : ℕ) = 0 := by
      change (j : ℕ) < j1.val at hj
      simp only [j1, Fin.val_castLE] at hj
      norm_num at hj
      exact hj
    have heq : j = j0 := by
      apply Fin.ext
      change (j : ℕ) = 0
      omega
    subst j
    exact execution_hit_zero_false program G ω
  have hfirst := firstHit_eq_some_iff (executionHit program G) ω j1
  have hjval : j1.val = 1 := by rfl
  rw [hjval] at hfirst
  rw [hfirst]
  constructor
  · intro h
    exact (execution_hit_seed_iff program G hinj ω).mp h.1
  · intro hw
    exact ⟨(execution_hit_seed_iff program G hinj ω).mpr hw, hprior⟩

/-- There is no first informative hit at the first seed point. -/
theorem execution_first_hit_zero_false {F A L : Type*}
    [Field F] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (ω : F × (A ≃ L)) :
    firstHit (executionHit program G) ω ≠ some 0 := by
  let j0 : Fin m := Fin.castLE (programLe program) (0 : Fin 2)
  have hfirst := firstHit_eq_some_iff (executionHit program G) ω j0
  have hjval : j0.val = 0 := by rfl
  rw [hjval] at hfirst
  intro h
  exact execution_hit_zero_false program G ω (hfirst.mp h).1

/-- Exactly one scalar, paired with every bijective encoding, produces
a first informative hit at the second seed point. -/
theorem execution_seed_hit_card {F A L : Type*}
    [Fintype F] [Field F] [Fintype A] [Fintype L]
    [Fintype (A ≃ L)] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G)) :
    (hitSet (firstHit (executionHit (F := F) program G)) 1).card =
      Fintype.card (A ≃ L) := by
  classical
  let S := hitSet (firstHit (executionHit (F := F) program G)) 1
  have hmem (ω : F × (A ≃ L)) : ω ∈ S ↔ ω.1 = 1 := by
    simpa only [S, hitSet, Finset.mem_filter, Finset.mem_univ, true_and] using
      execution_first_hit_seed_iff program G hinj ω
  let Φ : S ≃ (A ≃ L) := {
    toFun := fun x => x.1.2
    invFun := fun enc => ⟨(1, enc), (hmem (1, enc)).mpr rfl⟩
    left_inv := by
      intro x
      rcases x with ⟨⟨w, enc⟩, hw⟩
      have h : w = 1 := (hmem (w, enc)).mp hw
      subst w
      rfl
    right_inv := by intro enc; rfl
  }
  change S.card = Fintype.card (A ≃ L)
  calc
    S.card = Fintype.card S := (Fintype.card_coe S).symm
    _ = Fintype.card (A ≃ L) := Fintype.card_congr Φ

/-- The full first-hit count is the exact seed mass plus the late-stage
first-hit count. -/
theorem execution_total_hit_decomposition {F A L : Type*}
    [Fintype F] [Field F] [Fintype A] [Fintype L]
    [Fintype (A ≃ L)] [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G)) :
    (∑ k ∈ Finset.range m,
      (hitSet (firstHit (executionHit (F := F) program G)) k).card) =
      Fintype.card (A ≃ L) +
        ∑ k ∈ Finset.Ico 2 m,
          (hitSet (firstHit (executionHit (F := F) program G)) k).card := by
  classical
  let first := firstHit (executionHit (F := F) program G)
  have hzero : (hitSet first 0).card = 0 := by
    have hset : hitSet first 0 = ∅ := by
      ext ω
      simp [hitSet, first, execution_first_hit_zero_false program G ω]
    simp [hset]
  have hone : (hitSet first 1).card = Fintype.card (A ≃ L) :=
    execution_seed_hit_card program G hinj
  change (∑ k ∈ Finset.range m, (hitSet first k).card) =
    Fintype.card (A ≃ L) +
      ∑ k ∈ Finset.Ico 2 m, (hitSet first k).card
  have h2 : 2 ≤ m := programLe program
  calc
    (∑ k ∈ Finset.range m, (hitSet first k).card) =
      (∑ k ∈ Finset.range 2, (hitSet first k).card) +
        ∑ k ∈ Finset.Ico 2 m, (hitSet first k).card :=
          (Finset.sum_range_add_sum_Ico _ h2).symm
    _ = Fintype.card (A ≃ L) +
        ∑ k ∈ Finset.Ico 2 m, (hitSet first k).card := by
          simp [Finset.sum_range_succ, hzero, hone]

/-- For uniform scalar and bijective encoding, every informative group
equality over the whole typed program obeys one seed term plus the
quadratic late-stage term. -/
theorem execution_all_hit_bound {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [Fintype A] [Fintype L] [Fintype (A ≃ L)]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A)
    (hinj : Function.Injective (fun s : F => s • G))
    (fallback : L) :
    (Fintype.card F - m * m) *
      (∑ k ∈ Finset.range m,
        (hitSet (firstHit (executionHit (F := F) program G)) k).card) ≤
    ((Fintype.card F - m * m) + m * m * Fintype.card F) *
      Fintype.card (A ≃ L) := by
  rw [execution_total_hit_decomposition program G hinj]
  have hlate := execution_late_total_bound program G hinj fallback
  rw [Fintype.card_prod] at hlate
  calc
    (Fintype.card F - m * m) *
        (Fintype.card (A ≃ L) +
          ∑ k ∈ Finset.Ico 2 m,
            (hitSet (firstHit (executionHit (F := F) program G)) k).card) =
      (Fintype.card F - m * m) * Fintype.card (A ≃ L) +
        (Fintype.card F - m * m) *
          ∑ k ∈ Finset.Ico 2 m,
            (hitSet (firstHit (executionHit (F := F) program G)) k).card :=
              Nat.mul_add _ _ _
    _ ≤ (Fintype.card F - m * m) * Fintype.card (A ≃ L) +
        m * m * (Fintype.card F * Fintype.card (A ≃ L)) :=
          Nat.add_le_add_left hlate _
    _ = ((Fintype.card F - m * m) + m * m * Fintype.card F) *
        Fintype.card (A ≃ L) := by ring

#print axioms execution_hit_zero_false
#print axioms execution_hit_seed_iff
#print axioms execution_first_hit_seed_iff
#print axioms execution_first_hit_zero_false
#print axioms execution_seed_hit_card
#print axioms execution_total_hit_decomposition
#print axioms execution_all_hit_bound

end XedniFullHitBound
