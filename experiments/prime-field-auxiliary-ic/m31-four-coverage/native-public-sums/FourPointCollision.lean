import Mathlib.Tactic
import Mathlib.Data.ZMod.Basic

namespace FourPointCollision

/-- Differences of the two aligned row descriptions for the three partitions. -/
theorem residuals {G : Type*} [AddCommGroup G] (a b c d : G) :
    (c-a)-(d+b) = -((b+a)+(d-c)) ∧
    (c-b)-(d+a) = -((b+a)+(d-c)) := by
  constructor <;> abel

abbrev F := ZMod 2147483647
abbrev Point := F × F

def opposite (u : Point) : Point := (u.1, -u.2)

def onCurve (u : Point) : Prop := u.2^2 = u.1^3 + 2*u.1 + 14

/-- A nonvertical affine chord, certified without modular division. -/
def chord (u v w : Point) (s : F) : Prop :=
  u.1 ≠ v.1 ∧ s * (v.1-u.1) = v.2-u.2 ∧
    w.1 = s*s-u.1-v.1 ∧ w.2 = s*(u.1-w.1)-u.2

def p1 : Point := (963143994, 80740545)
def p22 : Point := (227180665, 71088508)
def p23 : Point := (1546047035, 480262751)
def p27 : Point := (996167626, 515266363)
def sum0 : Point := (1291788543, 588780956)
def sum1 : Point := (1463870740, 50953559)
def sum2 : Point := (932656382, 1794652635)

theorem fixture :
    onCurve p1 ∧
    onCurve p22 ∧
    onCurve p23 ∧
    onCurve p27 ∧
    chord p22 p1 sum0 1744292787 ∧
    chord p27 (opposite p23) (opposite sum0) 179467424 ∧
    chord p23 (opposite p1) sum1 348487795 ∧
    chord p27 p22 sum1 124764359 ∧
    chord p23 (opposite p22) sum2 1910657891 ∧
    chord p27 p1 sum2 1686934455 := by
  unfold onCurve chord
  decide +kernel

#print axioms fixture
#print axioms residuals
end FourPointCollision
