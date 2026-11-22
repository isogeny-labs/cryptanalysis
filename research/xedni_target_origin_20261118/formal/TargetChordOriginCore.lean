namespace XedniTargetChordOriginCore

/-- The kernel-level inversion step behind target-chord recovery. All
algebraic laws used by the proof are explicit hypotheses, so this declaration
can be audited with Lean core alone. -/
theorem recover_from_effective_coefficient
    {R : Type}
    (mul : R -> R -> R)
    (one target effective known inverse : R)
    (relation : mul effective target = known)
    (inverse_spec : mul inverse effective = one)
    (one_mul_target : mul one target = target)
    (mul_assoc_instance :
      mul (mul inverse effective) target = mul inverse (mul effective target)) :
    target = mul inverse known := by
  calc
    target = mul one target := one_mul_target.symm
    _ = mul (mul inverse effective) target := by rw [inverse_spec]
    _ = mul inverse (mul effective target) := mul_assoc_instance
    _ = mul inverse known := by rw [relation]

#print axioms recover_from_effective_coefficient

end XedniTargetChordOriginCore
