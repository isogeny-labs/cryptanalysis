import Std

namespace M31PublicEquations

abbrev p := 2147483647
abbrev Point := Option (Nat × Nat)

def power (x e : Nat) : Nat := Id.run do
  let mut acc := 1
  let mut v := x
  for i in [:31] do
    if e.testBit i then acc := acc*v%p
    v := v*v%p
  return acc

def neg : Point → Point := Option.map fun (x,y) => (x,(p-y)%p)

-- Both M31 panel curves have linear coefficient 2.
def add : Point → Point → Point
  | none, q => q
  | q, none => q
  | some (x,y), some (u,v) =>
    if x == u && (y+v)%p == 0 then none else
    let (num,den) := if x == u then (3*x*x+2,2*y) else (v+p-y,u+p-x)
    let slope := num * power den (p-2) % p
    let z := (slope*slope + 2*p-x-u)%p
    some (z,(slope*(x+p-z) + p-y)%p)

def mul (q : Point) (k : Nat) : Point := Id.run do
  let mut r := none
  let mut v := q
  for i in [:32] do
    if k.testBit i then r := add r v
    v := add v v
  return r

def onCurve (b : Nat) (q : Point) : Bool :=
  q.any fun (x,y) => x < p && y < p && y*y%p == (x*x*x+2*x+b)%p

def publicEquation (b n : Nat) (g q : Point) (k : Nat) : Bool :=
  n < 2^32 && k < n && onCurve b g && onCurve b q && mul g k == q

def rowEquation (g q : Point) (base : Array (Nat × Nat))
    (a b i j : Nat) (si sj : Int) : Bool := Id.run do
  let some u := base[i]? | return false
  let some v := base[j]? | return false
  if !(a < 2147505293 && b < 2147505293 && (si == 1 || si == -1) &&
      (sj == 1 || sj == -1) && onCurve 14 (some u) && onCurve 14 (some v)) then return false
  return add (mul g a) (mul q b) ==
    add (if si == 1 then some u else neg (some u)) (if sj == 1 then some v else neg (some v))

end M31PublicEquations
