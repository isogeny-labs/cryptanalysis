import Std

namespace FourFiberSelector

/-- The triple conjunction of two terminal selectors and one raw-fiber
selector is active exactly at the selected state. -/
theorem tripleGateTrue (i j selectedI selectedJ : Fin 48)
    (raw selectedRaw : Fin 4) :
    ((decide (i = selectedI) && decide (j = selectedJ)) &&
      decide (raw = selectedRaw)) = true ↔
    i = selectedI ∧ j = selectedJ ∧ raw = selectedRaw := by
  simp [and_assoc]

/-- One field-coordinate coefficient contributes exactly at its selected
joint terminal and raw-fiber state. -/
theorem coefficientTerm (i j selectedI selectedJ : Fin 48)
    (raw selectedRaw : Fin 4) (coefficient : Bool) :
    (((decide (i = selectedI) && decide (j = selectedJ)) &&
       decide (raw = selectedRaw)) && coefficient) =
      (if i = selectedI ∧ j = selectedJ ∧ raw = selectedRaw
       then coefficient else false) := by
  by_cases hi : i = selectedI
  · by_cases hj : j = selectedJ
    · by_cases hr : raw = selectedRaw
      · simp [hi, hj, hr]
      · simp [hi, hj, hr]
    · simp [hi, hj]
  · simp [hi]

#print axioms tripleGateTrue
#print axioms coefficientTerm

end FourFiberSelector
