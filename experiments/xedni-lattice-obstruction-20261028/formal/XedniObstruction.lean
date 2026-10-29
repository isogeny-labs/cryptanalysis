import Mathlib.LinearAlgebra.FiniteDimensional.Basic
import Mathlib.GroupTheory.Index
import Mathlib.Algebra.Order.BigOperators.Group.Finset

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

#print axioms XedniObstruction.relation_reduces
#print axioms XedniObstruction.no_dependent_lift
#print axioms XedniObstruction.all_compatible_lifts_blocked
#print axioms XedniObstruction.dotHom_surjective
#print axioms XedniObstruction.zero_relation_fiber_count
#print axioms XedniObstruction.zeroFiber_count
#print axioms XedniObstruction.bounded_relation_union_count
