import Std

/- The integer identity proves the cleared addition formula modulo two.
   The bridge from the cleared polynomial to the elliptic-curve group law
   is checked separately in Sage and remains an explicit formalization step. -/
namespace Adjacent

def curvePoly (x y : Int) : Int := y*y+x*y+x*x*x+1

def adjacentNumerator (x y : Int) : Int :=
  let d := x+x*x
  let q := y+y*y
  x*q*q + x*q*d + x*x*x*d*d + d*d

def quotientPoly (x y : Int) : Int := x*y*y+x*x*y+x^4+x*x

def remainderHalf (x y : Int) : Int :=
  x^6-x^5*y-x^4*y^2+x^3-x^2*y^3+x*y^3

theorem adjacent_polynomial_identity (x y : Int) :
    adjacentNumerator x y =
      curvePoly x y * quotientPoly x y + 2 * remainderHalf x y := by
  unfold adjacentNumerator curvePoly quotientPoly remainderHalf
  grind +ring

theorem adjacent_parity (x y h : Int) (hc : curvePoly x y = 2*h) :
    ∃ k : Int, adjacentNumerator x y = 2*k := by
  refine ⟨h*quotientPoly x y+remainderHalf x y, ?_⟩
  rw [adjacent_polynomial_identity, hc]
  grind +ring

#print axioms adjacent_polynomial_identity
#print axioms adjacent_parity

end Adjacent
