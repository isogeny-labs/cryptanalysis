import Std

namespace FinalRootSelector

/-- Guarded clauses for every valid selector value force the output pair
to equal the table entry selected by `s`. -/
theorem guarded_pair_iff_selected_row
    {n : Nat} {Code Root : Type}
    (codeTable : Fin n → Code) (rootTable : Fin n → Root)
    (s : Fin n) (code : Code) (root : Root) :
    (∀ i : Fin n, s ≠ i ∨
      (code = codeTable i ∧ root = rootTable i)) ↔
    code = codeTable s ∧ root = rootTable s := by
  classical
  constructor
  · intro h
    exact (h s).resolve_left (by simp)
  · intro h i
    by_cases hi : s = i
    · right
      simpa [← hi] using h
    · exact Or.inl hi

/-- Every table row has a satisfying selector assignment. -/
theorem every_row_has_selector
    {n : Nat} {Code Root : Type}
    (codeTable : Fin n → Code) (rootTable : Fin n → Root)
    (i : Fin n) :
    ∃ s : Fin n,
      s = i ∧
      (∀ j : Fin n, s ≠ j ∨
        (codeTable i = codeTable j ∧ rootTable i = rootTable j)) := by
  classical
  refine ⟨i,rfl,?_⟩
  exact (guarded_pair_iff_selected_row codeTable rootTable i
    (codeTable i) (rootTable i)).mpr ⟨rfl,rfl⟩

/-- Nominal clause count for a 30-bit signed-state selector with 28 code
and 131 field-output bits per selected row. This is an arithmetic
projection; it does not assert that every nominal source state is usable. -/
theorem nominal_n131_guard_count :
    (2 : Nat)^30 * (28 + 131) = 170724950016 := by
  decide

#print axioms FinalRootSelector.guarded_pair_iff_selected_row
#print axioms FinalRootSelector.every_row_has_selector
#print axioms FinalRootSelector.nominal_n131_guard_count

end FinalRootSelector
