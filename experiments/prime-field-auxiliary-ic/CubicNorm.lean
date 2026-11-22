import Std
/-! A cubic is closed under taking the product over the two children of an
auxiliary rational map. With known maps and terminal, one four-coefficient
update per stage computes the product over an entire paired fiber. -/
namespace CubicNorm
open Lean.Grind
structure Cubic (F : Type) where
  a : F
  b : F
  c : F
  d : F

variable {F : Type} [CommRing F]
def eval (h : Cubic F) (x : F) := ((h.a*x+h.b)*x+h.c)*x+h.d

def shift (h : Cubic F) (r : F) : Cubic F :=
  ⟨h.a, 3*h.a*r+h.b, (3*h.a*r+2*h.b)*r+h.c, eval h r⟩

theorem shift_eval (h : Cubic F) (r x : F) : eval (shift h r) x = eval h (r+x) := by
  simp only [shift, eval]
  grind

def productCubic (h : Cubic F) (B : F) : Cubic F :=
  let a := h.a; let b := h.b; let c := h.c; let d := h.d
  ⟨a*d, a*c*B+b*d, a*b*B*B+b*c*B+c*d-3*a*d*B,
   a*a*B*B*B+b*b*B*B+c*c*B+d*d-2*a*c*B*B-2*b*d*B⟩

theorem product_eval (h : Cubic F) (u v B : F) (pair : u*v=B) :
    eval (productCubic h B) (u+v) = eval h u * eval h v := by
  subst B
  simp only [productCubic,eval]
  grind

structure MapData (F : Type) where
  pole : F
  offset : F
  residue : F

def push (h : Cubic F) (m : MapData F) :=
  shift (productCubic (shift h m.pole) m.residue) (-m.offset)

theorem push_eval (h : Cubic F) (m : MapData F) (x y : F)
    (pair : (x-m.pole)*(y-m.pole)=m.residue) :
    eval (push h m) ((x-m.pole)+(y-m.pole)+m.offset) = eval h x * eval h y := by
  unfold push
  rw [shift_eval]
  have a : -m.offset+((x-m.pole)+(y-m.pole)+m.offset) = (x-m.pole)+(y-m.pole) := by grind
  rw [a,product_eval _ _ _ _ pair,shift_eval,shift_eval]
  congr 2 <;> grind

#print axioms push_eval
/-- Maps are listed outermost first; coefficients propagate from leaves to root. -/
def through (h : Cubic F) : List (MapData F) → Cubic F
| [] => h
| m :: ms => push (through h ms) m

def leafProduct (h : Cubic F) : List F → F
| [] => 1
| x :: xs => eval h x * leafProduct h xs

theorem leafProduct_append (h : Cubic F) (xs ys : List F) :
    leafProduct h (xs++ys) = leafProduct h xs * leafProduct h ys := by
  induction xs with
  | nil => simp only [List.nil_append,leafProduct]; grind
  | cons x xs ih => simp only [List.cons_append,leafProduct,ih]; grind

inductive Paired : List (MapData F) → F → List F → Prop
| leaf (x : F) : Paired [] x [x]
| branch {ms l r xs ys} (m : MapData F) : Paired ms l xs → Paired ms r ys →
    (l-m.pole)*(r-m.pole)=m.residue →
    Paired (m::ms) ((l-m.pole)+(r-m.pole)+m.offset) (xs++ys)

theorem wholeProduct (h : Cubic F) {ms z xs} (tree : Paired ms z xs) :
    eval (through h ms) z = leafProduct h xs := by
  induction tree with
  | leaf x => simp only [through,leafProduct]; grind
  | branch m tl tr hp il ir =>
    simp only [through,push_eval _ _ _ _ hp,leafProduct_append,il,ir]

#print axioms wholeProduct
def scale (t : F) (h : Cubic F) : Cubic F :=
  ⟨t*h.a,t*h.b,t*h.c,t*h.d⟩

