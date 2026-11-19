import Mathlib.Tactic

/-!
A valid adaptive public-point relation with a nonzero target coefficient
contains a discrete-log certificate. The statements work in any module over
the prime field `ZMod q`; an order-`q` elliptic-curve subgroup is the intended
instance. The results concern the algebraic output of a relation procedure,
without assuming an algorithm for finding such an output.
-/

namespace XedniAdaptivePublicRelationReduction

universe u

variable (q : ℕ) [Fact (Nat.Prime q)]
variable {G : Type u} [AddCommGroup G] [Module (ZMod q) G]

/-- A public relation gives a scalar that reproduces the target point. -/
theorem relation_certificate_verifies (P Q : G) (a b : ZMod q) (hb : b ≠ 0)
    (hrel : a • P + b • Q = 0) :
    (-a / b) • P = Q := by
  have h := congrArg (fun X : G => b⁻¹ • X) hrel
  have hsum : (b⁻¹ * a) • P + Q = 0 := by
    simpa [smul_add, smul_smul, inv_mul_cancel₀ hb, mul_comm] using h
  have hQ : Q = -((b⁻¹ * a) • P) := eq_neg_of_add_eq_zero_right hsum
  calc
    (-a / b) • P = (-(b⁻¹ * a)) • P := by
      congr 1
      field_simp
    _ = -((b⁻¹ * a) • P) := neg_smul _ _
    _ = Q := hQ.symm

/-- For a nonzero base point, the same certificate recovers the unique
target scalar. -/
theorem relation_certificate_recovers (P : G) (hP : P ≠ 0)
    (v a b : ZMod q) (hb : b ≠ 0)
    (hrel : a • P + b • (v • P) = 0) :
    v = -a / b := by
  have hsmul : (a + b * v) • P = 0 := by
    simpa [add_smul, mul_smul] using hrel
  have hcoef : a + b * v = 0 := (smul_eq_zero.mp hsmul).resolve_right hP
  apply (eq_div_iff hb).2
  linear_combination hcoef

/-- A known scalar supplies a relation with a unit target coefficient. -/
theorem known_scalar_gives_relation (P : G) (v : ZMod q) :
    (-v) • P + (1 : ZMod q) • (v • P) = 0 := by
  simp

/-- The existence of a nonzero-target-coefficient public relation is
equivalent to target membership in the one-dimensional span of the base. -/
theorem relation_certificate_iff_span (P Q : G) :
    (∃ a b : ZMod q, b ≠ 0 ∧ a • P + b • Q = 0) ↔
      ∃ v : ZMod q, Q = v • P := by
  constructor
  · rintro ⟨a, b, hb, hrel⟩
    exact ⟨-a / b, (relation_certificate_verifies q P Q a b hb hrel).symm⟩
  · rintro ⟨v, hv⟩
    refine ⟨-v, 1, one_ne_zero, ?_⟩
    rw [hv]
    exact known_scalar_gives_relation q P v

#print axioms relation_certificate_verifies
#print axioms relation_certificate_recovers
#print axioms known_scalar_gives_relation
#print axioms relation_certificate_iff_span

end XedniAdaptivePublicRelationReduction
