import Mathlib.LinearAlgebra.Prod

namespace PublicRowBlocks
variable {K A B X Y : Type*} [Field K]
  [AddCommGroup A] [Module K A] [AddCommGroup B] [Module K B]
  [AddCommGroup X] [Module K X] [AddCommGroup Y] [Module K Y]

/-- A and B carry row weights. X and Y are the disjoint column blocks. -/
theorem cancellation (f : A →ₗ[K] X) (g : B →ₗ[K] Y) (a : A) (b : B) :
    (f.prodMap g) (a,b) = 0 ↔ f a = 0 ∧ g b = 0 := by
  change (f a, g b) = (0,0) ↔ _
  exact Prod.mk.injEq .. ▸ Iff.rfl

theorem pooled_injective (f : A →ₗ[K] X) (g : B →ₗ[K] Y)
    (hf : Function.Injective f) (hg : Function.Injective g) :
    Function.Injective (f.prodMap g) := by
  intro a b eq
  exact Prod.ext (hf (congrArg Prod.fst eq)) (hg (congrArg Prod.snd eq))

#print axioms pooled_injective
end PublicRowBlocks
