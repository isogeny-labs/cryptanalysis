import Mathlib.LinearAlgebra.FiniteDimensional.Basic
import Mathlib.GroupTheory.Index
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.ZMod.Basic
import Mathlib.Algebra.Field.ZMod
import Mathlib.Data.Finset.Preimage

/-!
Corrected reduction-map implication. Dependence must supply some bounded
witness; arbitrary scalar multiples of a relation need not be bounded.
The height-theoretic existence of such a witness is a separate obligation.
-/

namespace XedniBoundedWitness

variable {r : ℕ} {H G : Type*} [AddCommGroup H] [AddCommGroup G]

def Relation (points : Fin r → H) (coeff : Fin r → ℤ) : Prop :=
  ∑ i, coeff i • points i = 0

def Nontrivial (coeff : Fin r → ℤ) : Prop :=
  ∃ i, coeff i ≠ 0

def Bounded (bound : ℕ) (coeff : Fin r → ℤ) : Prop :=
  ∀ i, (coeff i).natAbs ≤ bound

theorem relation_reduces (red : H →+ G) (lifts : Fin r → H)
    (coeff : Fin r → ℤ) (h : Relation lifts coeff) :
    Relation (fun i => red (lifts i)) coeff := by
  unfold Relation at *
  calc
    (∑ i, coeff i • red (lifts i)) = red (∑ i, coeff i • lifts i) := by
      simp
    _ = 0 := by rw [h]; simp

/-- A dependent lifted tuple supplies a bounded witness, which reduces to a
forbidden bounded relation downstairs. The witness may differ from the
original relation and need not bound its arbitrary multiples. -/
theorem no_dependent_lift (red : H →+ G) (lifts : Fin r → H)
    (bound : ℕ)
    (bounded_witness :
      (∃ coeff, Nontrivial coeff ∧ Relation lifts coeff) →
      ∃ witness, Nontrivial witness ∧ Relation lifts witness ∧ Bounded bound witness)
    (no_small_reduced_relation : ∀ coeff, Nontrivial coeff →
      Bounded bound coeff → ¬ Relation (fun i => red (lifts i)) coeff) :
    ∀ coeff, Nontrivial coeff → ¬ Relation lifts coeff := by
  intro coeff hnon hrel
  obtain ⟨witness, hw_non, hw_rel, hw_bound⟩ := bounded_witness ⟨coeff, hnon, hrel⟩
  exact no_small_reduced_relation witness hw_non hw_bound
    (relation_reduces red lifts witness hw_rel)

/-- For each compatible lift, dependence must supply a witness with the
same bound. The chosen witness can vary with the lift. -/
theorem all_compatible_lifts_blocked (red : H →+ G)
    (reduced : Fin r → G) (bound : ℕ)
    (bounded_witness : ∀ lifts : Fin r → H,
      (∀ i, red (lifts i) = reduced i) →
      (∃ coeff, Nontrivial coeff ∧ Relation lifts coeff) →
      ∃ witness, Nontrivial witness ∧ Relation lifts witness ∧ Bounded bound witness)
    (no_small_reduced_relation : ∀ coeff, Nontrivial coeff →
      Bounded bound coeff → ¬ Relation reduced coeff) :
    ∀ lifts : Fin r → H,
      (∀ i, red (lifts i) = reduced i) →
      ∀ coeff, Nontrivial coeff → ¬ Relation lifts coeff := by
  intro lifts hcompat coeff hnon hrel
  obtain ⟨witness, hw_non, hw_rel, hw_bound⟩ :=
    bounded_witness lifts hcompat ⟨coeff, hnon, hrel⟩
  have hred : Relation reduced witness := by
    simpa only [Relation, hcompat] using relation_reduces red lifts witness hw_rel
  exact no_small_reduced_relation witness hw_non hw_bound hred

/-- A dependent zero tuple has a nontrivial witness bounded by one. -/
theorem zero_tuple_has_bounded_witness :
    ∃ coeff : Fin 1 → ℤ,
      Nontrivial coeff ∧ Relation (fun _ => (0 : ℤ)) coeff ∧ Bounded 1 coeff := by
  refine ⟨fun _ => 1, ?_, ?_, ?_⟩
  · exact ⟨0, by decide⟩
  · simp [Relation]
  · intro i
    change (1 : ℤ).natAbs ≤ 1
    decide

/-- That same tuple has relations outside every proposed universal bound. -/
theorem zero_tuple_has_unbounded_relations (bound : ℕ) :
    ∃ coeff : Fin 1 → ℤ,
      Nontrivial coeff ∧ Relation (fun _ => (0 : ℤ)) coeff ∧ ¬ Bounded bound coeff := by
  refine ⟨fun _ => ((bound + 1 : ℕ) : ℤ), ?_, ?_, ?_⟩
  · refine ⟨0, ?_⟩
    change ((bound + 1 : ℕ) : ℤ) ≠ 0
    exact Int.ofNat_ne_zero.mpr (Nat.succ_ne_zero bound)
  · simp [Relation]
  · intro h
    have bad := h (0 : Fin 1)
    change bound + 1 ≤ bound at bad
    exact Nat.not_succ_le_self bound bad

end XedniBoundedWitness

#print axioms XedniBoundedWitness.relation_reduces
#print axioms XedniBoundedWitness.no_dependent_lift
#print axioms XedniBoundedWitness.all_compatible_lifts_blocked
#print axioms XedniBoundedWitness.zero_tuple_has_bounded_witness
#print axioms XedniBoundedWitness.zero_tuple_has_unbounded_relations
