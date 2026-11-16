import XedniObstruction
import Mathlib.Data.Fintype.Pi
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Data.Int.Interval

namespace XedniObstruction

variable {r q : ℕ}

noncomputable def dependentLiftSamples {H : Type*} [AddCommGroup H] [Fact q.Prime]
    (lifts : (Fin r → ZMod q) → Fin r → H) :
    Finset (Fin r → ZMod q) := by
  classical
  exact Finset.univ.filter (fun t =>
    ∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff)

/-- The complete finite box of nontrivial integer coefficient vectors. -/
noncomputable def boundedCandidates (bound : ℕ) : Finset (Fin r → ℤ) := by
  classical
  exact (Fintype.piFinset (fun _ : Fin r =>
    Finset.Icc (-(bound : ℤ)) (bound : ℤ))).filter Nontrivial

theorem mem_boundedCandidates (bound : ℕ) (coeff : Fin r → ℤ) :
    coeff ∈ boundedCandidates bound ↔
      Nontrivial coeff ∧ Bounded bound coeff := by
  classical
  constructor
  · intro h
    have hmem := Finset.mem_filter.mp h
    refine ⟨hmem.2, fun i => ?_⟩
    have hi := (Fintype.mem_piFinset.mp hmem.1) i
    simp only [Finset.mem_Icc] at hi
    omega
  · rintro ⟨hnon, hsmall⟩
    apply Finset.mem_filter.mpr
    refine ⟨Fintype.mem_piFinset.mpr ?_, hnon⟩
    intro i
    simp only [Finset.mem_Icc]
    have hi := hsmall i
    omega

theorem nontrivial_iff_ne_zero (coeff : Fin r → ℤ) :
    Nontrivial coeff ↔ coeff ≠ 0 := by
  constructor
  · rintro ⟨i, hi⟩ hzero
    exact hi (congrFun hzero i)
  · intro hnon
    by_contra hall
    apply hnon
    funext i
    by_contra hi
    exact hall ⟨i, hi⟩

/-- The complete nonzero integer coefficient box has its expected size. -/
theorem boundedCandidates_card (bound : ℕ) :
    (boundedCandidates (r := r) bound).card =
      (2 * bound + 1) ^ r - 1 := by
  classical
  let interval : Finset ℤ := Finset.Icc (-(bound : ℤ)) (bound : ℤ)
  let box : Finset (Fin r → ℤ) := Fintype.piFinset (fun _ => interval)
  have hzero : (0 : Fin r → ℤ) ∈ box := by
    simp [box, interval, Fintype.mem_piFinset]
  have hset : boundedCandidates (r := r) bound = box.erase 0 := by
    ext coeff
    simp [boundedCandidates, box, interval, nontrivial_iff_ne_zero,
      Finset.mem_erase]
    tauto
  have hinterval : interval.card = 2 * bound + 1 := by
    simp [interval, Int.card_Icc]
    omega
  rw [hset, Finset.card_erase_of_mem hzero]
  change (Fintype.piFinset (fun _ : Fin r => interval)).card - 1 = _
  rw [Fintype.card_piFinset_const, hinterval]

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

/-- The dependent-lift bound with its finite candidate box constructed
explicitly from the short-witness radius. -/
theorem dependent_lift_box_count {H : Type*} [AddCommGroup H]
    [Fact q.Prime] (red : H →+ ZMod q)
    (s : Fin r → ZMod q) (w : ZMod q)
    (lifts : (Fin r → ZMod q) → Fin r → H)
    (hcompat : ∀ t i, red (lifts t i) = xedniSampleMap s w t i)
    (bound : ℕ) (hbound : bound < q)
    (short_relation_witness : ∀ t,
      (∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff) →
      ∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff ∧
        Bounded bound coeff) :
    (dependentLiftSamples lifts).card * Nat.card (ZMod q) ≤
      (boundedCandidates (r := r) bound).card *
        Nat.card (Fin r → ZMod q) := by
  apply dependent_lift_sample_count red s w lifts hcompat bound hbound
    short_relation_witness (boundedCandidates bound)
  · intro coeff hnon hsmall
    exact (mem_boundedCandidates bound coeff).2 ⟨hnon, hsmall⟩
  · intro coeff hc
    exact (mem_boundedCandidates bound coeff).1 hc

/-- A closed-form upper bound for the dependent-lift sample count. -/
theorem dependent_lift_explicit_count {H : Type*} [AddCommGroup H]
    [Fact q.Prime] (red : H →+ ZMod q)
    (s : Fin r → ZMod q) (w : ZMod q)
    (lifts : (Fin r → ZMod q) → Fin r → H)
    (hcompat : ∀ t i, red (lifts t i) = xedniSampleMap s w t i)
    (bound : ℕ) (hbound : bound < q)
    (short_relation_witness : ∀ t,
      (∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff) →
      ∃ coeff, Nontrivial coeff ∧ Relation (lifts t) coeff ∧
        Bounded bound coeff) :
    (dependentLiftSamples lifts).card * Nat.card (ZMod q) ≤
      ((2 * bound + 1) ^ r - 1) * Nat.card (Fin r → ZMod q) := by
  simpa [boundedCandidates_card] using
    dependent_lift_box_count red s w lifts hcompat bound hbound
      short_relation_witness

#print axioms dependent_lift_sample_count
#print axioms mem_boundedCandidates
#print axioms nontrivial_iff_ne_zero
#print axioms boundedCandidates_card
#print axioms dependent_lift_box_count
#print axioms dependent_lift_explicit_count

end XedniObstruction
