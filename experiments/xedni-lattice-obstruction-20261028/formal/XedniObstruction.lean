import Mathlib.LinearAlgebra.FiniteDimensional.Basic
import Mathlib.GroupTheory.Index
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.ZMod.Basic
import Mathlib.Algebra.Field.ZMod
import Mathlib.Data.Finset.Preimage

/-!
The deterministic reduction-map obstruction behind the bounded-coefficient
analysis of the original xedni calculus.  No statement here assumes that the
height bound holds for every elliptic curve, or that a reduction tuple is
random: those are separate mathematical hypotheses.
-/

namespace XedniObstruction

variable {r : ℕ} {H G : Type*} [AddCommGroup H] [AddCommGroup G]

def Relation (points : Fin r → H) (coeff : Fin r → ℤ) : Prop :=
  ∑ i, coeff i • points i = 0

def Nontrivial (coeff : Fin r → ℤ) : Prop :=
  ∃ i, coeff i ≠ 0

def Bounded (bound : ℕ) (coeff : Fin r → ℤ) : Prop :=
  ∀ i, (coeff i).natAbs ≤ bound

/-- A rational relation reduces to a relation with the same coefficients. -/
theorem relation_reduces (red : H →+ G) (lifts : Fin r → H)
    (coeff : Fin r → ℤ) (h : Relation lifts coeff) :
    Relation (fun i => red (lifts i)) coeff := by
  unfold Relation at *
  calc
    (∑ i, coeff i • red (lifts i)) = red (∑ i, coeff i • lifts i) := by
      simp
    _ = 0 := by rw [h]; simp

/-- A checked absence of bounded relations downstairs excludes every
nontrivial dependent lift covered by the coefficient bound. -/
theorem no_dependent_lift (red : H →+ G) (lifts : Fin r → H)
    (bound : ℕ)
    (height_bound : ∀ coeff, Nontrivial coeff → Relation lifts coeff →
      Bounded bound coeff)
    (no_small_reduced_relation : ∀ coeff, Nontrivial coeff →
      Bounded bound coeff →
      ¬ Relation (fun i => red (lifts i)) coeff) :
    ∀ coeff, Nontrivial coeff → ¬ Relation lifts coeff := by
  intro coeff hnon hrel
  exact no_small_reduced_relation coeff hnon
    (height_bound coeff hnon hrel) (relation_reduces red lifts coeff hrel)

/-- The same obstruction applies to every lift of a fixed reduced tuple,
including lifts selected by any auxiliary condition. -/
theorem all_compatible_lifts_blocked (red : H →+ G)
    (reduced : Fin r → G) (bound : ℕ)
    (height_bound : ∀ lifts : Fin r → H,
      (∀ i, red (lifts i) = reduced i) →
      ∀ coeff, Nontrivial coeff → Relation lifts coeff → Bounded bound coeff)
    (no_small_reduced_relation : ∀ coeff, Nontrivial coeff →
      Bounded bound coeff → ¬ Relation reduced coeff) :
    ∀ lifts : Fin r → H,
      (∀ i, red (lifts i) = reduced i) →
      ∀ coeff, Nontrivial coeff → ¬ Relation lifts coeff := by
  intro lifts hcompat coeff hnon hrel
  have hsmall := height_bound lifts hcompat coeff hnon hrel
  have hred : Relation reduced coeff := by
    simpa only [Relation, hcompat] using relation_reduces red lifts coeff hrel
  exact no_small_reduced_relation coeff hnon hsmall hred

end XedniObstruction

namespace XedniObstruction

variable {r q : ℕ}

/-- An integer of magnitude below the modulus cannot vanish on reduction
unless it was already zero. -/
theorem intCast_ne_zero_of_natAbs_lt {a : ℤ}
    (ha : a ≠ 0) (hbound : a.natAbs < q) : (a : ZMod q) ≠ 0 := by
  intro hcast
  have hd : (q : ℤ) ∣ a := (ZMod.intCast_zmod_eq_zero_iff_dvd a q).mp hcast
  have hlt : a.natAbs < (q : ℤ).natAbs := by simpa using hbound
  exact ha (Int.eq_zero_of_dvd_of_natAbs_lt_natAbs hd hlt)

