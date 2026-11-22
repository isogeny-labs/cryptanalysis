import Std
import Init.Grind.Ring.Basic

namespace SignNorm
open Lean.Grind

theorem factor_nonzero_of_product_nonzero {F : Type}
    [Field F] (xs : List F) (hprod : xs.prod ≠ 0) :
    ∀ x ∈ xs, x ≠ 0 := by
  induction xs with
  | nil =>
      intro x hx
      simp at hx
  | cons a rest ih =>
      have ha : a ≠ 0 := by
        intro hz
        apply hprod
        grind
      have hrest : rest.prod ≠ 0 := by
        intro hz
        apply hprod
        grind
      intro x hx
      simp only [List.mem_cons] at hx
      rcases hx with rfl | htail
      · exact ha
      · exact ih hrest x htail

/-- A nonzero functional value on a sign product excludes every sign factor. -/
theorem trace_norm_excludes_each_sign {F : Type}
    [Field F] (L : F → Bool) (hzero : L 0 = false)
    (values : List F) (hcert : L values.prod = true) :
    ∀ value ∈ values, value ≠ 0 := by
  have hprod : values.prod ≠ 0 := by
    intro hz
    rw [hz, hzero] at hcert
    cases hcert
  exact factor_nonzero_of_product_nonzero values hprod

/-- One norm certificate for each code tuple excludes every sign in every tuple. -/
theorem trace_norm_excludes_box {F : Type}
    [Field F] (L : F → Bool) (hzero : L 0 = false)
    (rows : List (List F))
    (hcert : ∀ row ∈ rows, L row.prod = true) :
    ∀ row ∈ rows, ∀ value ∈ row, value ≠ 0 := by
  intro row hrow
  exact trace_norm_excludes_each_sign L hzero row (hcert row hrow)

#print axioms factor_nonzero_of_product_nonzero
#print axioms trace_norm_excludes_each_sign
#print axioms trace_norm_excludes_box
end SignNorm
