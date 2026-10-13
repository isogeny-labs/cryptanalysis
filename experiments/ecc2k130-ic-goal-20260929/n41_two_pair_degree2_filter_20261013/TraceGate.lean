import Std

/-! Conditional algebraic bridge for the exact N41 trace filter gate.
Concrete curve doubling, field trace, and subgroup divisibility are checked
outside Lean and remain explicit hypotheses here. -/
namespace TraceGate

universe u v
variable {G : Type u} {F : Type v} [Add G] [Add F]

theorem trace_artin_schreier
    (square : F → F) (trace : F → Bool)
    (trace_add : ∀ a b, trace (a + b) = Bool.xor (trace a) (trace b))
    (trace_square : ∀ a, trace (square a) = trace a)
    (a : F) : trace (square a + a) = false := by
  rw [trace_add, trace_square]
  cases trace a <;> rfl

theorem subgroup_x_trace_zero
    (x : G → F) (slope : G → F) (square : F → F) (trace : F → Bool)
    (double_surjective : ∀ p : G, ∃ q : G, p = q + q)
    (double_x : ∀ q : G, x (q + q) = square (slope q) + slope q)
    (trace_add : ∀ a b, trace (a + b) = Bool.xor (trace a) (trace b))
    (trace_square : ∀ a, trace (square a) = trace a)
    (p : G) : trace (x p) = false := by
  obtain ⟨q, hp⟩ := double_surjective p
  rw [hp, double_x]
  exact trace_artin_schreier square trace trace_add trace_square (slope q)

#print axioms TraceGate.trace_artin_schreier
#print axioms TraceGate.subgroup_x_trace_zero

end TraceGate
