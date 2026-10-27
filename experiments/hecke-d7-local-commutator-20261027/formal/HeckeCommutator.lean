module

public import Mathlib.Tactic.Abel
public import Mathlib.Algebra.Module.LinearMap.Basic
public import Mathlib.Algebra.Field.Basic

/-! The abstract linear-algebra step used by the finite Hecke-row certificates.
The concrete Hecke correspondences and rational-fiber availability are checked
in the experiment's Sage and integer receipts. -/
namespace HeckeCommutator

variable {R M : Type*} [CommRing R] [AddCommGroup M] [Module R M]

/-- If two linear operators commute at `x`, their shifted row operators
commute there as well. The scalars are the Hecke eigenvalues. -/
public theorem shifted_commutator (A B : M →ₗ[R] M) (a b : R) (x : M)
    (hcomm : A (B x) = B (A x)) :
    B (A x - a • x) - b • (A x - a • x) =
      A (B x - b • x) - a • (B x - b • x) := by
  simp only [map_sub, map_smul, smul_sub, smul_smul]
  rw [hcomm]
  rw [mul_comm b a]
  abel

/-- An exact commutator equation with one nonzero target coefficient
isolates that row in the span of the available rows. -/
public theorem isolate_one_missing {K V : Type*} [Field K] [AddCommGroup V]
    [Module K V] (coefficient : K) (target known : V)
    (hne : coefficient ≠ 0) (h : coefficient • target + known = 0) :
    target = -(coefficient⁻¹ • known) := by
  have hsum : target + coefficient⁻¹ • known = 0 := by
    have hscaled := congrArg (fun y : V => coefficient⁻¹ • y) h
    simpa [smul_add, smul_smul, inv_mul_cancel₀ hne] using hscaled
  calc
    target = target + coefficient⁻¹ • known - coefficient⁻¹ • known := by abel
    _ = -(coefficient⁻¹ • known) := by rw [hsum]; simp

#print axioms shifted_commutator
#print axioms isolate_one_missing

end HeckeCommutator
