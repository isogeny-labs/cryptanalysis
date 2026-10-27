module

public import Init

/-! Rational y-roots and the selected multiplicity-two pair at x = 4
on y² + y = x³ - x² - 10x - 20 over F₈₃. -/
namespace RepeatedRoot

set_option maxRecDepth 4096

public def onCurveAt4 (y : Nat) : Bool :=
  (y * y + y) % 83 == 71

public theorem rational_y_roots : ∀ y : Fin 83,
    onCurveAt4 y.val = true ↔ y.val = 38 ∨ y.val = 44 := by
  decide

public theorem unique_unordered_pair : ∀ a b : Fin 83,
    a.val ≤ b.val → onCurveAt4 a.val = true → onCurveAt4 b.val = true →
      (a.val + b.val) % 83 = 82 → a.val = 38 ∧ b.val = 44 := by
  decide

#print axioms rational_y_roots
#print axioms unique_unordered_pair

end RepeatedRoot
