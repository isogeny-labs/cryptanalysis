import XedniObstruction

namespace XedniObstruction

variable {r q : ℕ}

noncomputable def dependentLiftSamples {H : Type*} [AddCommGroup H] [Fact q.Prime]
    (lifts : (Fin r → ZMod q) → Fin r → H) :
    Finset (Fin r → ZMod q) := by
  classical
  exact Finset.univ.filter (fun t =>
    ∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff)

/-- A uniform short-relation witness bound over the sampled lifts transports
the fixed-candidate reduced relation bound to the dependent-lift event. -/
theorem dependent_lift_sample_count {H : Type*} [AddCommGroup H]
    [Fact q.Prime] (red : H →+ ZMod q)
    (s : Fin r → ZMod q) (w : ZMod q)
    (lifts : (Fin r → ZMod q) → Fin r → H)
    (hcompat : ∀ t i, red (lifts t i) = xedniSampleMap s w t i)
    (bound : ℕ) (hbound : bound < q)
    (short_relation_witness : ∀ t,
      (∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff) →
      ∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff ∧
        Bounded bound coeff)
    (candidates : Finset (Fin r → ℤ))
    (hcover : ∀ coeff, Nontrivial coeff → Bounded bound coeff →
      coeff ∈ candidates)
    (hvalid : ∀ coeff ∈ candidates,
      Nontrivial coeff ∧ Bounded bound coeff) :
    (dependentLiftSamples lifts).card *
        Nat.card (ZMod q) ≤
      candidates.card * Nat.card (Fin r → ZMod q) := by
  classical
  let event := (reducedCandidates (q := q) candidates).biUnion
    (zeroFiber (F := ZMod q))
  have hsubset :
      dependentLiftSamples lifts ⊆
      event.preimage (xedniSampleMap s w)
        (xedniSampleMap_bijective s w).1.injOn := by
    intro t ht
    have ht' : t ∈ Finset.univ.filter (fun t : Fin r → ZMod q =>
        ∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff) := by
      simpa [dependentLiftSamples] using ht
    obtain ⟨coeff, hnon, hrel, hsmall⟩ :=
      short_relation_witness t (Finset.mem_filter.mp ht').2
    have hmem : (fun i => (coeff i : ZMod q)) ∈
        reducedCandidates (q := q) candidates :=
      Finset.mem_image.mpr ⟨coeff, hcover coeff hnon hsmall, rfl⟩
    have hred := relation_reduces red (lifts t) coeff hrel
    have hdot : dotHom (fun i => (coeff i : ZMod q))
        (xedniSampleMap s w t) = 0 := by
      simpa [Relation, dotHom, hcompat, zsmul_eq_mul] using hred
    apply Finset.mem_preimage.mpr
    apply Finset.mem_biUnion.mpr
    refine ⟨fun i => (coeff i : ZMod q), hmem, ?_⟩
    simpa [zeroFiber] using hdot
  have hcard := Finset.card_le_card hsubset
  have hcount := sampled_integer_candidate_union_count bound hbound
    candidates hvalid s w
  exact (Nat.mul_le_mul_right _ hcard).trans hcount

#print axioms dependent_lift_sample_count

end XedniObstruction
