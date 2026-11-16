import AdaptiveStageSum

namespace XedniTranscriptFiberEquivalence

open XedniAdaptiveProgramInvariant XedniTranscriptDeterminism
open XedniSymbolicCollision

/-- Reconstructing a complete trace from labels preserves every form
already present at the current program node. -/
theorem formsFromTranscript_prefix {F L : Type*} [Field F]
    {n m : ℕ} (program : Program L n m) (labels : Fin m → L)
    (forms : Fin n → Affine F) (i : Fin n) :
    formsFromTranscript program labels forms
      (Fin.castLE (programLe program) i) = forms i := by
  induction program with
  | done => rfl
  | step choose tail ih =>
      simpa [formsFromTranscript, programLe, Fin.snoc_castSucc] using
        ih labels (Fin.snoc forms
          (formOp (choose (prefixLabels (.step choose tail) labels)).op
            (forms (choose (prefixLabels (.step choose tail) labels)).lhs)
            (forms (choose (prefixLabels (.step choose tail) labels)).rhs))) i.castSucc

/-- If an encoding assigns every reconstructed affine point the prescribed
label, executing the adaptive group program follows exactly that label path. -/
theorem labels_of_symbolic_fiber {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (G : A) (w : F) (forms : Fin n → Affine F)
    (points : Fin n → A) (labels : Fin m → L)
    (hinit : ∀ i, points i = (eval (forms i) w) • G)
    (hsym : ∀ i, labels i = enc
      ((eval (formsFromTranscript program labels forms i) w) • G)) :
    ∀ i, labels i = enc (runGroup program enc points i) := by
  induction program with
  | done =>
      intro i
      simpa [formsFromTranscript, runGroup, hinit] using hsym i
  | step choose tail ih =>
      let cmd := choose (prefixLabels (.step choose tail) labels)
      have hprefix : ∀ i,
          prefixLabels (.step choose tail) labels i = enc (points i) := by
        intro i
        change labels (Fin.castLE (programLe (.step choose tail)) i) =
          enc (points i)
        rw [hsym (Fin.castLE (programLe (.step choose tail)) i)]
        rw [formsFromTranscript_prefix (.step choose tail) labels forms i]
        rw [hinit i]
      have hchoose : choose (fun i => enc (points i)) = cmd := by
        dsimp [cmd]
        congr 1
        funext i
        exact (hprefix i).symm
      let nextPoint : A :=
        pointOp cmd.op (points cmd.lhs) (points cmd.rhs)
      let nextForm : Affine F :=
        formOp cmd.op (forms cmd.lhs) (forms cmd.rhs)
      let nextPoints := Fin.snoc (α := fun _ => A) points nextPoint
      let nextForms := Fin.snoc (α := fun _ => Affine F) forms nextForm
      have hstep : ∀ i, nextPoints i = (eval (nextForms i) w) • G := by
        intro i
        refine Fin.lastCases ?_ ?_ i
        · simp [nextPoints, nextForms, nextPoint, nextForm,
            Fin.snoc_last, op_commutes, hinit]
        · intro j
          simp [nextPoints, nextForms, Fin.snoc_castSucc, hinit]
      have hsymTail : ∀ i, labels i = enc
          ((eval (formsFromTranscript tail labels nextForms i) w) • G) := by
        intro i
        simpa only [formsFromTranscript, cmd, nextForms] using hsym i
      have htail := ih nextForms nextPoints labels hstep hsymTail
      simpa only [runGroup, hchoose, nextPoints] using htail

/-- Actual label fibers and symbolic reconstructed-form fibers coincide
for every finite adaptive add/sub program, without an injective-trace
assumption. -/
theorem labels_iff_symbolic_fiber {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (G : A) (w : F) (forms : Fin n → Affine F)
    (points : Fin n → A) (labels : Fin m → L)
    (hinit : ∀ i, points i = (eval (forms i) w) • G) :
    (∀ i, labels i = enc (runGroup program enc points i)) ↔
    (∀ i, labels i = enc
      ((eval (formsFromTranscript program labels forms i) w) • G)) := by
  constructor
  · intro hlabels i
    rw [hlabels i]
    have hforms := runForms_eq_transcript program enc G w forms points
      labels hinit hlabels
    rw [← hforms]
    exact congrArg enc (run_invariant program enc G w forms points hinit i)
  · exact labels_of_symbolic_fiber program enc G w forms points labels hinit


/-- The exact number of encodings following a proposed adaptive transcript. -/
noncomputable def actualFiberCount {A L : Type*}
    [Fintype A] [Fintype L] [AddGroup A] {n m : ℕ}
    (program : Program L n m) (points : Fin n → A)
    (labels : Fin m → L) : ℕ := by
  classical
  exact Fintype.card {enc : A ≃ L //
    ∀ i, labels i = enc (runGroup program enc points i)}

noncomputable def symbolicFiberCount {F A L : Type*}
    [Field F] [Fintype A] [Fintype L]
    [AddCommGroup A] [Module F A] {n m : ℕ}
    (program : Program L n m) (G : A) (w : F)
    (forms : Fin n → Affine F) (labels : Fin m → L) : ℕ := by
  classical
  exact Fintype.card {enc : A ≃ L // ∀ i, labels i = enc
    ((eval (formsFromTranscript program labels forms i) w) • G)}

noncomputable def encodingCount {A L : Type*}
    [Fintype A] [Fintype L] : ℕ := by
  classical
  exact Fintype.card (A ≃ L)

/-- The symbolic reconstructed-form fiber has exactly the same encoding
count as the actual adaptive execution fiber. -/
theorem actual_fiber_count_eq_symbolic {F A L : Type*}
    [Field F] [Fintype A] [Fintype L]
    [AddCommGroup A] [Module F A] {n m : ℕ}
    (program : Program L n m) (G : A) (w : F)
    (forms : Fin n → Affine F) (points : Fin n → A)
    (labels : Fin m → L)
    (hinit : ∀ i, points i = (eval (forms i) w) • G) :
    actualFiberCount program points labels =
      symbolicFiberCount program G w forms labels := by
  classical
  let e : {enc : A ≃ L //
      ∀ i, labels i = enc (runGroup program enc points i)} ≃
      {enc : A ≃ L // ∀ i, labels i = enc
        ((eval (formsFromTranscript program labels forms i) w) • G)} := {
    toFun := fun ⟨enc, h⟩ =>
      ⟨enc, (labels_iff_symbolic_fiber program enc G w forms points labels hinit).mp h⟩
    invFun := fun ⟨enc, h⟩ =>
      ⟨enc, (labels_iff_symbolic_fiber program enc G w forms points labels hinit).mpr h⟩
    left_inv := by intro x; apply Subtype.ext; rfl
    right_inv := by intro x; apply Subtype.ext; rfl
  }
  exact Fintype.card_congr e

/-- At a fixed scalar, complete adaptive label fibers partition all
bijections. Each encoding occurs under its one actual label transcript. -/
theorem actual_fiber_partition {A L : Type*}
    [Fintype A] [Fintype L] [AddGroup A] {n m : ℕ}
    (program : Program L n m) (points : Fin n → A) :
    (∑ labels : Fin m → L, actualFiberCount program points labels) =
      encodingCount (A := A) (L := L) := by
  classical
  let e : (Σ labels : Fin m → L,
      {enc : A ≃ L // ∀ i, labels i =
        enc (runGroup program enc points i)}) ≃ (A ≃ L) := {
    toFun := fun pair => pair.2.1
    invFun := fun enc =>
      ⟨fun i => enc (runGroup program enc points i), ⟨enc, by intro i; rfl⟩⟩
    left_inv := by
      intro pair
      rcases pair with ⟨labels, ⟨enc, h⟩⟩
      have heq : labels = fun i => enc (runGroup program enc points i) :=
        funext h
      subst labels
      rfl
    right_inv := by intro enc; rfl
  }
  unfold encodingCount
  calc
    (∑ labels : Fin m → L, actualFiberCount program points labels) =
        Fintype.card (Σ labels : Fin m → L,
          {enc : A ≃ L // ∀ i, labels i =
            enc (runGroup program enc points i)}) := by
          simp [actualFiberCount, Fintype.card_sigma]
    _ = Fintype.card (A ≃ L) := Fintype.card_congr e


/-- For the public input `G,Q=wG`, a complete adaptive transcript is
exactly the label assignment to its reconstructed affine forms. -/
theorem dlp_labels_iff_symbolic_fiber {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (w : F) (labels : Fin m → L) :
    (∀ i, labels i = enc (runGroup program enc (seedPoints G w) i)) ↔
    (∀ i, labels i = enc ((eval
      (formsFromTranscript program labels (seedForms (F := F)) i) w) • G)) := by
  exact labels_iff_symbolic_fiber program enc G w seedForms
    (seedPoints G w) labels (seed_invariant G w)

#print axioms dlp_labels_iff_symbolic_fiber
#print axioms actualFiberCount
#print axioms symbolicFiberCount
#print axioms encodingCount
#print axioms actual_fiber_count_eq_symbolic
#print axioms actual_fiber_partition
#print axioms formsFromTranscript_prefix
#print axioms labels_of_symbolic_fiber
#print axioms labels_iff_symbolic_fiber

end XedniTranscriptFiberEquivalence