private theorem shift_scale (t : F) (h : Cubic F) (r : F) :
    shift (scale t h) r = scale t (shift h r) := by
  unfold shift scale eval
  congr 1 <;> grind

private theorem product_scale (t : F) (h : Cubic F) (b : F) :
    productCubic (scale t h) b = scale (t*t) (productCubic h b) := by
  simp only [productCubic, scale, Cubic.mk.injEq]
  exact ⟨by grind, by grind, by grind, by grind⟩

theorem push_scale (t : F) (h : Cubic F) (m : MapData F) :
    push (scale t h) m = scale (t*t) (push h m) := by
  simp only [push,shift_scale,product_scale]

/-- A nonempty norm chain loses the global sign already at its first pair. -/
theorem through_neg (h : Cubic F) (m : MapData F) (ms : List (MapData F)) :
    through (scale (-1) h) (m::ms) = through h (m::ms) := by
  induction ms generalizing m with
  | nil =>
    simp only [through,push_scale]
    have unit : (-1:F)*(-1)=1 := by grind
    rw [unit]
    generalize push h m = a
    cases a
    unfold scale
    congr 1 <;> grind
  | cons n ns ih =>
    change push (through (scale (-1) h) (n::ns)) m = push (through h (n::ns)) m
    rw [ih n]

#print axioms push_scale
#print axioms through_neg
/-- Add the two child values of a cubic, using their known coordinate
product to express the sum in the parent coordinate. -/
def traceStep (h : Cubic F) (m : MapData F) : Cubic F :=
  let q := shift h m.pole
  shift ⟨q.a, q.b, q.c-3*q.a*m.residue, 2*q.d-2*q.b*m.residue⟩ (-m.offset)

theorem traceStep_eval (h : Cubic F) (m : MapData F) (x y : F)
    (pair : (x-m.pole)*(y-m.pole)=m.residue) :
    eval (traceStep h m) ((x-m.pole)+(y-m.pole)+m.offset) = eval h x + eval h y := by
  unfold traceStep
  rw [shift_eval]
  simp only [shift, eval]
  grind

def traceThrough (h : Cubic F) : List (MapData F) → Cubic F
| [] => h
| m :: ms => traceStep (traceThrough h ms) m

def leafSum (h : Cubic F) : List F → F
| [] => 0
| x :: xs => eval h x + leafSum h xs

private theorem leafSum_append (h : Cubic F) (xs ys : List F) :
    leafSum h (xs++ys) = leafSum h xs + leafSum h ys := by
  induction xs with
  | nil => simp only [List.nil_append,leafSum]; grind
  | cons x xs ih => simp only [List.cons_append,leafSum,ih]; grind

theorem wholeSum (h : Cubic F) {ms z xs} (tree : Paired ms z xs) :
    eval (traceThrough h ms) z = leafSum h xs := by
  induction tree with
  | leaf x => simp only [traceThrough,leafSum]; grind
  | branch m tl tr hp il ir =>
    simp only [traceThrough,traceStep_eval _ _ _ _ hp,leafSum_append,il,ir]

theorem leafSum_scale (k : F) (h : Cubic F) (xs : List F) :
    leafSum (scale k h) xs = k * leafSum h xs := by
  induction xs with
  | nil => simp only [leafSum]; grind
  | cons x xs ih =>
    change eval (scale k h) x + leafSum (scale k h) xs = k * (eval h x + leafSum h xs)
    rw [ih]
    simp only [eval,scale]
    grind

theorem trace_scale_at_terminal (k : F) (h : Cubic F) {ms z xs}
    (tree : Paired ms z xs) :
    eval (traceThrough (scale k h) ms) z = k * eval (traceThrough h ms) z := by
  rw [wholeSum _ tree, wholeSum _ tree, leafSum_scale]

#print axioms trace_scale_at_terminal
#print axioms wholeSum
end CubicNorm
