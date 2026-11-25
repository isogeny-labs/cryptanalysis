/- Exact Boolean clauses used by the shared monomial gates. -/
theorem and_gate_iff (v a b : Bool) :
    ((!v || a) && (!v || b) && (v || !a || !b) = true) ↔
      (v = (a && b)) := by
  cases v <;> cases a <;> cases b <;> decide

theorem xor_row_flip (x tail rhs : Bool) :
    ((if rhs then x else !x) ^^ tail = true) ↔
      (x ^^ tail = rhs) := by
  cases x <;> cases tail <;> cases rhs <;> decide

#print axioms and_gate_iff
#print axioms xor_row_flip
