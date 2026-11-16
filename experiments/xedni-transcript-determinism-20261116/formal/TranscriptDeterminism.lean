import AdaptiveProgramInvariant

namespace XedniTranscriptDeterminism

open XedniAdaptiveProgramInvariant XedniSymbolicCollision

/-- The final trace of a typed program contains its initial trace. -/
def programLe {L : Type*} {n m : ℕ} :
    Program L n m → n ≤ m
  | .done => Nat.le_refl _
  | .step _ tail => (Nat.le_succ _).trans (programLe tail)

def prefixLabels {L : Type*} {n m : ℕ}
    (program : Program L n m) (labels : Fin m → L) : Fin n → L :=
  fun i => labels (Fin.castLE (programLe program) i)

/-- The affine trace determined by a complete visible label transcript.
This construction does not inspect the target scalar or group encoding. -/
def formsFromTranscript {F L : Type*} [Field F] {n m : ℕ}
    (program : Program L n m) (labels : Fin m → L)
    (forms : Fin n → Affine F) : Fin m → Affine F :=
  match program with
  | .done => forms
  | .step choose tail =>
      let cmd := choose (prefixLabels (.step choose tail) labels)
      formsFromTranscript tail labels
        (Fin.snoc forms (formOp cmd.op (forms cmd.lhs) (forms cmd.rhs)))

