import Std.Tactic

/-! Faithful structural implications. The actual etale groups, quotient
category and Ciani/Picard interpretations remain written bridges. -/
set_option autoImplicit false
namespace OddProductRefinement223

theorem killed_fiftytwo_primary_projectors {A : Type}
    (act : Nat → A → A) (plus : A → A → A) (zero : A)
    (mul : ∀ m n x, act (m*n) x=act m (act n x))
    (sum : ∀ m n x, act (m+n) x=plus (act m x) (act n x))
    (one : ∀ x, act 1 x=x) (zeroStable : ∀ n, act n zero=zero)
    (addZero : ∀ x, plus x zero=x) (x : A) (killed : act 52 x=zero) :
    x=plus (act 13 x) (act 40 x) ∧
    act 4 (act 13 x)=zero ∧ act 13 (act 40 x)=zero ∧
    (∀ z, act 4 z=zero → act 13 z=zero → z=zero) := by
  have h53 : act 53 x=x := by
    calc
      act 53 x=plus (act 1 x) (act 52 x) := sum 1 52 x
      _=x := by rw [one, killed, addZero]
  refine ⟨?_, ?_, ?_, ?_⟩
  · calc
      x=act 53 x := h53.symm
      _=plus (act 13 x) (act 40 x) := sum 13 40 x
  · rw [← mul]
    exact killed
  · calc
      act 13 (act 40 x)=act 520 x := (mul 13 40 x).symm
      _=act 10 (act 52 x) := mul 10 52 x
      _=zero := by rw [killed, zeroStable]
  · intro z h4 h13
    have hz : act 13 z=z := by
      calc
        act 13 z=plus (act 1 z) (act 12 z) := sum 1 12 z
        _=plus z (act 3 (act 4 z)) := by rw [one, mul 3 4 z]
        _=z := by rw [h4, zeroStable, addZero]
    exact hz.symm.trans h13

theorem quotient_factor_and_twice_chain {A B J L : Type}
    (phiOld : A → J) (normOld : J → A) (gamma : A → B)
    (phiNew : B → L) (doubleJ : J → J) (zeroJ : J) (zeroL : L)
    (admissible : (A → L) → Prop)
    (quotient : ∀ f, admissible f →
      (∀ a, phiOld a=zeroJ → f a=zeroL) →
      ∃ beta : J → L, ∀ a, beta (phiOld a)=f a)
    (compositionHom : admissible (fun a => phiNew (gamma a)))
    (transportedKernel : ∀ a, phiOld a=zeroJ → phiNew (gamma a)=zeroL)
    (oldJ : ∀ x, phiOld (normOld x)=doubleJ x) :
    ∃ beta : J → L,
      (∀ a, beta (phiOld a)=phiNew (gamma a)) ∧
      (∀ x, phiNew (gamma (normOld x))=beta (doubleJ x)) := by
  obtain ⟨beta, factor⟩ := quotient (fun a => phiNew (gamma a))
    compositionHom transportedKernel
  refine ⟨beta, factor, ?_⟩
  intro x
  calc
    phiNew (gamma (normOld x))=beta (phiOld (normOld x)) := (factor (normOld x)).symm
    _=beta (doubleJ x) := congrArg beta (oldJ x)

theorem identical_source_pair_elimination {A B J L : Type}
    (phiOld : A → J) (normOld : J → A) (gamma : A → B)
    (phiNew : B → L) (doubleA : A → A)
    (oldA : ∀ a, normOld (phiOld a)=doubleA a) :
    ∀ a, phiNew (gamma (normOld (phiOld a)))=phiNew (gamma (doubleA a)) := by
  intro a
  rw [oldA]

end OddProductRefinement223
