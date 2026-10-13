import Std
set_option maxRecDepth 8192
set_option maxHeartbeats 0

/-! Coefficient certificate for the characteristic-two quadratic resultant.
    Variables A,B,C,D,E,F,z are independent; all exponent digits fit base 5.
    This makes the common-root argument independent of the S3 coefficients. -/
namespace S4Bezout

abbrev Mon := Nat × Nat × Nat × Nat × Nat × Nat × Nat
abbrev Poly := List Mon

def var (position : Nat) : Poly :=
  [((if position == 0 then 1 else 0),
    (if position == 1 then 1 else 0),
    (if position == 2 then 1 else 0),
    (if position == 3 then 1 else 0),
    (if position == 4 then 1 else 0),
    (if position == 5 then 1 else 0),
    (if position == 6 then 1 else 0))]
def add (p q : Poly) : Poly := p ++ q
def monMul (x y : Mon) : Mon :=
  (x.1+y.1, x.2.1+y.2.1, x.2.2.1+y.2.2.1,
   x.2.2.2.1+y.2.2.2.1, x.2.2.2.2.1+y.2.2.2.2.1,
   x.2.2.2.2.2.1+y.2.2.2.2.2.1,
   x.2.2.2.2.2.2+y.2.2.2.2.2.2)
def mul (p q : Poly) : Poly := p.flatMap (fun x => q.map (monMul x))
def sq (p : Poly) : Poly := mul p p
def encode (m : Mon) : Nat :=
  1 <<< (m.1 + 5*m.2.1 + 25*m.2.2.1 + 125*m.2.2.2.1 +
         625*m.2.2.2.2.1 + 3125*m.2.2.2.2.2.1 +
         15625*m.2.2.2.2.2.2)
def normalForm (p : Poly) : Nat := p.foldl (fun acc m => Nat.xor acc (encode m)) 0

def A : Poly := var 0
def B : Poly := var 1
def C : Poly := var 2
def D : Poly := var 3
def E : Poly := var 4
def F : Poly := var 5
def z : Poly := var 6
def f : Poly := add (add (mul A (sq z)) (mul B z)) C
def g : Poly := add (add (mul D (sq z)) (mul E z)) F
def U : Poly := add (mul A F) (mul D C)
def V : Poly := add (mul A E) (mul D B)
def W : Poly := add (mul B F) (mul E C)
def resultant : Poly := add (sq U) (mul V W)
def bezout : Poly :=
  add (sq (add (mul D f) (mul A g)))
      (mul V (add (mul E f) (mul B g)))

theorem bezout_equals_resultant : normalForm bezout = normalForm resultant := by
  decide

#print axioms S4Bezout.bezout_equals_resultant
end S4Bezout
