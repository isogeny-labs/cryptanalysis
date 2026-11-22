import Std

namespace FiberCollision

def p : Nat := 2147483647
def roots := [3, 1393679185, 1431655765, 753804470]
def eval (a b c d x : Nat) := (((a*x+b)*x+c)*x+d) % p
def cubicA := eval 1545733438 193392777 697360912 1677219680
def cubicB := eval 683797012 1367500483 845922299 1051947785

/-- Siblings for the map x ↦ x + B/x away from zero. -/
def siblings (x y B z : Nat) := x*y % p = B ∧ (x+y) % p = z

theorem sameFiber :
    siblings 3 1431655765 1 1431655768 ∧
    siblings 1393679185 753804470 1 8 ∧
    siblings 1431655768 8 715827909 1431655776 := by unfold siblings; decide

theorem values : roots.map cubicA = [1,1,6,6] ∧ roots.map cubicB = [1,2,2,9] := by decide

def disc (a b c d : Int) :=
  (b^2*c^2-4*a*c^3-4*b^3*d-27*a^2*d^2+18*a*b*c*d) % (p : Int)

theorem discriminants :
    disc 1545733438 193392777 697360912 1677219680 = 84431450 ∧
    disc 683797012 1367500483 845922299 1051947785 = 1275157021 := by decide

/-- Compute x^(2^n - 1) modulo p without constructing the full power. -/
def ladder (x : Nat) : Nat → Nat
  | 0 => 1
  | n+1 => let t := ladder x n; (t*t*(x%p))%p

theorem ladder_spec (x n : Nat) : ladder x n = x^(2^n-1) % p := by
  induction n with
  | zero => simp [ladder,p]
  | succ n ih =>
    have h : 0 < 2^n := Nat.two_pow_pos n
    have e : 2^(n+1)-1 = (2^n-1)+(2^n-1)+1 := by rw [Nat.pow_succ]; omega
    rw [ladder, ih, e, Nat.pow_succ, Nat.pow_add]
    simp [Nat.mul_mod]

def aggregates (xs : List Nat) := (xs.sum % p, xs.prod % p)
def countEulerOne (xs : List Nat) := (xs.filter fun x => ladder x 30 == 1).length

theorem collision :
    aggregates (roots.map cubicA) = (14,36) ∧ aggregates (roots.map cubicB) = (14,36) ∧
    countEulerOne (roots.map cubicA) = 2 ∧ countEulerOne (roots.map cubicB) = 4 := by
  rw [values.1, values.2]
  decide

/-- Any decoder of the two terminal residues alone fails on one of these cubics. -/
theorem noDecoder (f : Nat × Nat → Nat) :
    ¬ (f (aggregates (roots.map cubicA)) = countEulerOne (roots.map cubicA) ∧
       f (aggregates (roots.map cubicB)) = countEulerOne (roots.map cubicB)) := by
  obtain ⟨a,b,c,d⟩ := collision
  rw [a,b,c,d]
  omega

theorem eulerExponent : 2^30-1 = (p-1)/2 := by decide

#print axioms noDecoder
#print axioms collision
#print axioms ladder_spec
end FiberCollision
