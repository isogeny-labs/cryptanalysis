import Mathlib

namespace XedniTargetChordOrigin

/-- If the chosen chord origin has source scalar `-(target + chordKnown)`,
the origin translation adds the total relation-coefficient sum to the
explicit coefficient of the target. -/
theorem target_chord_relation_expansion {R : Type*} [CommRing R]
    (targetCoefficient coefficientSum target knownSum chordKnown : R) :
    targetCoefficient * target + knownSum -
        coefficientSum * (-(target + chordKnown)) =
      (targetCoefficient + coefficientSum) * target +
        (knownSum + coefficientSum * chordKnown) := by
  ring

/-- A unit effective coefficient recovers the unknown target even when its
explicit relation coefficient is zero. -/
theorem target_chord_recovers {R : Type*} [CommRing R]
    (targetCoefficient coefficientSum target knownSum chordKnown inverse : R)
    (inverse_spec : inverse * (targetCoefficient + coefficientSum) = 1)
    (relation : targetCoefficient * target + knownSum -
        coefficientSum * (-(target + chordKnown)) = 0) :
    target = -inverse * (knownSum + coefficientSum * chordKnown) := by
  have linear :
      (targetCoefficient + coefficientSum) * target =
        -(knownSum + coefficientSum * chordKnown) := by
    linear_combination relation
  calc
    target = 1 * target := by ring
    _ = (inverse * (targetCoefficient + coefficientSum)) * target := by
      rw [inverse_spec]
    _ = inverse * ((targetCoefficient + coefficientSum) * target) := by ring
    _ = inverse * (-(knownSum + coefficientSum * chordKnown)) := by rw [linear]
    _ = -inverse * (knownSum + coefficientSum * chordKnown) := by ring

/-- With zero explicit target coefficient, the coefficient sum alone is the
effective target coefficient supplied by the target-dependent origin. -/
theorem zero_explicit_target_coefficient {R : Type*} [Ring R]
    (coefficientSum : R) :
    (0 : R) + coefficientSum = coefficientSum := by
  simp

#print axioms target_chord_relation_expansion
#print axioms target_chord_recovers
#print axioms zero_explicit_target_coefficient

end XedniTargetChordOrigin
