import GroupTraceInvariant

namespace XedniAdaptiveProgramInvariant

open XedniSymbolicCollision

inductive Op where
  | add
  | sub
deriving DecidableEq

structure Command (n : ℕ) where
  op : Op
  lhs : Fin n
  rhs : Fin n

/-- A finite program whose next operation and operands can depend on every
label currently visible. The transcript length is indexed in the type. -/
inductive Program (L : Type*) : ℕ → ℕ → Type _ where
  | done {n : ℕ} : Program L n n
  | step {n m : ℕ} (choose : (Fin n → L) → Command n)
      (tail : Program L (n + 1) m) : Program L n m

def formOp {F : Type*} [Ring F] : Op → Affine F → Affine F → Affine F
  | .add, f, g => plus f g
  | .sub, f, g => plus f (scale (-1) g)

def pointOp {A : Type*} [AddGroup A] : Op → A → A → A
  | .add, x, y => x + y
  | .sub, x, y => x - y

/-- Affine evaluation commutes with each group command. -/
theorem op_commutes {F A : Type*} [Field F]
    [AddCommGroup A] [Module F A] (G : A)
    (op : Op) (f g : Affine F) (w : F) :
    pointOp op ((eval f w) • G) ((eval g w) • G) =
      (eval (formOp op f g) w) • G := by
  cases op with
  | add => simp [pointOp, formOp, eval_plus, add_smul]
  | sub => simp [pointOp, formOp, eval_plus, eval_scale,
      sub_eq_add_neg, add_smul, neg_smul]

/-- Execute operations on actual group elements, selecting every command
from the current encoded group-point labels. -/
def runGroup {A L : Type*} [AddGroup A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (points : Fin n → A) : Fin m → A :=
  match program with
  | .done => points
  | .step choose tail =>
      let cmd := choose (fun i => enc (points i))
      runGroup tail enc
        (Fin.snoc points (pointOp cmd.op (points cmd.lhs) (points cmd.rhs)))

/-- Execute the same program symbolically. At each node the chooser sees
the labels of evaluated forms, not the hidden scalar or coefficients. -/
def runForms {F A L : Type*} [Field F] [AddCommGroup A]
    [Module F A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (G : A) (w : F) (forms : Fin n → Affine F) :
    Fin m → Affine F :=
  match program with
  | .done => forms
  | .step choose tail =>
      let cmd := choose (fun i => enc ((eval (forms i) w) • G))
      runForms tail enc G w
        (Fin.snoc forms (formOp cmd.op (forms cmd.lhs) (forms cmd.rhs)))

/-- Every point in an arbitrary finite adaptive add/sub transcript equals
the evaluation of its corresponding affine form. -/
theorem run_invariant {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {n m : ℕ}
    (program : Program L n m) (enc : A ≃ L)
    (G : A) (w : F) (forms : Fin n → Affine F)
    (points : Fin n → A)
    (hinit : ∀ i, points i = (eval (forms i) w) • G) :
    ∀ i, runGroup program enc points i =
      (eval (runForms program enc G w forms i) w) • G := by
  induction program with
  | done => simpa [runGroup, runForms] using hinit
  | step choose tail ih =>
      have hcmd :
          choose (fun i => enc (points i)) =
            choose (fun i => enc ((eval (forms i) w) • G)) := by
        congr 1
        funext i
        rw [hinit i]
      simp only [runGroup, runForms, hcmd]
      apply ih
      intro i
      refine Fin.lastCases ?_ ?_ i
      · simp [Fin.snoc_last, op_commutes, hinit]
      · intro j
        simp [Fin.snoc_castSucc, hinit]

/-- The public DLP inputs `G` and `Q = w • G` have constant and identity
affine forms respectively. -/
def seedForms {F : Type*} [Field F] : Fin 2 → Affine F :=
  fun i => if i = 0 then ⟨0, 1⟩ else ⟨1, 0⟩

def seedPoints {F A : Type*} [Field F]
    [AddCommGroup A] [Module F A] (G : A) (w : F) : Fin 2 → A :=
  fun i => if i = 0 then G else w • G

theorem seed_invariant {F A : Type*} [Field F]
    [AddCommGroup A] [Module F A] (G : A) (w : F) :
    ∀ i, seedPoints G w i = (eval (seedForms i) w) • G := by
  intro i
  fin_cases i <;> simp [seedPoints, seedForms, eval]

/-- The full group transcript of any finite label-adaptive add/sub program
on public DLP inputs is represented by affine forms in the hidden scalar. -/
theorem dlp_program_invariant {F A L : Type*} [Field F]
    [AddCommGroup A] [Module F A] {m : ℕ}
    (program : Program L 2 m) (enc : A ≃ L)
    (G : A) (w : F) :
    ∀ i, runGroup program enc (seedPoints G w) i =
      (eval (runForms program enc G w seedForms i) w) • G := by
  exact run_invariant program enc G w seedForms (seedPoints G w)
    (seed_invariant G w)

#print axioms Op
#print axioms Program
#print axioms formOp
#print axioms pointOp
#print axioms op_commutes
#print axioms runGroup
#print axioms runForms
#print axioms run_invariant
#print axioms seedForms
#print axioms seedPoints
#print axioms seed_invariant
#print axioms dlp_program_invariant

end XedniAdaptiveProgramInvariant
