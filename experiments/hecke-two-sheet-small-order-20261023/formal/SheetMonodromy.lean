module

public import Mathlib.Data.Bool.Basic

/-! A two-point fiber has only identity or swap monodromy. -/
namespace SheetMonodromy

public theorem bijection_bool_square (f : Bool → Bool)
    (hinj : ∀ x y : Bool, f x = f y → x = y) (b : Bool) : f (f b) = b := by
  have hneq : f false ≠ f true := by
    intro h
    have impossible : false = true := hinj false true h
    cases impossible
  cases h0 : f false <;> cases h1 : f true <;> cases b <;>
    simp_all

public theorem two_sheet_dichotomy (f : Bool → Bool)
    (hinj : ∀ x y : Bool, f x = f y → x = y) (b : Bool) :
    f b = b ∨ (f b ≠ b ∧ f (f b) = b) := by
  by_cases h : f b = b
  · exact Or.inl h
  · exact Or.inr ⟨h, bijection_bool_square f hinj b⟩

end SheetMonodromy

#print axioms SheetMonodromy.bijection_bool_square
#print axioms SheetMonodromy.two_sheet_dichotomy
