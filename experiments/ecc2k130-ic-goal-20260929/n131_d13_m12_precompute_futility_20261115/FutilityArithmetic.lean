import Init

/-! The arithmetic behind the prospective preparation-query decision rule. -/

theorem first_rank_check_needs_1098_productive_queries :
    4 * 1097 < 4390 ∧ 4390 ≤ 4 * 1098 := by
  decide

theorem prospective_zero_tail_below_five_percent :
    20 * (7094 : Nat) ^ 23 < (8192 : Nat) ^ 23 := by
  decide

#print axioms first_rank_check_needs_1098_productive_queries
#print axioms prospective_zero_tail_below_five_percent
