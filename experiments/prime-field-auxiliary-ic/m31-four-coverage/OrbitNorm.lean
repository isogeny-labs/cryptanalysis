import Mathlib.Tactic
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.LegendreSymbol.QuadraticChar.Basic

namespace M31OrbitNorm
variable {R : Type*} [CommRing R]

structure Cubic (R : Type*) where
  a : R
  b : R
  c : R
  d : R
deriving DecidableEq

def ev (f : Cubic R) (x : R) := ((f.a*x+f.b)*x+f.c)*x+f.d

def shift (f : Cubic R) (t : R) : Cubic R :=
  ⟨f.a, f.b+3*f.a*t, f.c+2*f.b*t+3*f.a*t^2, ev f t⟩

theorem shift_eval (f : Cubic R) (t x : R) : ev (shift f t) x = ev f (x+t) := by
  simp only [ev, shift]; ring

def norm (f : Cubic R) (B : R) : Cubic R :=
  let h := f.a*f.d
  let j := f.a*f.c*B+f.b*f.d
  ⟨h,j,f.a*f.b*B^2+f.b*f.c*B+f.c*f.d-3*B*h,
   f.a^2*B^3+f.b^2*B^2+f.c^2*B+f.d^2-2*B*j⟩

theorem norm_eval (f : Cubic R) (x z : R) :
    ev (norm f (x*z)) (x+z) = ev f x * ev f z := by
  simp only [ev, norm]; ring

structure Step (R : Type*) where
  t : R
  A : R
  B : R

def descend (f : Cubic R) (s : Step R) :=
  shift (norm (shift f s.t) s.B) (-s.A)

theorem paired (f : Cubic R) (s : Step R) (x z : R)
    (h : (x-s.t)*(z-s.t) = s.B) :
    ev (descend f s) (x-s.t+(z-s.t)+s.A) = ev f x * ev f z := by
  simp only [descend, shift_eval, add_neg_cancel_right]
  rw [← h, norm_eval, shift_eval, shift_eval]
  simp

/-- A quotient level pairs two equally shaped child fibers. -/
inductive Fiber (R : Type*) where
  | leaf (x : R)
  | pair (left right : Fiber R)

def product (f : Cubic R) : Fiber R → R
  | .leaf x => ev f x
  | .pair l r => product f l * product f r

inductive Above : List (Step R) → Fiber R → R → Prop where
  | leaf (x : R) : Above [] (.leaf x) x
  | pair {ss l r x z} (s : Step R) (hl : Above ss l x) (hr : Above ss r z)
      (h : (x-s.t)*(z-s.t) = s.B) :
      Above (ss ++ [s]) (.pair l r) (x-s.t+(z-s.t)+s.A)

theorem full_norm (f : Cubic R) {ss tree y} (h : Above ss tree y) :
    ev (ss.foldl descend f) y = product f tree := by
  induction h with
  | leaf => rfl
  | pair s _ _ h il ir =>
    simp only [List.foldl_append, List.foldl_cons, List.foldl_nil, product]
    rw [paired _ s _ _ h, il, ir]

/-- Slope of the chord to the two-torsion point (0,0) gives the paired abscissa. -/
theorem chord_pair {K : Type*} [Field K] (u y A B : K) (h : u ≠ 0)
    (curve : y^2 = u*(u^2+A*u+B)) : u*((y/u)^2-A-u) = B := by
  field_simp
  linear_combination curve

/-- The quotient image lies on Y² = X(X²-2AX+A²-4B). -/
theorem quotient_curve {K : Type*} [Field K] (u y A B : K) (hu : u ≠ 0)
    (curve : y^2 = u*(u^2+A*u+B)) :
    let X := u+A+B/u
    let Y := (y/u)*(u-B/u)
    Y^2 = X*(X^2-2*A*X+A^2-4*B) := by
  dsimp only
  have hx : (y/u)^2 = u+A+B/u := by
    field_simp
    linear_combination curve
  have hs : (u+A+B/u)^2-2*A*(u+A+B/u)+A^2-4*B = (u-B/u)^2 := by
    field_simp
    ring
  rw [mul_pow, hx, hs]

theorem projective_step (x v : R) (s : Step R) :
    let u := x*v
    let w := u-s.t*v
    w*w+s.A*(w*v)+s.B*v^2 =
      ((x-s.t)^2+s.A*(x-s.t)+s.B)*v^2 := by ring

abbrev F := ZMod 2147483647
def steps : List (Step F) :=
  [⟨0,0,1⟩,⟨2,6,8⟩,⟨262150,786438,3145792⟩,
   ⟨135006214,403445766,562160130⟩,⟨199756251,1939860868,1327400300⟩]

theorem final_cubic : steps.foldl descend (⟨1,0,2,14⟩ : Cubic F) =
    ⟨1330410815,368863965,1911999596,1606038711⟩ := by decide +kernel

theorem concrete_norm {tree terminal} (h : Above steps tree terminal) :
    product (⟨1,0,2,14⟩ : Cubic F) tree =
    ev ⟨1330410815,368863965,1911999596,1606038711⟩ terminal := by
  rw [← full_norm _ h, final_cubic]

theorem homogeneous (f : Cubic R) (x v : R) :
    ((f.a*(x*v)+f.b*v)*(x*v)^2 + f.c*(x*v)*v^2 + f.d*v^3)*v = ev f x*v^4 := by
  simp only [ev]; ring

private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

theorem projective_character (f : Cubic F) (x v : F) (hv : v ≠ 0) :
    quadraticChar F (((f.a*(x*v)+f.b*v)*(x*v)^2 + f.c*(x*v)*v^2 + f.d*v^3)*v) =
    quadraticChar F (ev f x) := by
  rw [homogeneous, map_mul, show v^4 = (v^2)^2 by ring,
    quadraticChar_sq_one' (pow_ne_zero 2 hv), mul_one]

end M31OrbitNorm
