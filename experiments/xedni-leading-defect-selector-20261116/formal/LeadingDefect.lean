import Mathlib.Data.ZMod.Basic

namespace XedniLeadingDefect

/-- The first graded piece of a formal group is additive. This lemma applies
to its leading-coefficient map once that map has been constructed as an additive
homomorphism. The EC formal-group construction is a separate proof obligation. -/
theorem leading_linear_combination {K : Type*} [AddCommGroup K]
    (lead : K →+ ZMod p) (P₁ P₂ : K) (a b : ℤ) :
    lead (a • P₁ + b • P₂) = a • lead P₁ + b • lead P₂ := by
  simp

/-- Under the same explicit homomorphism hypothesis, cancellation of the
leading residue is equivalent to lying in the kernel. -/
theorem leading_cancellation_iff_kernel {K : Type*} [AddCommGroup K]
    (lead : K →+ ZMod p) (P₁ P₂ : K) (a b : ℤ) :
    a • lead P₁ + b • lead P₂ = 0 ↔
      a • P₁ + b • P₂ ∈ lead.ker := by
  rw [AddMonoidHom.mem_ker, leading_linear_combination]

#print axioms leading_linear_combination
#print axioms leading_cancellation_iff_kernel

end XedniLeadingDefect
