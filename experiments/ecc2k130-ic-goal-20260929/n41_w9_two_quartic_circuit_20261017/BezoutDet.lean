import Std
import Init.Grind.Ring.Basic

namespace BezoutDet
open Lean.Grind

/-- Unsigned 3-by-3 Leibniz expansion; signs coincide in characteristic two. -/
def det3 {R : Type} [CommRing R] (a b c d e f g h i : R) : R :=
  a*e*i + b*f*g + c*d*h + c*e*g + b*d*i + a*f*h

/-- Unsigned 4-by-4 Laplace expansion for a symmetric matrix. -/
def det4Sym {R : Type} [CommRing R]
    (a b c d e f g h i j : R) : R :=
  a*det3 b h i h c j i j d +
  e*det3 e h i f c j g j d +
  f*det3 e b i f h j g i d +
  g*det3 e b h f h c g i j

/-- In characteristic two, opposite non-involution permutations cancel.
The resulting determinant needs seven diagonal terms and one square. -/
theorem symmetric_det4_char2 {R : Type} [CommRing R]
    (charTwo : ∀ x : R, x+x=0) (a b c d e f g h i j : R) :
    det4Sym a b c d e f g h i j =
      a*b*c*d + e*e*c*d + f*f*b*d + g*g*b*c +
      h*h*a*d + i*i*a*c + j*j*a*b +
      (e*j+f*i+g*h)*(e*j+f*i+g*h) := by
  have h2 : (2 : R) = 0 := by
    have hz := charTwo 1
    grind +ring
  unfold det4Sym det3
  grind +ring

/-- Quartic evaluation written from low to high coefficients. -/
def poly4 {R : Type} [CommRing R] (c0 c1 c2 c3 c4 x : R) : R :=
  c0 + c1*x + c2*x*x + c3*x*x*x + c4*x*x*x*x

/-- The bivariate form of a symmetric four-by-four Bezout matrix. -/
def bezoutBivar {R : Type} [CommRing R]
    (a b c d e f g h i j x y : R) : R :=
  a + e*(x+y) + f*(x*x+y*y) + g*(x*x*x+y*y*y) +
  b*x*y + h*(x*x*y+x*y*y) + i*(x*x*x*y+x*y*y*y) +
  c*x*x*y*y + j*(x*x*x*y*y+x*x*y*y*y) + d*x*x*x*y*y*y

/-- The ten bilinear coefficient combinations used in the circuit
really are the Bezout quotient of the two quartics. -/
theorem quartic_bezout_factor_char2 {R : Type} [CommRing R]
    (charTwo : ∀ t : R, t+t=0)
    (f0 f1 f2 f3 f4 g0 g1 g2 g3 g4 x y : R) :
    let k10 := f1*g0+f0*g1
    let k20 := f2*g0+f0*g2
    let k30 := f3*g0+f0*g3
    let k40 := f4*g0+f0*g4
    let k21 := f2*g1+f1*g2
    let k31 := f3*g1+f1*g3
    let k41 := f4*g1+f1*g4
    let k32 := f3*g2+f2*g3
    let k42 := f4*g2+f2*g4
    let k43 := f4*g3+f3*g4
    poly4 f0 f1 f2 f3 f4 x * poly4 g0 g1 g2 g3 g4 y +
      poly4 f0 f1 f2 f3 f4 y * poly4 g0 g1 g2 g3 g4 x =
      (x+y) * bezoutBivar k10 (k21+k30) (k32+k41) k43
        k20 k30 k40 (k31+k40) k41 k42 x y := by
  have h2 : (2 : R) = 0 := by
    have hz := charTwo 1
    grind +ring
  dsimp [poly4, bezoutBivar]
  grind +ring

#print axioms BezoutDet.symmetric_det4_char2
#print axioms BezoutDet.quartic_bezout_factor_char2

end BezoutDet
