import Std
set_option maxRecDepth 8192
set_option maxHeartbeats 0

/-! A coefficient-level characteristic-two certificate for the S4 identity.
    Polynomials are lists of monomials; `normalForm` XORs coefficients with
    the same exponent vector. The field-level interpretation is documented
    in PROOF_MAP.md. -/
namespace FiveMulIdentity

abbrev Mon := Nat × Nat × Nat × Nat
abbrev Poly := List Mon

def one : Poly := [(0, 0, 0, 0)]
def a : Poly := [(1, 0, 0, 0)]
def b : Poly := [(0, 1, 0, 0)]
def c : Poly := [(0, 0, 1, 0)]
def t : Poly := [(0, 0, 0, 1)]
def add (p q : Poly) : Poly := p ++ q
def monMul (x y : Mon) : Mon :=
  (x.1 + y.1, x.2.1 + y.2.1, x.2.2.1 + y.2.2.1, x.2.2.2 + y.2.2.2)
def mul (p q : Poly) : Poly := p.flatMap (fun x => q.map (monMul x))
def sq (p : Poly) : Poly := mul p p
def encode (m : Mon) : Nat :=
  1 <<< (m.1 + 8*m.2.1 + 64*m.2.2.1 + 512*m.2.2.2)
def normalForm (p : Poly) : Nat := p.foldl (fun acc m => Nat.xor acc (encode m)) 0

def A : Poly := add one (sq (mul a b))
def B : Poly := mul a b
def C : Poly := add (sq a) (sq b)
def D : Poly := add one (sq (mul c t))
def E : Poly := mul c t
def F : Poly := add (sq c) (sq t)
def resultant : Poly :=
  add (sq (add (mul A F) (mul D C)))
      (mul (add (mul A E) (mul D B))
           (add (mul B F) (mul E C)))

def e1 : Poly := add (add a b) (add c t)
def e3 : Poly := add (mul (mul a b) (add c t))
                     (mul (mul c t) (add a b))
def e4 : Poly := mul (mul a b) (mul c t)
def symmetric : Poly :=
  let x := sq e1
  let y := sq e3
  let z := e4
  add (add (sq y) (sq x))
      (add y (mul z (add (add x y) (mul x z))))

theorem resultant_eq_symmetric : normalForm resultant = normalForm symmetric := by
  decide

#print axioms FiveMulIdentity.resultant_eq_symmetric
def optimizedE3 : Poly :=
  add (mul (mul a b) c)
      (mul t (add (mul c (add a b)) (mul a b)))
def optimizedE4 : Poly := mul t (mul (mul a b) c)
def optimized : Poly :=
  let x := sq e1
  let y := sq optimizedE3
  let z := optimizedE4
  add (add (sq y) (sq x))
      (add y (mul z (add (add x y) (mul x z))))

theorem optimized_eq_symmetric : normalForm optimized = normalForm symmetric := by
  decide

#print axioms FiveMulIdentity.optimized_eq_symmetric
end FiveMulIdentity
