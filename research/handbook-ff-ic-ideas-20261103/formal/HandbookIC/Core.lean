/-!
# HandbookIC.Core — shared vocabulary for the handbook-derived IC ideas

Core-Lean only (no Mathlib): the abstract objects of an elliptic-curve
index calculus are modelled on the *exponent side*. A DLP instance is a
type `G` with a bijection onto `Fin n` (the discrete logarithm), a factor
base is a finite list of elements, a relation is an integer combination
of base elements equal to `a·g + b·q`, and cost models are natural-number
functions. The elliptic-curve group law itself is **not** modelled here;
every idea module says which hypotheses stand in for curve-specific facts.
-/

namespace HandbookIC

/-- A cyclic group of order `n` given through its discrete logarithm.
`exp` and `log` are mutually inverse, so `G` is a copy of `Fin n`. -/
structure CyclicGroup (G : Type) (n : Nat) where
  log : G → Fin n
  exp : Fin n → G
  log_exp : ∀ k, log (exp k) = k
  exp_log : ∀ g, exp (log g) = g

/-- A DLP instance: generator `g`, target `q`, secret `x` with `log q = x·log g`. -/
structure DLPInstance (G : Type) (n : Nat) extends CyclicGroup G n where
  g : G
  q : G
  x : Fin n
  log_g_one : log g = ⟨1 % n, Nat.mod_lt _ (by
    cases n with
    | zero => exact absurd (log g).isLt (Nat.not_lt_zero _)
    | succ m => exact Nat.succ_pos m)⟩
  log_q : (log q).val = (x.val * (log g).val) % n

/-- A factor base is a finite indexed family of group elements. -/
abbrev FactorBase (G : Type) (B : Nat) := Fin B → G

/-- A relation `a·g + b·q = Σ c_j · P_j`, recorded on the exponent side. -/
structure Relation (B : Nat) where
  a : Int
  b : Int
  c : Fin B → Int

/-- Sum of a finite integer-valued family. -/
def finSum : (B : Nat) → (Fin B → Int) → Int
  | 0, _ => 0
  | B + 1, f => finSum B (fun i => f i.castSucc) + f (Fin.last B)

/-- The exponent-side content of a relation: `a + b·x ≡ Σ c_j log P_j (mod n)`. -/
def Relation.holds {G : Type} {n B : Nat} (I : DLPInstance G n)
    (F : FactorBase G B) (r : Relation B) : Prop :=
  (r.a + r.b * (I.x.val : Int)) % (n : Int)
    = finSum B (fun j => r.c j * ((I.log (F j)).val : Int)) % (n : Int)

/-- A relation with `b` invertible mod `n` and every `log P_j` known determines `x`.
Stated as the exponent-side identity; invertibility is a hypothesis. -/
def Relation.solvesTarget {G : Type} {n B : Nat} (I : DLPInstance G n)
    (F : FactorBase G B) (r : Relation B) (bInv : Int) : Prop :=
  r.holds I F →
    (r.b * bInv) % (n : Int) = 1 % (n : Int) →
    ((I.x.val : Int)) % (n : Int)
      = ((finSum B (fun j => r.c j * ((I.log (F j)).val : Int)) - r.a) * bInv) % (n : Int)

/-- Phase costs of an index calculus, in one counted unit (group operations). -/
structure Cost where
  factorBase : Nat
  relations  : Nat
  linearAlgebra : Nat
  descent : Nat

/-- Total cold cost: every phase counts. -/
def Cost.total (c : Cost) : Nat :=
  c.factorBase + c.relations + c.linearAlgebra + c.descent

/-- A phase-level improvement that leaves every other phase unchanged. -/
def Cost.improvesRelations (c c' : Cost) : Prop :=
  c'.factorBase = c.factorBase ∧ c'.linearAlgebra = c.linearAlgebra ∧
  c'.descent = c.descent ∧ c'.relations < c.relations

theorem Cost.total_lt_of_improvesRelations (c c' : Cost)
    (h : c.improvesRelations c') : c'.total < c.total := by
  unfold Cost.total
  obtain ⟨h1, h2, h3, h4⟩ := h
  omega

/-- Relabelling: the headline phase fell but the total did not. Not an improvement. -/
def Cost.relabels (c c' : Cost) : Prop :=
  c'.relations < c.relations ∧ c.total ≤ c'.total

theorem Cost.not_improvement_of_relabels (c c' : Cost) (h : c.relabels c') :
    ¬ c'.total < c.total := by
  obtain ⟨_, h2⟩ := h
  omega

/-- Number of smooth elements in a list, for a decidable smoothness test. -/
def smoothCount {α : Type} (xs : List α) (smooth : α → Bool) : Nat :=
  (xs.filter smooth).length

theorem smoothCount_le_length {α : Type} (xs : List α) (smooth : α → Bool) :
    smoothCount xs smooth ≤ xs.length := by
  unfold smoothCount
  exact List.length_filter_le _ _

/-- Expected relation-collection cost: trials needed divided by the smooth
fraction, in integer arithmetic (`need` relations, `p` smooth out of `t` trials). -/
def expectedTrials (need p t : Nat) : Nat := need * t / p

/-- Quotienting a base of size `N` by a free action of a group of order `k`
gives `N / k` orbit representatives. -/
def orbitRepresentatives (N k : Nat) : Nat := N / k

theorem orbitRepresentatives_le (N k : Nat) : orbitRepresentatives N k ≤ N := by
  unfold orbitRepresentatives
  exact Nat.div_le_self N k

theorem orbitRepresentatives_mul_le (N k : Nat) :
    orbitRepresentatives N k * k ≤ N := by
  unfold orbitRepresentatives
  exact Nat.div_mul_le_self N k

/-- A generic lower-bound reference (for example a matched Pollard rho count).
`beats` is strict and on the total. -/
def Cost.beats (c : Cost) (reference : Nat) : Prop := c.total < reference

end HandbookIC

#print axioms HandbookIC.Cost.total_lt_of_improvesRelations
#print axioms HandbookIC.Cost.not_improvement_of_relabels
#print axioms HandbookIC.smoothCount_le_length
#print axioms HandbookIC.orbitRepresentatives_le
#print axioms HandbookIC.orbitRepresentatives_mul_le