/-- The group run preserves every original point in its original position. -/
theorem runGroup_prefix {A L : Type*} [AddGroup A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (points : Fin n → A) (i : Fin n) :
    runGroup program enc points (Fin.castLE (programLe program) i) = points i := by
  induction program with
  | done => rfl
  | step choose tail ih =>
      simpa [runGroup, programLe, Fin.snoc_castSucc] using
        ih (Fin.snoc points
          (pointOp (choose (fun j => enc (points j))).op
            (points (choose (fun j => enc (points j))).lhs)
            (points (choose (fun j => enc (points j))).rhs))) i.castSucc

/-- Once the full visible transcript is fixed, the corresponding affine
form sequence is determined by those labels and the program alone. -/
theorem runForms_eq_transcript {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (G : A) (w : F) (forms : Fin n → Affine F)
    (points : Fin n → A) (labels : Fin m → L)
    (hinit : ∀ i, points i = (eval (forms i) w) • G)
    (hlabels : ∀ i, labels i = enc (runGroup program enc points i)) :
    runForms program enc G w forms =
      formsFromTranscript program labels forms := by
  induction program with
  | done => rfl
  | step choose tail ih =>
      let cmd := choose (fun i => enc (points i))
      have hsym :
          choose (fun i => enc ((eval (forms i) w) • G)) = cmd := by
        dsimp [cmd]
        congr 1
        funext i
        rw [← hinit i]
      have htrans :
          choose (prefixLabels (.step choose tail) labels) = cmd := by
        dsimp [cmd]
        congr 1
        funext i
        change labels (Fin.castLE (programLe (Program.step choose tail)) i) =
          enc (points i)
        rw [hlabels (Fin.castLE (programLe (Program.step choose tail)) i)]
        rw [runGroup_prefix]
      let nextPoint : A :=
        XedniAdaptiveProgramInvariant.pointOp cmd.op
          (points cmd.lhs) (points cmd.rhs)
      let nextForm : Affine F :=
        XedniAdaptiveProgramInvariant.formOp cmd.op
          (forms cmd.lhs) (forms cmd.rhs)
      let nextPoints := Fin.snoc (α := fun _ => A) points nextPoint
      let nextForms := Fin.snoc (α := fun _ => Affine F) forms nextForm
      have hstep : ∀ i, nextPoints i = (eval (nextForms i) w) • G := by
        intro i
        refine Fin.lastCases ?_ ?_ i
        · simp [nextPoints, nextForms, nextPoint, nextForm,
            Fin.snoc_last, op_commutes, hinit]
        · intro j
          simp [nextPoints, nextForms, Fin.snoc_castSucc, hinit]
      have hlabelsTail :
          ∀ i, labels i = enc (runGroup tail enc nextPoints i) := by
        intro i
        simpa [runGroup, nextPoints, cmd] using hlabels i
      simp only [runForms, formsFromTranscript, hsym, htrans]
      change runForms tail enc G w nextForms =
        formsFromTranscript tail labels nextForms
      exact ih nextForms nextPoints labels hstep hlabelsTail

/-- On public DLP inputs, the symbolic form trace depends only on the
observed complete label transcript. -/
theorem dlp_forms_from_transcript {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (w : F) (labels : Fin m → L)
    (hlabels : ∀ i, labels i =
      enc (runGroup program enc (seedPoints G w) i)) :
    runForms program enc G w seedForms =
      formsFromTranscript program labels seedForms := by
  exact runForms_eq_transcript program enc G w seedForms
    (seedPoints G w) labels (seed_invariant G w) hlabels

/-- The actual group transcript is the evaluation of forms reconstructed
from the observed labels, for every public DLP scalar consistent with them. -/
theorem dlp_group_from_transcript {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (w : F) (labels : Fin m → L)
    (hlabels : ∀ i, labels i =
      enc (runGroup program enc (seedPoints G w) i)) :
    ∀ i, runGroup program enc (seedPoints G w) i =
      (eval (formsFromTranscript program labels seedForms i) w) • G := by
  intro i
  rw [← dlp_forms_from_transcript program enc G w labels hlabels]
  exact dlp_program_invariant program enc G w i

/-- An informative equality of actual group elements in a fixed visible
transcript puts the hidden scalar in that transcript's symbolic candidate
set. -/
theorem dlp_collision_mem_candidates {F A L : Type*}
    [Fintype F] [DecidableEq F] [Field F]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (hinj : Function.Injective (fun s : F => s • G))
    (w : F) (labels : Fin m → L)
    (hlabels : ∀ k, labels k =
      enc (runGroup program enc (seedPoints G w) k))
    (i j : Fin m) (hij : i < j)
    (hdistinct : formsFromTranscript program labels (seedForms (F := F)) i ≠
      formsFromTranscript program labels (seedForms (F := F)) j)
    (hhit : runGroup program enc (seedPoints G w) i =
      runGroup program enc (seedPoints G w) j) :
    w ∈ collisionSet (formsFromTranscript program labels (seedForms (F := F))) := by
  classical
  let forms := formsFromTranscript program labels (seedForms (F := F))
  have heq : eval (forms i) w = eval (forms j) w := by
    apply hinj
    simpa only [forms, ← dlp_group_from_transcript program enc G w labels hlabels] using hhit
  have hs : (forms i).slope ≠ (forms j).slope := by
    intro hs
    exact (same_slope_distinct_ne (forms i) (forms j) hs hdistinct w) heq
  rw [collision_set_eq_candidates]
  have hp : (i, j) ∈ activePairs forms := by
    simp [activePairs, hij, hs]
  have hc : w = candidate (forms i) (forms j) :=
    (unequal_slope_eq_iff_candidate (forms i) (forms j) hs w).mp heq
  exact Finset.mem_image.mpr ⟨(i, j), hp, hc.symm⟩

/-- At a fixed visible transcript, the informative candidate set has at
most the number of ordered form pairs. -/
theorem transcript_candidate_bound {F L : Type*}
    [Fintype F] [DecidableEq F] [Field F] {m : ℕ}
    (program : Program L 2 m) (labels : Fin m → L) :
    (collisionSet (formsFromTranscript program labels (seedForms (F := F)))).card ≤
      m * m := by
  exact symbolic_collision_bound _

#print axioms programLe
#print axioms prefixLabels
#print axioms formsFromTranscript
#print axioms runGroup_prefix
#print axioms runForms_eq_transcript
#print axioms dlp_forms_from_transcript
#print axioms dlp_group_from_transcript
#print axioms dlp_collision_mem_candidates
#print axioms transcript_candidate_bound

end XedniTranscriptDeterminism
