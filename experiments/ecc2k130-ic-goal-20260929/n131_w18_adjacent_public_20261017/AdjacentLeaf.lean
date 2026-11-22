import Std

/- Exact integer-polynomial parts of the two-way adjacent leaf. -/
namespace AdjacentLeaf

def denominator (a e : Int) : Int := 1 + a^2 + e*a^4
def numerator (a e : Int) : Int := a + e*a^3

theorem plus_branch (a : Int) :
    denominator a 0 = 1+a^2 ∧ numerator a 0 = a := by
  simp [denominator, numerator]

theorem minus_branch (a : Int) :
    denominator a 1 = 1+a^2+a^4 ∧
    numerator a 1 = a+a^3 := by
  simp [denominator, numerator]

theorem composed_denominator_mod_two (a : Int) :
    (1+a^2)^2+a^2 = (1+a^2+a^4)+2*a^2 := by
  grind +ring

#print axioms plus_branch
#print axioms minus_branch
#print axioms composed_denominator_mod_two

end AdjacentLeaf
