import Mathlib.LinearAlgebra.Matrix.Nondegenerate

namespace DirectLiftRank

/-- A nonzero pivot minor excludes any nonzero coefficient vector in its kernel.
    The experiment supplies the minors as independently replayed data. -/
theorem no_relation_of_nonzero_minor
    {n : ℕ} {R : Type*} [CommRing R] [NoZeroDivisors R]
    (minor : Matrix (Fin n) (Fin n) R) (coeff : Fin n → R)
    (hdet : minor.det ≠ 0) (hvanish : Matrix.mulVec minor coeff = 0) :
    coeff = 0 := by
  exact (minor.mulVec_injective_of_det_ne_zero hdet) (by simpa using hvanish)

#print axioms no_relation_of_nonzero_minor

end DirectLiftRank
