import XedniObstruction

/-!
A bounded-density extension of the finite xedni sample count. A selection
rule can change the sampling law. We charge its largest point mass rather
than silently treating the selected inputs as uniform.
-/

namespace XedniSelectionLaw

open XedniObstruction

variable {r q : ℕ}

/-- Weighted mass of the selected dependent-lift event, before normalization.
The weight function is an arbitrary nonnegative integer measure. -/
theorem selected_dependent_lift_weight_bound {H : Type*} [AddCommGroup H]
    [Fact q.Prime] (red : H →+ ZMod q)
    (s : Fin r → ZMod q) (w : ZMod q)
    (admissible : Finset (Fin r → ZMod q))
    (lifts : (Fin r → ZMod q) → Fin r → H)
    (hcompat : ∀ t ∈ admissible, ∀ i,
      red (lifts t i) = xedniSampleMap s w t i)
    (bound : ℕ) (hbound : bound < q)
    (bounded_witness : ∀ t ∈ admissible,
      (∃ coeff, XedniObstruction.Nontrivial coeff ∧ Relation (lifts t) coeff) →
      ∃ small, XedniObstruction.Nontrivial small ∧ Bounded bound small ∧ Relation (lifts t) small)
    (candidates : Finset (Fin r → ℤ))
    (hcover : ∀ coeff, XedniObstruction.Nontrivial coeff → Bounded bound coeff →
      coeff ∈ candidates)
    (hvalid : ∀ coeff ∈ candidates,
      XedniObstruction.Nontrivial coeff ∧ Bounded bound coeff)
    (weight : (Fin r → ZMod q) → ℕ) (maxWeight : ℕ)
    (hweight : ∀ t ∈ admissible, weight t ≤ maxWeight) :
    (∑ t ∈ selectedDependentLiftSamples admissible lifts, weight t) *
        Nat.card (ZMod q) ≤
      maxWeight * candidates.card * Nat.card (Fin r → ZMod q) := by
  classical
  let event := selectedDependentLiftSamples admissible lifts
  have hsum : (∑ t ∈ event, weight t) ≤ event.card * maxWeight := by
    calc
      (∑ t ∈ event, weight t) ≤ ∑ _t ∈ event, maxWeight := by
        apply Finset.sum_le_sum
        intro t ht
        exact hweight t (Finset.mem_filter.mp ht).1
      _ = event.card * maxWeight := by simp
  have hcard := selected_dependent_lift_sample_count red s w admissible lifts
    hcompat bound hbound bounded_witness candidates hcover hvalid
  have hleft := Nat.mul_le_mul_right (Nat.card (ZMod q)) hsum
  have hright := Nat.mul_le_mul_left maxWeight hcard
  calc
    (∑ t ∈ event, weight t) * Nat.card (ZMod q) ≤
      (event.card * maxWeight) * Nat.card (ZMod q) := hleft
    _ = maxWeight * (event.card * Nat.card (ZMod q)) := by ac_rfl
    _ ≤ maxWeight * (candidates.card * Nat.card (Fin r → ZMod q)) := hright
    _ = maxWeight * candidates.card * Nat.card (Fin r → ZMod q) := by ac_rfl

end XedniSelectionLaw

#print axioms XedniSelectionLaw.selected_dependent_lift_weight_bound
