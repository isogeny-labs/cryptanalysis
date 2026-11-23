import Mathlib.Tactic

namespace JointLiftCensus
variable {R : Type*} [CommRing R]

theorem cubic_step (x : R) :
    ((x+1)^3+(x+1) = (x^3+x) + (3*x^2+3*x+2)) ∧
    (3*(x+1)^2+3*(x+1)+2 = (3*x^2+3*x+2)+(6*x+6)) ∧
    (6*(x+1)+6 = (6*x+6)+6) := by
  constructor
  · ring
  constructor <;> ring

theorem target_step (x : R) : x^3+2*x+14 = (x^3+x)+x+14 := by ring

theorem square_step (y : R) : (y+1)^2 = y^2+(2*y+1) := by ring

end JointLiftCensus
