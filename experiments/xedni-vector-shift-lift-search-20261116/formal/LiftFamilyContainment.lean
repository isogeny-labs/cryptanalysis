import Mathlib

/-!
An indexed candidate family may change its rational group, reduction map,
point lifts and coefficient vector for every attempt. A compatible rational
relation in any candidate still maps to the same-vector public relation.
-/

theorem indexed_lift_relation_reduces
    {I F : Type*} [AddCommGroup F]
    (R : I → Type*) [∀ i, AddCommGroup (R i)]
    (reduce : ∀ i, R i →+ F) (P Q : ∀ i, R i)
    (a b : I → ℤ) (U V : F)
    (hP : ∀ i, reduce i (P i) = U)
    (hQ : ∀ i, reduce i (Q i) = V) :
    (∃ i, a i • P i + b i • Q i = 0) →
      ∃ i, a i • U + b i • V = 0 := by
  rintro ⟨i, hi⟩
  refine ⟨i, ?_⟩
  have h := congrArg (reduce i) hi
  simpa [map_add, map_zsmul, hP i, hQ i] using h

theorem indexed_query_lift_relation_reduces
    {I F : Type*} [AddCommGroup F]
    (R : I → Type*) [∀ i, AddCommGroup (R i)]
    (reduce : ∀ i, R i →+ F) (P Q : ∀ i, R i)
    (a b : I → ℤ) (U V : I → F)
    (hP : ∀ i, reduce i (P i) = U i)
    (hQ : ∀ i, reduce i (Q i) = V i) :
    (∃ i, a i • P i + b i • Q i = 0) →
      ∃ i, a i • U i + b i • V i = 0 := by
  rintro ⟨i, hi⟩
  refine ⟨i, ?_⟩
  have h := congrArg (reduce i) hi
  simpa [map_add, map_zsmul, hP i, hQ i] using h

theorem indexed_lift_no_public_relation
    {I F : Type*} [AddCommGroup F]
    (R : I → Type*) [∀ i, AddCommGroup (R i)]
    (reduce : ∀ i, R i →+ F) (P Q : ∀ i, R i)
    (a b : I → ℤ) (U V : F)
    (hP : ∀ i, reduce i (P i) = U)
    (hQ : ∀ i, reduce i (Q i) = V)
    (hnone : ∀ i, a i • U + b i • V ≠ 0) :
    ∀ i, a i • P i + b i • Q i ≠ 0 := by
  intro i hi
  obtain ⟨j, hj⟩ := indexed_lift_relation_reduces R reduce P Q a b U V hP hQ ⟨i, hi⟩
  exact hnone j hj

theorem fixed_vector_lift_search_containment
    {I F : Type*} [AddCommGroup F]
    (R : I → Type*) [∀ i, AddCommGroup (R i)]
    (reduce : ∀ i, R i →+ F) (P Q : ∀ i, R i)
    (a b : ℤ) (U V : F)
    (hP : ∀ i, reduce i (P i) = U)
    (hQ : ∀ i, reduce i (Q i) = V) :
    (∃ i, a • P i + b • Q i = 0) → a • U + b • V = 0 := by
  rintro ⟨i, hi⟩
  have h := congrArg (reduce i) hi
  simpa [map_add, map_zsmul, hP i, hQ i] using h

#print axioms indexed_lift_relation_reduces
#print axioms indexed_query_lift_relation_reduces
#print axioms indexed_lift_no_public_relation
#print axioms fixed_vector_lift_search_containment
