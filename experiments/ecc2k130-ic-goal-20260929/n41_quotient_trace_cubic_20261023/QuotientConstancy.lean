import Std

namespace QuotientCubic

variable {K : Type}

/-- An exact quotient identity certifies a constant value at every root. -/
theorem constant_remainder_sound (zero : K) (add mul : K → K → K)
    (H P Q : K → K) (u b : K)
    (hzero : ∀ x : K, mul zero x = zero)
    (hadd : ∀ x : K, add x zero = x)
    (hroot : H u = zero)
    (hdiv : ∀ v : K, P v = add b (mul (H v) (Q v))) : P u = b := by
  simpa [hroot, hzero, hadd] using hdiv u

/-- A constant residue with the opposite target bit rules out that root. -/
theorem reject_mismatch (zero : K) (add mul : K → K → K)
    (H P Q : K → K) (u b targetBit : K)
    (hzero : ∀ x : K, mul zero x = zero)
    (hadd : ∀ x : K, add x zero = x)
    (hroot : H u = zero)
    (hdiv : ∀ v : K, P v = add b (mul (H v) (Q v)))
    (hmismatch : b ≠ targetBit) : P u ≠ targetBit := by
  rw [constant_remainder_sound zero add mul H P Q u b hzero hadd hroot hdiv]
  exact hmismatch

#print axioms constant_remainder_sound
#print axioms reject_mismatch

end QuotientCubic
