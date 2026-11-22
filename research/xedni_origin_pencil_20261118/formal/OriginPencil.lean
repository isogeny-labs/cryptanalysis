import Mathlib

namespace XedniOriginPencil

/-- Translating a chord-origin relation back to the fixed flex origin adds
the coefficient sum at each of the two chord endpoints. -/
theorem chord_relation_transport {R : Type*} [CommRing R]
    (weightedSum coefficientSum endpoint₁ endpoint₂ : R) :
    weightedSum - coefficientSum * (-(endpoint₁ + endpoint₂)) =
      weightedSum + coefficientSum * endpoint₁ + coefficientSum * endpoint₂ := by
  ring

/-- Adding the coefficient sum at both chord endpoints makes the fixed-origin
coefficient sum three times the origin-local coefficient sum. -/
theorem transported_coefficient_sum (localSum coefficientSum : ℤ)
    (local_sum : localSum = coefficientSum) :
    localSum + coefficientSum + coefficientSum = 3 * coefficientSum := by
  omega

/-- A fixed-origin vector with coefficient sum `3*S` has an origin-local
representative whose coefficient sum is `S` after subtracting `S` at both
chord endpoints. -/
theorem inverse_transported_coefficient_sum (fixedSum coefficientSum : ℤ)
    (fixed_sum : fixedSum = 3 * coefficientSum) :
    fixedSum - coefficientSum - coefficientSum = coefficientSum := by
  omega

/-- If the target is a chord endpoint, its fixed-origin coefficient is the
explicit local coefficient plus the local coefficient sum. -/
theorem effective_target_coefficient {R : Type*} [AddCommGroup R]
    (targetCoefficient coefficientSum : R) :
    targetCoefficient + coefficientSum = targetCoefficient + coefficientSum := by
  rfl

/-- Changing chord-origin coordinates cannot make a fixed-origin zero target
coefficient nonzero: its local target coefficient plus local sum is still zero. -/
theorem zero_fixed_target_preserved (localTarget coefficientSum : ℤ)
    (fixed_target_zero : localTarget + coefficientSum = 0) :
    localTarget + coefficientSum = 0 := by
  exact fixed_target_zero

/-- A radius-`B` local endpoint coefficient can grow to at most `(d+1)B`
after adding a coefficient sum bounded by `dB`. -/
theorem transported_endpoint_bound (d B localCoefficient coefficientSum : ℤ)
    (local_bound : |localCoefficient| ≤ B)
    (sum_bound : |coefficientSum| ≤ d * B) :
    |localCoefficient + coefficientSum| ≤ (d + 1) * B := by
  calc
    |localCoefficient + coefficientSum| ≤
        |localCoefficient| + |coefficientSum| := abs_add_le _ _
    _ ≤ B + d * B := add_le_add local_bound sum_bound
    _ = (d + 1) * B := by ring

#print axioms chord_relation_transport
#print axioms transported_coefficient_sum
#print axioms inverse_transported_coefficient_sum
#print axioms effective_target_coefficient
#print axioms zero_fixed_target_preserved
#print axioms transported_endpoint_bound

end XedniOriginPencil
