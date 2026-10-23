module

public import Mathlib.Data.Set.Basic

/-! The algebraic transport step for split-level CM orientations.  `I` is the
set of elements of either prime ideal above the level prime.  Only
equivariance, zero preservation and injectivity are needed here; the
geometric identification of Hecke edges is recorded separately. -/
namespace IdealOrientation

public def annihilatedBy {O T : Type*} [Zero T]
    (act : O → T → T) (I : Set O) (x : T) : Prop :=
  ∀ a ∈ I, act a x = 0

public theorem transport_iff {O T U : Type*} [Zero T] [Zero U]
    (actT : O → T → T) (actU : O → U → U) (I : Set O)
    (f : T → U) (hf0 : f 0 = 0) (hinj : Function.Injective f)
    (hequiv : ∀ a x, f (actT a x) = actU a (f x)) (x : T) :
    annihilatedBy actU I (f x) ↔ annihilatedBy actT I x := by
  constructor
  · intro hu a ha
    apply hinj
    rw [hequiv, hu a ha, hf0]
  · intro ht a ha
    rw [← hequiv, ht a ha, hf0]

public theorem two_ideal_labels_preserved {O T U : Type*} [Zero T] [Zero U]
    (actT : O → T → T) (actU : O → U → U)
    (I J : Set O) (f : T → U) (hf0 : f 0 = 0)
    (hinj : Function.Injective f)
    (hequiv : ∀ a x, f (actT a x) = actU a (f x)) (x : T) :
    (annihilatedBy actU I (f x) ↔ annihilatedBy actT I x) ∧
    (annihilatedBy actU J (f x) ↔ annihilatedBy actT J x) := by
  exact ⟨transport_iff actT actU I f hf0 hinj hequiv x,
    transport_iff actT actU J f hf0 hinj hequiv x⟩

end IdealOrientation

#print axioms IdealOrientation.transport_iff
#print axioms IdealOrientation.two_ideal_labels_preserved
