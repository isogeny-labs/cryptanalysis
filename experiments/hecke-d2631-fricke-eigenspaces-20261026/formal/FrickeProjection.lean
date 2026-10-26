module

public import Mathlib.Tactic.Ring

/-! Pair-coordinate invertibility underlying the `+`/`-` matrix split. -/
namespace FrickeProjection

/-- The plus and minus coordinates reconstruct the two original rational
coordinates. Applied pairwise, this makes the Fricke coordinate change
invertible over `ℚ`. -/
public theorem recover_first (x y : ℚ) :
    ((x + y) + (x - y)) / 2 = x := by ring

public theorem recover_second (x y : ℚ) :
    ((x + y) - (x - y)) / 2 = y := by ring

end FrickeProjection

#print axioms FrickeProjection.recover_first
#print axioms FrickeProjection.recover_second
