import Std

/-! The bit order matches `rank_extended.py`: all linear coordinates, followed
by squarefree pairs `(i,j)` in increasing `i`, then increasing `j`. -/
namespace QuadraticFeature

def packBits : List Nat → Nat
  | [] => 0
  | bit :: bits => bit + 2 * packBits bits

def pairBits (n x : Nat) : List Nat :=
  (List.range n).flatMap fun i =>
    ((List.range n).filter (fun j => i < j)).map fun j =>
      if x.testBit i && x.testBit j then 1 else 0

def quadraticTail (n x : Nat) : Nat := packBits (pairBits n x)

def feature (n x : Nat) : Nat := x + 2^n * quadraticTail n x

theorem feature_mod (n x : Nat) (hx : x < 2^n) :
    feature n x % 2^n = x := by
  unfold feature
  simp [Nat.add_mod, Nat.mod_eq_of_lt hx]

theorem feature_injective_on (n x y : Nat)
    (hx : x < 2^n) (hy : y < 2^n)
    (h : feature n x = feature n y) : x = y := by
  have hmod := congrArg (fun value : Nat => value % 2^n) h
  simpa [feature_mod n x hx, feature_mod n y hy] using hmod

#eval feature 4 11 -- 347: linear bits 1011, pair bits at positions 0,2,4.
#print axioms feature_mod
#print axioms feature_injective_on

end QuadraticFeature
