import TranscriptFiberEquivalence

namespace XedniTypedPrefixProgram

open XedniAdaptiveProgramInvariant XedniTranscriptDeterminism
open XedniTranscriptFiberEquivalence XedniSymbolicCollision

/-- Truncate a typed adaptive program after reaching trace length `k`.
The proof arguments certify that the requested stage occurs in the program. -/
def takeAt {L : Type*} {n m : ℕ} (program : Program L n m)
    (k : ℕ) (hn : n ≤ k) (hk : k ≤ m) : Program L n k :=
  match program with
  | .done => by
      have h : k = n := by omega
      subst k
      exact .done
  | .step choose tail => by
      by_cases h : k = n
      · subst k
        exact .done
      · have hnext : n + 1 ≤ k := by omega
        exact .step choose (takeAt tail k hnext hk)


/-- Running the truncated adaptive program gives exactly the corresponding
prefix of the complete group execution, for every encoding and input. -/
theorem runGroup_takeAt {A L : Type*} [AddGroup A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (points : Fin n → A) (k : ℕ) (hn : n ≤ k) (hk : k ≤ m)
    (i : Fin k) :
    runGroup (takeAt program k hn hk) enc points i =
      runGroup program enc points (Fin.castLE hk i) := by
  induction program generalizing k with
  | @done n0 =>
      have h : k = n0 := by omega
      subst k
      simp [takeAt, runGroup]
  | @step n0 m0 choose tail ih =>
      by_cases h : k = n0
      · subst k
        simpa [takeAt, runGroup] using
          (runGroup_prefix (.step choose tail) enc points i).symm
      · have hnext : n0 + 1 ≤ k := by omega
        let cmd := choose (fun j => enc (points j))
        let nextPoints := Fin.snoc (α := fun _ => A) points
          (pointOp cmd.op (points cmd.lhs) (points cmd.rhs))
        have hi := ih nextPoints k hnext hk i
        simpa [takeAt, h, runGroup, cmd, nextPoints] using hi


def restrictLabels {L : Type*} {k m : ℕ}
    (hk : k ≤ m) (labels : Fin m → L) : Fin k → L :=
  fun i => labels (Fin.castLE hk i)

/-- Reconstructing forms from the truncated program and truncated labels
gives the same form prefix as reconstructing the complete transcript. -/
theorem formsFromTranscript_takeAt {F L : Type*} [Field F]
    {n m : ℕ} (program : Program L n m)
    (labels : Fin m → L) (forms : Fin n → Affine F)
    (k : ℕ) (hn : n ≤ k) (hk : k ≤ m) (i : Fin k) :
    formsFromTranscript (takeAt program k hn hk)
      (restrictLabels hk labels) forms i =
    formsFromTranscript program labels forms (Fin.castLE hk i) := by
  induction program generalizing k with
  | @done n0 =>
      have h : k = n0 := by omega
      subst k
      simp [takeAt, formsFromTranscript]
  | @step n0 m0 choose tail ih =>
      by_cases h : k = n0
      · subst k
        simpa [takeAt, formsFromTranscript, restrictLabels] using
          (formsFromTranscript_prefix (.step choose tail) labels forms i).symm
      · have hnext : n0 + 1 ≤ k := by omega
        let cmd := choose (prefixLabels (.step choose tail) labels)
        have hcmd : choose (prefixLabels
            (.step choose (takeAt tail k hnext hk))
            (restrictLabels hk labels)) = cmd := by
          dsimp [cmd, prefixLabels, restrictLabels]
          apply congrArg choose
          funext j
          apply congrArg labels
          exact Fin.ext rfl
        have hi := ih labels
          (Fin.snoc forms
            (formOp cmd.op (forms cmd.lhs) (forms cmd.rhs)))
          k hnext hk i
        simpa [formsFromTranscript, takeAt, h, hcmd, cmd] using hi


/-- Any proposed complete label tuple has an exact actual-versus-symbolic
fiber condition at every typed prefix of a public DLP program. The
condition uses only the first `k` labels and first `k` reconstructed forms. -/
theorem dlp_prefix_labels_iff_symbolic {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (w : F) (labels : Fin m → L)
    (k : ℕ) (h2 : 2 ≤ k) (hk : k ≤ m) :
    (∀ i : Fin k, restrictLabels hk labels i =
      enc (runGroup program enc (seedPoints G w) (Fin.castLE hk i))) ↔
    (∀ i : Fin k, restrictLabels hk labels i = enc
      ((eval (formsFromTranscript program labels (seedForms (F := F))
        (Fin.castLE hk i)) w) • G)) := by
  have h := dlp_labels_iff_symbolic_fiber
    (takeAt program k h2 hk) enc G w (restrictLabels hk labels)
  simpa only [runGroup_takeAt, formsFromTranscript_takeAt] using h


/-- Changing unseen suffix labels cannot change any reconstructed affine
form already present at stage `k`. -/
theorem form_prefix_depends_only_on_visible_labels {F L : Type*}
    [Field F] {n m : ℕ} (program : Program L n m)
    (forms : Fin n → Affine F) (k : ℕ)
    (hn : n ≤ k) (hk : k ≤ m)
    (labels₁ labels₂ : Fin m → L)
    (hagree : ∀ i : Fin k,
      restrictLabels hk labels₁ i = restrictLabels hk labels₂ i)
    (i : Fin k) :
    formsFromTranscript program labels₁ forms (Fin.castLE hk i) =
      formsFromTranscript program labels₂ forms (Fin.castLE hk i) := by
  have hres : restrictLabels hk labels₁ = restrictLabels hk labels₂ :=
    funext hagree
  calc
    formsFromTranscript program labels₁ forms (Fin.castLE hk i) =
        formsFromTranscript (takeAt program k hn hk)
          (restrictLabels hk labels₁) forms i :=
      (formsFromTranscript_takeAt program labels₁ forms k hn hk i).symm
    _ = formsFromTranscript (takeAt program k hn hk)
          (restrictLabels hk labels₂) forms i := by rw [hres]
    _ = formsFromTranscript program labels₂ forms (Fin.castLE hk i) :=
      formsFromTranscript_takeAt program labels₂ forms k hn hk i


noncomputable def prefixSymbolicFiberCount {F A L : Type*}
    [Field F] [Fintype A] [Fintype L]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A) (w : F)
    (labels : Fin m → L) (k : ℕ) (_h2 : 2 ≤ k) (hk : k ≤ m) : ℕ := by
  classical
  exact Fintype.card {enc : A ≃ L // ∀ i : Fin k,
    restrictLabels hk labels i = enc
      ((eval (formsFromTranscript program labels (seedForms (F := F))
        (Fin.castLE hk i)) w) • G)}

/-- The number of encodings producing any proposed visible prefix equals
the symbolic fiber count reconstructed from that same prefix. -/
theorem actual_prefix_fiber_count_eq_symbolic {F A L : Type*}
    [Field F] [Fintype A] [Fintype L]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (G : A) (w : F)
    (labels : Fin m → L) (k : ℕ) (h2 : 2 ≤ k) (hk : k ≤ m) :
    actualFiberCount (takeAt program k h2 hk) (seedPoints G w)
      (restrictLabels hk labels) =
    prefixSymbolicFiberCount program G w labels k h2 hk := by
  classical
  let e : {enc : A ≃ L // ∀ i : Fin k,
      restrictLabels hk labels i =
        enc (runGroup (takeAt program k h2 hk) enc (seedPoints G w) i)} ≃
      {enc : A ≃ L // ∀ i : Fin k,
        restrictLabels hk labels i = enc
          ((eval (formsFromTranscript program labels (seedForms (F := F))
            (Fin.castLE hk i)) w) • G)} := {
    toFun := fun ⟨enc, h⟩ =>
      ⟨enc, (dlp_prefix_labels_iff_symbolic program enc G w labels
        k h2 hk).mp (by simpa only [runGroup_takeAt] using h)⟩
    invFun := fun ⟨enc, h⟩ =>
      ⟨enc, by
        have ha := (dlp_prefix_labels_iff_symbolic program enc G w labels
          k h2 hk).mpr h
        simpa only [runGroup_takeAt] using ha⟩
    left_inv := by intro x; apply Subtype.ext; rfl
    right_inv := by intro x; apply Subtype.ext; rfl
  }
  exact Fintype.card_congr e

#print axioms actual_prefix_fiber_count_eq_symbolic
#print axioms prefixSymbolicFiberCount
#print axioms form_prefix_depends_only_on_visible_labels
#print axioms dlp_prefix_labels_iff_symbolic
#print axioms formsFromTranscript_takeAt
#print axioms restrictLabels
#print axioms runGroup_takeAt
#print axioms takeAt

end XedniTypedPrefixProgram
