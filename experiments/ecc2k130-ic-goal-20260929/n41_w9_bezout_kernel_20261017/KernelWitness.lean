import Std
import Init.Grind.Ring.Basic

namespace KernelWitness
open Lean.Grind

def poly4 {R : Type} [CommRing R] (c0 c1 c2 c3 c4 x : R) : R :=
  c0 + c1*x + c2*x*x + c3*x*x*x + c4*x*x*x*x

/-- Every Bezout row is a linear combination of the two evaluated
quartics, with coefficients given by their polynomial tails. -/
theorem row_tail_identity {R : Type} [CommRing R]
    (charTwo : ∀ t : R, t+t=0)
    (f0 f1 f2 f3 f4 g0 g1 g2 g3 g4 w : R) :
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
    k10+k20*w+k30*w*w+k40*w*w*w =
      poly4 g0 g1 g2 g3 g4 w*(f1+f2*w+f3*w*w+f4*w*w*w) +
      poly4 f0 f1 f2 f3 f4 w*(g1+g2*w+g3*w*w+g4*w*w*w) ∧
    k20+(k21+k30)*w+(k31+k40)*w*w+k41*w*w*w =
      poly4 g0 g1 g2 g3 g4 w*(f2+f3*w+f4*w*w) +
      poly4 f0 f1 f2 f3 f4 w*(g2+g3*w+g4*w*w) ∧
    k30+(k31+k40)*w+(k32+k41)*w*w+k42*w*w*w =
      poly4 g0 g1 g2 g3 g4 w*(f3+f4*w) +
      poly4 f0 f1 f2 f3 f4 w*(g3+g4*w) ∧
    k40+k41*w+k42*w*w+k43*w*w*w =
      poly4 g0 g1 g2 g3 g4 w*f4 +
      poly4 f0 f1 f2 f3 f4 w*g4 := by
  have h2 : (2 : R)=0 := by
    have hz:=charTwo 1
    grind +ring
  dsimp [poly4]
  constructor
  · grind +ring
  constructor
  · grind +ring
  constructor
  · grind +ring
  · grind +ring

/-- A shared root yields the normalized right-kernel vector
`(1,w,w²,w³)` for the quartic Bezout matrix. -/
theorem common_root_kernel {R : Type} [CommRing R]
    (charTwo : ∀ t : R, t+t=0)
    (f0 f1 f2 f3 f4 g0 g1 g2 g3 g4 w : R)
    (hf : poly4 f0 f1 f2 f3 f4 w=0)
    (hg : poly4 g0 g1 g2 g3 g4 w=0) :
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
    k10+k20*w+k30*w*w+k40*w*w*w=0 ∧
    k20+(k21+k30)*w+(k31+k40)*w*w+k41*w*w*w=0 ∧
    k30+(k31+k40)*w+(k32+k41)*w*w+k42*w*w*w=0 ∧
    k40+k41*w+k42*w*w+k43*w*w*w=0 := by
  have h := row_tail_identity charTwo f0 f1 f2 f3 f4 g0 g1 g2 g3 g4 w
  dsimp at h ⊢
  rcases h with ⟨h0,h1,h2,h3⟩
  constructor
  · rw [h0,hf,hg]; grind +ring
  constructor
  · rw [h1,hf,hg]; grind +ring
  constructor
  · rw [h2,hf,hg]; grind +ring
  · rw [h3,hf,hg]; grind +ring

/-- Unsigned 3-by-3 determinant in characteristic two. -/
def det3 {R : Type} [CommRing R] (a b c d e f g h i : R) : R :=
  a*e*i+b*f*g+c*d*h+c*e*g+b*d*i+a*f*h

def det4Sym {R : Type} [CommRing R]
    (a b c d e f g h i j : R) : R :=
  a*det3 b h i h c j i j d +
  e*det3 e h i f c j g j d +
  f*det3 e b i f h j g i d +
  g*det3 e b h f h c g i j

/-- The first-column cofactor identity, with a normalized kernel vector.
The three extra column terms cancel pairwise in characteristic two. -/
theorem det_as_kernel_rows {R : Type} [CommRing R]
    (charTwo : ∀ t : R, t+t=0)
    (a b c d e f g h i j u v w : R) :
    det4Sym a b c d e f g h i j =
      det3 b h i h c j i j d*(a+e*u+f*v+g*w) +
      det3 e f g h c j i j d*(e+b*u+h*v+i*w) +
      det3 e f g b h i i j d*(f+h*u+c*v+j*w) +
      det3 e f g b h i h c j*(g+i*u+j*v+d*w) := by
  have h2 : (2 : R)=0 := by
    have hz:=charTwo 1
    grind +ring
  unfold det4Sym det3
  grind +ring

theorem normalized_kernel_implies_det_zero {R : Type} [CommRing R]
    (charTwo : ∀ t : R, t+t=0)
    (a b c d e f g h i j u v w : R)
    (h0 : a+e*u+f*v+g*w=0)
    (h1 : e+b*u+h*v+i*w=0)
    (h2 : f+h*u+c*v+j*w=0)
    (h3 : g+i*u+j*v+d*w=0) :
    det4Sym a b c d e f g h i j=0 := by
  rw [det_as_kernel_rows charTwo a b c d e f g h i j u v w]
  rw [h0,h1,h2,h3]
  grind +ring

#print axioms KernelWitness.row_tail_identity
#print axioms KernelWitness.common_root_kernel
#print axioms KernelWitness.det_as_kernel_rows
#print axioms KernelWitness.normalized_kernel_implies_det_zero

end KernelWitness
