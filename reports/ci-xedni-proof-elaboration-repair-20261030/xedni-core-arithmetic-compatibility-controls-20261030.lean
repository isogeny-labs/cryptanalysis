import Init
namespace XedniCoreCompatibility
 theorem constant_bound (i : Fin 1) : ((fun _ : Fin 1 => (1 : Int)) i).natAbs ≤ 1 := by
  change (1 : Int).natAbs ≤ 1
  decide
 theorem successor_nonzero (bound : Nat) : ((bound + 1 : Nat) : Int) ≠ 0 := by
  exact Int.ofNat_ne_zero.mpr (Nat.succ_ne_zero bound)
 theorem bound_contradiction (bound : Nat)
   (h : ∀ i : Fin 1, ((fun _ : Fin 1 => ((bound + 1 : Nat) : Int)) i).natAbs ≤ bound) : False := by
  have bad := h (0 : Fin 1)
  change bound + 1 ≤ bound at bad
  exact Nat.not_succ_le_self bound bad
#print axioms constant_bound
#print axioms successor_nonzero
#print axioms bound_contradiction
end XedniCoreCompatibility
