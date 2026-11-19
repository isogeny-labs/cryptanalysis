import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import Mathlib.Tactic

/-!
A valid adaptive public-point relation with a nonzero target coefficient
contains a discrete-log certificate. The first results work in any module
over the prime field `ZMod q`. The integer-scalar results work directly in
an additive commutative group with a point of order `q`, including an
elliptic-curve subgroup once its order and membership are established. The
results concern the algebraic output of a relation procedure, without
assuming an algorithm for finding such an output.
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

section IntegerGroup

variable {H : Type u} [AddCommGroup H]

/-- An ordinary integer-scalar relation on a point of additive order `q`
recovers the target scalar modulo `q`. This statement does not require a
`ZMod q` module instance on the ambient group. -/
theorem integer_relation_recovers_scalar (P : H)
    (horder : addOrderOf P = q) (v a b : ℤ)
    (hb : (b : ZMod q) ≠ 0)
    (hrel : a • P + b • (v • P) = 0) :
    (v : ZMod q) = -(a : ZMod q) / (b : ZMod q) := by
  have hsmul : (a + b * v) • P = 0 := by
    simpa [add_zsmul, mul_zsmul] using hrel
  have hdvd : (q : ℤ) ∣ a + b * v := by
    have h : (addOrderOf P : ℤ) ∣ a + b * v :=
      (addOrderOf_dvd_iff_zsmul_eq_zero).2 hsmul
    simpa [horder] using h
  have hz : ((a + b * v : ℤ) : ZMod q) = 0 :=
    (ZMod.intCast_zmod_eq_zero_iff_dvd _ _).2 hdvd
  have hcoef : (a : ZMod q) + (b : ZMod q) * (v : ZMod q) = 0 := by
    simpa only [Int.cast_add, Int.cast_mul] using hz
  apply (eq_div_iff hb).2
  linear_combination hcoef

/-- A valid integer-scalar relation for a target in the subgroup generated
by `P` gives an integer representative of the target log and its exact
residue modulo `q`. -/
theorem integer_relation_for_subgroup (P Q : H)
    (horder : addOrderOf P = q)
    (hQ : Q ∈ AddSubgroup.zmultiples P)
    (a b : ℤ) (hb : (b : ZMod q) ≠ 0)
    (hrel : a • P + b • Q = 0) :
    ∃ v : ℤ, Q = v • P ∧
      (v : ZMod q) = -(a : ZMod q) / (b : ZMod q) := by
  obtain ⟨v, hv⟩ := AddSubgroup.mem_zmultiples_iff.mp hQ
  refine ⟨v, hv.symm, ?_⟩
  rw [← hv] at hrel
  exact integer_relation_recovers_scalar q P horder v a b hb hrel

end IntegerGroup

/-- Specialization to mathlib's elliptic-curve point group. The order and
subgroup-membership hypotheses are exactly the facts a concrete curve
certificate must provide. -/
theorem elliptic_relation_for_subgroup
    (W : WeierstrassCurve (ZMod q)) [W.IsElliptic]
    (P Q : W.toAffine.Point)
    (horder : addOrderOf P = q)
    (hQ : Q ∈ AddSubgroup.zmultiples P)
    (a b : ℤ) (hb : (b : ZMod q) ≠ 0)
    (hrel : a • P + b • Q = 0) :
    ∃ v : ℤ, Q = v • P ∧
      (v : ZMod q) = -(a : ZMod q) / (b : ZMod q) :=
  integer_relation_for_subgroup q P Q horder hQ a b hb hrel

section PublicOracle

variable {H : Type u} [AddCommGroup H] [DecidableEq H]

/-- The public point associated with a scalar residue and base point. -/
def pointOfScalar (P : H) (v : ZMod q) : H := v.val • P

/-- Verify a public integer-coefficient relation and extract its scalar
certificate. The computation uses only `P`, `Q`, and the candidate pair. -/
def extractScalar (P Q : H) : Option (ℤ × ℤ) → Option (ZMod q)
  | none => none
  | some (a, b) =>
    if (b : ZMod q) ≠ 0 ∧ a • P + b • Q = 0 then
      some (-(a : ZMod q) / (b : ZMod q))
    else none

/-- The extractor returns the target scalar exactly when its candidate is a
valid public relation for that target. -/
theorem extractScalar_iff_valid (P : H) (horder : addOrderOf P = q)
    (v : ZMod q) (o : Option (ℤ × ℤ)) :
    extractScalar q P (pointOfScalar q P v) o = some v ↔
      ∃ a b : ℤ, o = some (a, b) ∧
        (b : ZMod q) ≠ 0 ∧ a • P + b • pointOfScalar q P v = 0 := by
  cases o with
  | none => simp [extractScalar]
  | some ab =>
    obtain ⟨a, b⟩ := ab
    by_cases hv : (b : ZMod q) ≠ 0 ∧ a • P + b • pointOfScalar q P v = 0
    · have hlog : v = -(a : ZMod q) / (b : ZMod q) := by
        have h := integer_relation_recovers_scalar q P horder (v.val : ℤ) a b hv.1
        have hrel : a • P + b • ((v.val : ℤ) • P) = 0 := by
          simpa only [pointOfScalar, natCast_zsmul] using hv.2
        have hres := h hrel
        simpa using hres
      simp [extractScalar, hv, hlog]
    · simp [extractScalar, hv]

/-- A Boolean check of a candidate public relation. -/
def validRelationOutput (P Q : H) : Option (ℤ × ℤ) → Bool
  | none => false
  | some (a, b) => decide ((b : ZMod q) ≠ 0 ∧ a • P + b • Q = 0)

theorem validRelationOutput_iff (P Q : H) (o : Option (ℤ × ℤ)) :
    validRelationOutput q P Q o = true ↔
      ∃ a b : ℤ, o = some (a, b) ∧
        (b : ZMod q) ≠ 0 ∧ a • P + b • Q = 0 := by
  cases o with
  | none => simp [validRelationOutput]
  | some ab =>
    obtain ⟨a, b⟩ := ab
    simp [validRelationOutput]

/-- For any fixed set of scalar inputs, a public-input coefficient oracle
and the verified scalar extractor succeed on exactly the same targets. -/
theorem extractor_success_set_eq (P : H) (horder : addOrderOf P = q)
    (oracle : H → Option (ℤ × ℤ)) (targets : Finset (ZMod q)) :
    targets.filter (fun v =>
      extractScalar q P (pointOfScalar q P v)
        (oracle (pointOfScalar q P v)) = some v) =
    targets.filter (fun v =>
      validRelationOutput q P (pointOfScalar q P v)
        (oracle (pointOfScalar q P v)) = true) := by
  ext v
  simp only [Finset.mem_filter]
  rw [extractScalar_iff_valid q P horder v (oracle (pointOfScalar q P v)),
    validRelationOutput_iff]

end PublicOracle

#print axioms relation_certificate_verifies
#print axioms relation_certificate_recovers
#print axioms known_scalar_gives_relation
#print axioms relation_certificate_iff_span
#print axioms integer_relation_recovers_scalar
#print axioms integer_relation_for_subgroup
#print axioms elliptic_relation_for_subgroup
#print axioms extractScalar_iff_valid
#print axioms validRelationOutput_iff
#print axioms extractor_success_set_eq

end XedniAdaptivePublicRelationReduction
