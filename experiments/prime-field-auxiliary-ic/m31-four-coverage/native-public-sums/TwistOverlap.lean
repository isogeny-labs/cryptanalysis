import Std

namespace M31.TwistOverlap

/-- On an abscissa with nonzero cubic value, true means it is a square. -/
def sign (square : Bool) : Int := if square then 1 else -1

/-- Each row records the two square tests at the same abscissa. -/
def overlap (rows : List (Bool × Bool)) : Int :=
  ((rows.filter fun r => r.1 && r.2).length : Int)

theorem four_overlap (rows : List (Bool × Bool)) :
    4 * overlap rows = (rows.length : Int) +
      (rows.map fun r => sign r.1).sum +
      (rows.map fun r => sign r.2).sum +
      (rows.map fun r => sign r.1 * sign r.2).sum := by
  induction rows with
  | nil => simp [overlap]
  | cons row rows ih =>
    rcases row with ⟨a,b⟩
    unfold overlap at *
    cases a <;> cases b <;> simp [sign] at * <;> omega

/-- The numeric correlation and cancellation of the two marginal character
sums are explicit hypotheses, allowing independent trace certification. -/
theorem m31_overlap (rows : List (Bool × Bool))
    (size : rows.length = 2147483647)
    (cancel : (rows.map fun r => sign r.1).sum +
      (rows.map fun r => sign r.2).sum = 0)
    (correlation : (rows.map fun r => sign r.1 * sign r.2).sum =
      -1 - 68941 - 37001) : overlap rows = 536844426 := by
  have count := four_overlap rows
  rw [size] at count
  omega

end M31.TwistOverlap
