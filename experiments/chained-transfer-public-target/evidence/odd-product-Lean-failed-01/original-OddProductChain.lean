import Std.Tactic

/-! Derive the actual52 compositions from genuine dual2/source13 pairs.
Scalar actions and commutation are explicit hypotheses, not an assumed52
or inverse conclusion. Actual geometric interpretations remain written. -/
set_option autoImplicit false
namespace OddProductChain223

theorem both_chain_fiftytwo {A B J L : Type}
    (phiOld : A → J) (normOld : J → A)
    (gamma : A → B) (delta : B → A)
    (phiNew : B → L) (normNew : L → B)
    (sA : Nat → A → A) (sB : Nat → B → B)
    (sJ : Nat → J → J) (sL : Nat → L → L)
    (oldA : ∀ a, normOld (phiOld a)=sA 2 a)
    (oldJ : ∀ x, phiOld (normOld x)=sJ 2 x)
    (newB : ∀ b, normNew (phiNew b)=sB 2 b)
    (newL : ∀ y, phiNew (normNew y)=sL 2 y)
    (sourceA : ∀ a, delta (gamma a)=sA 13 a)
    (sourceB : ∀ b, gamma (delta b)=sB 13 b)
    (gammaScalar : ∀ n a, gamma (sA n a)=sB n (gamma a))
    (deltaScalar : ∀ n b, delta (sB n b)=sA n (delta b))
    (phiOldScalar : ∀ n a, phiOld (sA n a)=sJ n (phiOld a))
    (phiNewScalar : ∀ n b, phiNew (sB n b)=sL n (phiNew b))
    (jMul : ∀ m n x, sJ (m*n) x=sJ m (sJ n x))
    (lMul : ∀ m n y, sL (m*n) y=sL m (sL n y)) :
    (∀ x, phiOld (delta (normNew (phiNew (gamma (normOld x)))))=sJ 52 x) ∧
    (∀ y, phiNew (gamma (normOld (phiOld (delta (normNew y)))))=sL 52 y) := by
  constructor
  · intro x
    rw [newB, deltaScalar, sourceA, phiOldScalar, phiOldScalar, oldJ,
      ← jMul, ← jMul]
    rfl
  · intro y
    rw [oldA, gammaScalar, sourceB, phiNewScalar, phiNewScalar, newL,
      ← lMul, ← lMul]
    rfl

theorem original_source_point_fiftytwo {A B J L : Type}
    (phiOld : A → J) (normOld : J → A)
    (gamma : A → B) (delta : B → A)
    (phiNew : B → L) (normNew : L → B)
    (sA : Nat → A → A) (sB : Nat → B → B)
    (oldA : ∀ a, normOld (phiOld a)=sA 2 a)
    (newB : ∀ b, normNew (phiNew b)=sB 2 b)
    (sourceA : ∀ a, delta (gamma a)=sA 13 a)
    (deltaScalar : ∀ n b, delta (sB n b)=sA n (delta b))
    (aMul : ∀ m n a, sA (m*n) a=sA m (sA n a)) :
    ∀ a, delta (normNew (phiNew (gamma (normOld (phiOld a)))))=sA 52 a := by
  intro a
  rw [oldA, newB, deltaScalar, sourceA, ← aMul, ← aMul]
  rfl

end OddProductChain223