/-- Every nontrivial coefficient vector in a box of radius below `q`
remains nonzero when passed to the subgroup scalar field. -/
theorem bounded_intVector_cast_nonzero (bound : ℕ) (hbound : bound < q)
    (coeff : Fin r → ℤ) (hnon : Nontrivial coeff)
    (hsmall : Bounded bound coeff) :
    ∃ i, (coeff i : ZMod q) ≠ 0 := by
  obtain ⟨i, hi⟩ := hnon
  exact ⟨i, intCast_ne_zero_of_natAbs_lt hi
    (lt_of_le_of_lt (hsmall i) hbound)⟩

noncomputable def reducedCandidates (candidates : Finset (Fin r → ℤ)) :
    Finset (Fin r → ZMod q) := by
  classical
  exact candidates.image (fun coeff i => (coeff i : ZMod q))

/-- With fixed public coefficients `s` and fixed target scalar `w`, choosing
the `t` coefficients uniformly is equivalent to choosing the reduced points
uniformly: the map is its own inverse. -/
def xedniSampleMap {F : Type*} [Field F]
    (s : Fin r → F) (w : F) (t : Fin r → F) : Fin r → F :=
  fun i => s i * w - t i

theorem xedniSampleMap_involutive {F : Type*} [Field F]
    (s : Fin r → F) (w : F) : Function.Involutive (xedniSampleMap s w) := by
  intro t
  funext i
  simp [xedniSampleMap]

theorem xedniSampleMap_bijective {F : Type*} [Field F]
    (s : Fin r → F) (w : F) : Function.Bijective (xedniSampleMap s w) :=
  (xedniSampleMap_involutive s w).bijective

end XedniObstruction

namespace XedniObstruction

variable {r : ℕ} {F : Type*} [Field F]

/-- Coordinates of independent uniformly sampled subgroup points after choosing
a generator of the prime-order subgroup. -/
def dotHom (coeff : Fin r → F) : (Fin r → F) →+ F where
  toFun points := ∑ i, coeff i * points i
  map_zero' := by simp
  map_add' x y := by simp [mul_add, Finset.sum_add_distrib]

/-- Any coefficient vector with a nonzero coordinate gives a surjective
relation map. This is the exact algebraic basis of the one-over-group-order
fiber count under independent uniform sampling. -/
theorem dotHom_surjective (coeff : Fin r → F)
    (hcoeff : ∃ i, coeff i ≠ 0) : Function.Surjective (dotHom coeff) := by
  obtain ⟨i, hi⟩ := hcoeff
  intro y
  refine ⟨fun j => if j = i then y / coeff i else 0, ?_⟩
  simp [dotHom, hi, mul_div_cancel₀]

/-- Every value of the relation map has the same fiber size; in particular
the zero-relation fiber has exactly one over `Nat.card F` of all tuples. -/
theorem zero_relation_fiber_count [Finite F] (coeff : Fin r → F)
    (hcoeff : ∃ i, coeff i ≠ 0) :
    Nat.card (dotHom coeff).ker * Nat.card F = Nat.card (Fin r → F) := by
  exact AddSubgroup.card_ker_mul_card_of_surjective
    (dotHom_surjective coeff hcoeff)

noncomputable def zeroFiber [Fintype F] (coeff : Fin r → F) : Finset (Fin r → F) := by
  classical
  exact Finset.univ.filter (fun points => dotHom coeff points = 0)

theorem zeroFiber_count [Fintype F] (coeff : Fin r → F)
    (hcoeff : ∃ i, coeff i ≠ 0) :
    (zeroFiber coeff).card * Nat.card F = Nat.card (Fin r → F) := by
  classical
  have hcard : (zeroFiber coeff).card = Nat.card (dotHom coeff).ker := by
    simp [zeroFiber, Nat.card_eq_fintype_card, Fintype.card_subtype,
      AddMonoidHom.mem_ker]
  rw [hcard]
  exact zero_relation_fiber_count coeff hcoeff

