module

public import Mathlib.Algebra.Group.Hom.Defs

/-! Uniqueness of a relation solution once its residual kernel is fixed by seeds. -/
namespace SeedUniqueness

public theorem unique_of_relation_and_seed_values
    {V W S : Type*} [AddCommGroup V] [AddCommGroup W] [AddCommGroup S]
    (A : V →+ W) (seed : V →+ S)
    (hkernel : ∀ v : V, A v = 0 → seed v = 0 → v = 0)
    (x y : V) (hrelation : A x = A y) (hseed : seed x = seed y) : x = y := by
  have hzero : x - y = 0 := hkernel (x - y) (by simp [hrelation]) (by simp [hseed])
  calc
    x = x - y + y := (sub_add_cancel x y).symm
    _ = y := by rw [hzero]; simp

end SeedUniqueness

#print axioms SeedUniqueness.unique_of_relation_and_seed_values
