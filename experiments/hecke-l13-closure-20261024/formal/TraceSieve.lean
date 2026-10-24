module

public import Init

/-! The finite arithmetic part of the degree-13 scalar-Frobenius trace sieve. -/
namespace TraceSieve

public theorem square_roots_three_mod_thirteen :
    ∀ s : Fin 13,
      (s.val * s.val) % 13 = 3 ↔ s.val = 4 ∨ s.val = 9 := by
  decide

public theorem scalar_trace_residue :
    ∀ s : Fin 13,
      (s.val * s.val) % 13 = 3 →
      (2 * s.val) % 13 = 5 ∨ (2 * s.val) % 13 = 8 := by
  decide

end TraceSieve

#print axioms TraceSieve.square_roots_three_mod_thirteen
#print axioms TraceSieve.scalar_trace_residue