/-- Exact union bound for a fixed list of nonzero bounded coefficient
vectors under independent uniform sampling of the reduced points. -/
theorem bounded_relation_union_count [Fintype F] [DecidableEq F]
    (candidates : Finset (Fin r → F))
    (hnonzero : ∀ coeff ∈ candidates, ∃ i, coeff i ≠ 0) :
    (candidates.biUnion zeroFiber).card * Nat.card F ≤
      candidates.card * Nat.card (Fin r → F) := by
  classical
  calc
    (candidates.biUnion zeroFiber).card * Nat.card F ≤
        (∑ coeff ∈ candidates, (zeroFiber coeff).card) * Nat.card F := by
          exact Nat.mul_le_mul_right _ Finset.card_biUnion_le
    _ = ∑ coeff ∈ candidates, (zeroFiber coeff).card * Nat.card F := by
          rw [Finset.sum_mul]
    _ = ∑ coeff ∈ candidates, Nat.card (Fin r → F) := by
          apply Finset.sum_congr rfl
          intro coeff hc
          exact zeroFiber_count coeff (hnonzero coeff hc)
    _ = candidates.card * Nat.card (Fin r → F) := by simp

end XedniObstruction

namespace XedniObstruction

variable {r q : ℕ}

/-- A finite list of bounded nontrivial integer relations inherits the exact
finite-field union bound after reduction modulo a prime order `q`. -/
theorem integer_candidate_union_count [Fact q.Prime]
    (bound : ℕ) (hbound : bound < q)
    (candidates : Finset (Fin r → ℤ))
    (hvalid : ∀ coeff ∈ candidates,
      Nontrivial coeff ∧ Bounded bound coeff) :
    ((reducedCandidates (q := q) candidates).biUnion (zeroFiber (F := ZMod q))).card *
      Nat.card (ZMod q) ≤
      candidates.card * Nat.card (Fin r → ZMod q) := by
  classical
  have hnon : ∀ coeff ∈ reducedCandidates (q := q) candidates,
      ∃ i, coeff i ≠ (0 : ZMod q) := by
    intro coeff hc
    obtain ⟨a, ha, rfl⟩ := Finset.mem_image.mp hc
    exact bounded_intVector_cast_nonzero bound hbound a
      (hvalid a ha).1 (hvalid a ha).2
  have hcount := bounded_relation_union_count (F := ZMod q)
    (reducedCandidates (q := q) candidates) hnon
  exact hcount.trans (Nat.mul_le_mul_right _ Finset.card_image_le)

/-- The full-support sampling law transports each finite event without
changing its number of samples. -/
theorem xedni_sample_event_card {F : Type*} [Field F] [Fintype F]
    (s : Fin r → F) (w : F) (event : Finset (Fin r → F)) :
    (event.preimage (xedniSampleMap s w)
      (xedniSampleMap_bijective s w).1.injOn).card = event.card := by
  classical
  rw [Finset.card_preimage]
  simp [Function.Surjective.range_eq (xedniSampleMap_bijective s w).2]

/-- For fixed public coefficients and target scalar, a finite family of
bounded integer relations occupies at most `|candidates|/q` of the uniform
sample space. The count uses the exact preimage event under xedni sampling. -/
theorem sampled_integer_candidate_union_count [Fact q.Prime]
    (bound : ℕ) (hbound : bound < q)
    (candidates : Finset (Fin r → ℤ))
    (hvalid : ∀ coeff ∈ candidates,
      Nontrivial coeff ∧ Bounded bound coeff)
    (s : Fin r → ZMod q) (w : ZMod q) :
    (((reducedCandidates (q := q) candidates).biUnion
      (zeroFiber (F := ZMod q))).preimage (xedniSampleMap s w)
      (xedniSampleMap_bijective s w).1.injOn).card *
        Nat.card (ZMod q) ≤
      candidates.card * Nat.card (Fin r → ZMod q) := by
  rw [xedni_sample_event_card]
  exact integer_candidate_union_count bound hbound candidates hvalid

end XedniObstruction

#print axioms XedniObstruction.relation_reduces
#print axioms XedniObstruction.no_dependent_lift
#print axioms XedniObstruction.all_compatible_lifts_blocked
#print axioms XedniObstruction.dotHom_surjective
#print axioms XedniObstruction.zero_relation_fiber_count
#print axioms XedniObstruction.zeroFiber_count
#print axioms XedniObstruction.bounded_relation_union_count
#print axioms XedniObstruction.intCast_ne_zero_of_natAbs_lt
#print axioms XedniObstruction.bounded_intVector_cast_nonzero
#print axioms XedniObstruction.integer_candidate_union_count
#print axioms XedniObstruction.xedniSampleMap_involutive
#print axioms XedniObstruction.xedniSampleMap_bijective
#print axioms XedniObstruction.xedni_sample_event_card
#print axioms XedniObstruction.sampled_integer_candidate_union_count
