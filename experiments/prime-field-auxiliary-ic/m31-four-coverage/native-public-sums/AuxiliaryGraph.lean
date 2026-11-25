import Mathlib

namespace AuxiliaryGraph

variable {K X Y Z : Type*} [Field K]
  [AddCommGroup X] [Module K X] [AddCommGroup Y] [Module K Y]
  [AddCommGroup Z] [Module K Z]

/-- The augmented system requires y = L x and A x + B y = 0. -/
def solutions (L : X →ₗ[K] Y) (A : X →ₗ[K] Z) (B : Y →ₗ[K] Z) :
    Submodule K (X × Y) where
  carrier := {v | v.2 = L v.1 ∧ A v.1 + B v.2 = 0}
  zero_mem' := by simp
  add_mem' := by
    rintro ⟨x,y⟩ ⟨u,v⟩ ⟨hy,h⟩ ⟨hv,k⟩
    exact ⟨by simpa using congrArg₂ (· + ·) hy hv, by
      change A (x+u) + B (y+v) = 0
      rw [map_add, map_add, add_add_add_comm, h, k, add_zero]⟩
  smul_mem' := by
    rintro t ⟨x,y⟩ ⟨hy,h⟩
    exact ⟨by simpa using congrArg (t • ·) hy, by
      change A (t • x) + B (t • y) = 0
      rw [map_smul, map_smul, ← smul_add, h, smul_zero]⟩

/-- Projection onto the old variables loses no information. -/
def eliminate (L : X →ₗ[K] Y) (A : X →ₗ[K] Z) (B : Y →ₗ[K] Z) :
    solutions L A B ≃ₗ[K] LinearMap.ker (A + B.comp L) where
  toFun v := ⟨v.val.1, by
    change A v.val.1 + B (L v.val.1) = 0
    rw [← v.property.1]
    exact v.property.2⟩
  invFun x := ⟨(x.val, L x.val), rfl, x.property⟩
  left_inv v := Subtype.ext (Prod.ext rfl v.property.1.symm)
  right_inv _ := rfl
  map_add' _ _ := rfl
  map_smul' _ _ := rfl

theorem solution_dimension (L : X →ₗ[K] Y) (A : X →ₗ[K] Z) (B : Y →ₗ[K] Z) :
    Module.finrank K (solutions L A B) = Module.finrank K (LinearMap.ker (A+B.comp L)) :=
  (eliminate L A B).finrank_eq

/-- The independent constraints on the old variables are measured by the
rank of the substituted rows. X may itself be a previous solution space. -/
theorem rank_budget [FiniteDimensional K X]
    (L : X →ₗ[K] Y) (A : X →ₗ[K] Z) (B : Y →ₗ[K] Z) :
    Module.finrank K (LinearMap.range (A + B.comp L)) +
      Module.finrank K (solutions L A B) = Module.finrank K X := by
  rw [solution_dimension]
  exact (A + B.comp L).finrank_range_add_finrank_ker

/-- Every assignment extends exactly once when the additional rows vanish
after substituting the definitions of the auxiliary variables. -/
theorem unique_extension (L : X →ₗ[K] Y) (A : X →ₗ[K] Z) (B : Y →ₗ[K] Z)
    (h : A + B.comp L = 0) (x : X) :
    ∃! y, (x,y) ∈ solutions L A B := by
  refine ⟨L x, ⟨rfl, ?_⟩, fun _ hy => hy.1⟩
  exact LinearMap.congr_fun h x

#print axioms rank_budget
#print axioms solution_dimension
#print axioms unique_extension
end AuxiliaryGraph
