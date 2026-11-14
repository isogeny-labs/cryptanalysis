import Std.Tactic

/-! Faithful conditional scalar-sampling implications. Actual Picard groups,
scalar laws and the implemented geometric maps are explicit bridges. -/
set_option autoImplicit false
namespace NormAssistedSampling223

theorem norm_half_roundtrip {A J : Type}
    (Phi : A → J) (N : J → A)
    (actA : Nat → A → A) (actJ : Nat → J → J)
    (addJ : J → J → J) (zeroJ : J)
    (equivariant : ∀ n a, Phi (actA n a) = actJ n (Phi a))
    (compose : ∀ m n x, actJ m (actJ n x) = actJ (m*n) x)
    (add_action : ∀ m n x, actJ (m+n) x = addJ (actJ m x) (actJ n x))
    (one_action : ∀ x, actJ 1 x = x)
    (zero_left : ∀ x, addJ zeroJ x = x)
    (G : J) (torsion : actJ 2773073 G = zeroJ)
    (norm_two : Phi (N G) = actJ 2 G) :
    Phi (actA 1386537 (N G)) = G := by
  calc
    Phi (actA 1386537 (N G)) = actJ 1386537 (Phi (N G)) := equivariant _ _
    _ = actJ 1386537 (actJ 2 G) := congrArg (actJ 1386537) norm_two
    _ = actJ (1386537*2) G := compose _ _ _
    _ = actJ (2773073+1) G := by rfl
    _ = addJ (actJ 2773073 G) (actJ 1 G) := add_action _ _ _
    _ = G := by rw [torsion, one_action, zero_left]

theorem prepared_sample_exact {A J : Type}
    (Phi : A → J) (actA : Nat → A → A) (actJ : Nat → J → J)
    (equivariant : ∀ n a, Phi (actA n a) = actJ n (Phi a))
    (u : A) (G : J) (prepared : Phi u = G) (r : Nat) :
    Phi (actA r u) = actJ r G := by
  calc
    Phi (actA r u) = actJ r (Phi u) := equivariant _ _
    _ = actJ r G := congrArg (actJ r) prepared

theorem omitted_half_rejected {A J : Type}
    (Phi : A → J) (N : J → A) (addJ : J → J → J) (zeroJ : J)
    (zero_right : ∀ x, addJ x zeroJ = x)
    (left_cancel : ∀ x y z, addJ x y = addJ x z → y = z)
    (G : J) (nonzero : G ≠ zeroJ)
    (norm_double : Phi (N G) = addJ G G) :
    Phi (N G) ≠ G := by
  intro wrong
  have doubled : addJ G G = G := norm_double.symm.trans wrong
  have canceled : G = zeroJ := left_cancel G G zeroJ (doubled.trans (zero_right G).symm)
  exact nonzero canceled

end NormAssistedSampling223
