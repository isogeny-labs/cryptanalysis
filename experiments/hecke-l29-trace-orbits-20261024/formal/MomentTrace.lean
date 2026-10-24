import Mathlib.LinearAlgebra.Vandermonde

/-!
For distinct neighbor abscissas, the matrix used to reconstruct the
ordinate polynomial from mixed power sums is invertible.  The finite
degree-29 computation supplies the abscissas and moments externally.
-/

namespace MomentTrace

open Matrix

variable {K : Type*} [Field K] {n : ℕ}

def momentMatrix (x : Fin n → K) : Matrix (Fin n) (Fin n) K :=
  Matrix.of fun i j => ∑ k : Fin n, x k ^ (i + j : ℕ)

theorem momentMatrix_eq_gram (x : Fin n → K) :
    momentMatrix x = (vandermonde x)ᵀ * vandermonde x := by
  ext i j
  exact (vandermonde_transpose_mul_vandermonde x i j).symm

theorem momentMatrix_det_ne_zero (x : Fin n → K) (hx : Function.Injective x) :
    (momentMatrix x).det ≠ 0 := by
  have hv : (vandermonde x).det ≠ 0 := by
    intro hz
    obtain ⟨i, j, hij, hne⟩ := (det_vandermonde_eq_zero_iff.mp hz)
    exact hne (hx hij)
  rw [momentMatrix_eq_gram, det_mul, det_transpose]
  exact mul_ne_zero hv hv

theorem momentMatrix_mulVec_injective (x : Fin n → K) (hx : Function.Injective x) :
    Function.Injective (momentMatrix x).mulVec := by
  apply mulVec_injective_iff_isUnit.mpr
  apply (momentMatrix x).isUnit_iff_isUnit_det.mpr
  exact isUnit_iff_ne_zero.mpr (momentMatrix_det_ne_zero x hx)

theorem moment_reconstruction_unique (x : Fin n → K) (hx : Function.Injective x)
    (observed left right : Fin n → K)
    (hleft : (momentMatrix x).mulVec left = observed)
    (hright : (momentMatrix x).mulVec right = observed) :
    left = right :=
  momentMatrix_mulVec_injective x hx (hleft.trans hright.symm)

/-- A complete Frobenius orbit has a trace fixed by Frobenius.  The concrete
    fixed-point-to-rational-point bridge is supplied by the finite-field
    certificate rather than assumed here. -/
theorem cyclic_trace_fixed {G : Type*} [AddCommGroup G]
    (σ : G →+ G) (f : ℕ → G) (d : ℕ)
    (hstep : ∀ i, σ (f i) = f (i + 1)) (hperiod : f d = f 0) :
    σ (∑ i ∈ Finset.range d, f i) = ∑ i ∈ Finset.range d, f i := by
  rw [map_sum]
  simp_rw [hstep]
  have hrotate := (Finset.sum_range_succ f d).symm.trans
    (Finset.sum_range_succ' f d)
  rw [hperiod] at hrotate
  have h : (∑ i ∈ Finset.range d, f i) =
      ∑ i ∈ Finset.range d, f (i + 1) := add_right_cancel hrotate
  exact h.symm

#print axioms momentMatrix_eq_gram
#print axioms momentMatrix_det_ne_zero
#print axioms momentMatrix_mulVec_injective
#print axioms moment_reconstruction_unique
#print axioms cyclic_trace_fixed

end MomentTrace
