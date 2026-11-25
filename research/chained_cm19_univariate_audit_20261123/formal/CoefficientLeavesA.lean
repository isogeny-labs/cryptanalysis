import Init

/- Concrete integer and mod-seven coefficient leaves only. These definitions
   do not instantiate an actual elliptic curve, field quotient or Jacobian.
   Their semantic bridges and the full geometric theorem remain open. -/
namespace ChainedCM19.CoefficientLeavesA

structure Coeff where
  constant : Int
  omega : Int
  deriving DecidableEq

def c (a b : Int) : Coeff := ⟨a, b⟩
def plus (a b : Coeff) : Coeff :=
  c (a.constant + b.constant) (a.omega + b.omega)
def times (a b : Coeff) : Coeff :=
  c (a.constant * b.constant - 5 * a.omega * b.omega)
    (a.constant * b.omega + a.omega * b.constant + a.omega * b.omega)
def bar (a : Coeff) : Coeff := c (a.constant + a.omega) (-a.omega)

structure Vec3 where
  x : Coeff
  y : Coeff
  z : Coeff
  deriving DecidableEq
structure Mat3 where
  r0 : Vec3
  r1 : Vec3
  r2 : Vec3
  deriving DecidableEq
def dot (a b : Vec3) : Coeff :=
  plus (plus (times a.x b.x) (times a.y b.y)) (times a.z b.z)
def matVec (a : Mat3) (v : Vec3) : Vec3 :=
  ⟨dot a.r0 v, dot a.r1 v, dot a.r2 v⟩
def transpose (a : Mat3) : Mat3 :=
  ⟨⟨a.r0.x, a.r1.x, a.r2.x⟩,
    ⟨a.r0.y, a.r1.y, a.r2.y⟩,
    ⟨a.r0.z, a.r1.z, a.r2.z⟩⟩
def row (v : Vec3) (a : Mat3) : Vec3 := matVec (transpose a) v
def barVec (v : Vec3) : Vec3 := ⟨bar v.x, bar v.y, bar v.z⟩
def dagger (a : Mat3) : Mat3 :=
  let t := transpose a
  ⟨barVec t.r0, barVec t.r1, barVec t.r2⟩

def s : Mat3 :=
  ⟨⟨c (-4) 0, c (-2) 0, c 2 0⟩,
    ⟨c 2 2, c (-1) 2, c (-1) (-2)⟩,
    ⟨c (-4) 2, c (-3) 1, c 3 (-1)⟩⟩
def hInv : Mat3 :=
  ⟨⟨c 2 0, c (-2) 1, c 1 1⟩,
    ⟨c (-1) (-1), c 5 0, c 3 (-2)⟩,
    ⟨c 2 (-1), c 1 2, c 5 0⟩⟩
def n : Mat3 :=
  ⟨⟨c 0 0, c (-1) 0, c 1 0⟩,
    ⟨c 3 0, c 1 0, c (-1) 0⟩,
    ⟨c 0 0, c (-2) 1, c (-1) (-1)⟩⟩
def v : Vec3 := ⟨c 1 0, c (-1) (-1), c 2 (-1)⟩
def u : Vec3 := ⟨c 2 0, c 1 (-2), c 5 (-1)⟩
def ell : Vec3 := ⟨c 0 1, c 1 0, c 0 0⟩

theorem splitColumn : matVec s v = u := by decide
theorem leftInverseCoefficients : dot ell u = c 1 0 := by decide
theorem inverseGramRow :
    row ell hInv = ⟨c (-1) 1, c 0 (-1), c (-2) 0⟩ := by decide
theorem normFourCoefficients : dot (row ell hInv) (barVec ell) = c 4 0 := by decide
theorem pushforwardNumeratorCoefficients :
    row (row ell hInv) (dagger n) = ⟨c (-2) 1, c (-1) 2, c (-1) 0⟩ := by decide

def coefficient (p : List Nat) (i : Nat) : Nat := (p[i]?).getD 0
def multiply7 (a b : List Nat) : List Nat :=
  (List.range (a.length + b.length - 1)).map fun k =>
    (List.range a.length).foldl (fun total i =>
      (total + if i ≤ k then coefficient a i * coefficient b (k-i) else 0) % 7) 0
def scale7 (n : Nat) (a : List Nat) : List Nat := a.map fun x => n*x % 7
def plus7 (a b : List Nat) : List Nat :=
  (List.range (max a.length b.length)).map fun i => (coefficient a i + coefficient b i) % 7
def minus7 (a b : List Nat) : List Nat :=
  (List.range (max a.length b.length)).map fun i => (coefficient a i + 7 - coefficient b i) % 7
def modulus : List Nat := [3,6,3,5,2,0,1]
def numerator : List Nat := [6,4,0,1]
def denominator : List Nat := [5,0,3]
def inverseDenominator : List Nat := [1,3,3,0,2]

theorem normPolynomialCoefficients :
    minus7 (multiply7 numerator numerator) (scale7 3 (multiply7 denominator denominator)) = modulus := by decide
theorem denominatorInverseCoefficients :
    multiply7 denominator inverseDenominator = plus7 [1] (scale7 6 modulus) := by decide

#print axioms splitColumn
#print axioms leftInverseCoefficients
#print axioms inverseGramRow
#print axioms normFourCoefficients
#print axioms pushforwardNumeratorCoefficients
#print axioms normPolynomialCoefficients
#print axioms denominatorInverseCoefficients

end ChainedCM19.CoefficientLeavesA
