import PublicGroupRecovery
import Mathlib.Algebra.Module.ZMod

namespace XedniPublicFirstLargeHoldout

/-- In a prime-order scalar module, a relation between two public multiples
of a nonzero point is equivalent to direct scalar recovery. -/
theorem prime_order_public_relation_iff_recovered_scalar
    (q : ℕ) [Fact (Nat.Prime q)]
    {A : Type*} [AddCommGroup A] [Module (ZMod q) A]
    (G : A) (hG : G ≠ 0) (a b w t₁ t₂ : ZMod q)
    (hs : a + b ≠ 0) :
    a • ((w - t₁) • G) + b • ((w - t₂) • G) = 0 ↔
      w = (a * t₁ + b * t₂) / (a + b) := by
  have hcombine : a • ((w - t₁) • G) + b • ((w - t₂) • G) =
      (a * (w - t₁) + b * (w - t₂)) • G := by
    rw [add_smul, mul_smul, mul_smul]
  rw [hcombine]
  have hzero : (a * (w - t₁) + b * (w - t₂)) • G = 0 ↔
      a * (w - t₁) + b * (w - t₂) = 0 := by
    constructor
    · intro h
      exact (smul_eq_zero.mp h).resolve_right hG
    · intro h
      simp [h]
  rw [hzero]
  exact public_relation_iff_recovered_scalar a b w t₁ t₂ hs

/-- The public relation in an additive group killed by `q`, using its
canonical `ZMod q` action. -/
def TorsionPublicRelation (q : ℕ) [Fact (Nat.Prime q)]
    {A : Type*} [AddCommGroup A]
    (htors : ∀ X : A, q • X = 0)
    (G : A) (a b w t₁ t₂ : ZMod q) : Prop := by
  letI : Module (ZMod q) A := AddCommGroup.zmodModule htors
  exact a • ((w - t₁) • G) + b • ((w - t₂) • G) = 0

/-- Any additive group killed by prime `q` inherits the needed `ZMod q`
module structure; its public relation determines the target scalar. -/
theorem torsion_public_relation_iff_recovered_scalar
    (q : ℕ) [Fact (Nat.Prime q)]
    {A : Type*} [AddCommGroup A]
    (htors : ∀ X : A, q • X = 0)
    (G : A) (hG : G ≠ 0) (a b w t₁ t₂ : ZMod q)
    (hs : a + b ≠ 0) :
    TorsionPublicRelation q htors G a b w t₁ t₂ ↔
      w = (a * t₁ + b * t₂) / (a + b) := by
  unfold TorsionPublicRelation
  letI : Module (ZMod q) A := AddCommGroup.zmodModule htors
  exact prime_order_public_relation_iff_recovered_scalar q G hG a b w t₁ t₂ hs

#print axioms prime_order_public_relation_iff_recovered_scalar
#print axioms torsion_public_relation_iff_recovered_scalar

end XedniPublicFirstLargeHoldout
