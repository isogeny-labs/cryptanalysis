module

public import Mathlib.LinearAlgebra.FiniteDimensional.Basic

/-!
Every derived Hecke coefficient row is a finite linear combination of the
lifted sources' class-part rows. The theorem is independent of the D79 curve
and states the row-space and rank-gain implication over an arbitrary field.
-/

namespace ClasspartSpanBound

open scoped BigOperators

variable {F : Type*} [Field F]
variable {n : Nat} {B S H : Type*}
variable [Fintype B] [Fintype S] [Fintype H]

public def rowSpan (rows : B → (Fin n → F)) : Submodule F (Fin n → F) :=
  Submodule.span F (Set.range rows)

public def derivedRow (source : S → (Fin n → F)) (coeff : H → S → F)
    (i : H) : Fin n → F :=
  ∑ j : S, coeff i j • source j

public theorem derived_mem_source_span (source : S → (Fin n → F))
    (coeff : H → S → F) (i : H) :
    derivedRow source coeff i ∈ Submodule.span F (Set.range source) := by
  classical
  unfold derivedRow
  apply Submodule.sum_mem
  intro j _
  exact Submodule.smul_mem _ _ (Submodule.subset_span ⟨j, rfl⟩)

public theorem derived_span_le_source_span (source : S → (Fin n → F))
    (coeff : H → S → F) :
    Submodule.span F (Set.range (derivedRow source coeff)) ≤
      Submodule.span F (Set.range source) := by
  apply Submodule.span_le.mpr
  rintro _ ⟨i, rfl⟩
  exact derived_mem_source_span source coeff i

public theorem augmented_span_le (baseline : B → (Fin n → F))
    (source : S → (Fin n → F)) (coeff : H → S → F) :
    (Submodule.span F (Set.range baseline) ⊔
      Submodule.span F (Set.range (derivedRow source coeff))) ≤
      (Submodule.span F (Set.range baseline) ⊔
        Submodule.span F (Set.range source)) := by
  exact sup_le le_sup_left ((derived_span_le_source_span source coeff).trans le_sup_right)

public theorem augmented_rank_le (baseline : B → (Fin n → F))
    (source : S → (Fin n → F)) (coeff : H → S → F) :
    Module.finrank F ↥(Submodule.span F (Set.range baseline) ⊔
      Submodule.span F (Set.range (derivedRow source coeff))) ≤
    Module.finrank F ↥(Submodule.span F (Set.range baseline) ⊔
      Submodule.span F (Set.range source)) := by
  exact Submodule.finrank_mono (augmented_span_le baseline source coeff)

public theorem rank_gain_le (baseline : B → (Fin n → F))
    (source : S → (Fin n → F)) (coeff : H → S → F) :
    Module.finrank F ↥(Submodule.span F (Set.range baseline) ⊔
      Submodule.span F (Set.range (derivedRow source coeff))) -
      Module.finrank F ↥(Submodule.span F (Set.range baseline)) ≤
    Module.finrank F ↥(Submodule.span F (Set.range baseline) ⊔
      Submodule.span F (Set.range source)) -
      Module.finrank F ↥(Submodule.span F (Set.range baseline)) := by
  exact Nat.sub_le_sub_right (augmented_rank_le baseline source coeff) _

#print axioms derived_mem_source_span
#print axioms derived_span_le_source_span
#print axioms augmented_span_le
#print axioms augmented_rank_le
#print axioms rank_gain_le

end ClasspartSpanBound
