import Mathlib.Logic.Equiv.Fintype
import Mathlib.Data.Fintype.Card
import Mathlib.Tactic

namespace XedniRandomLabelCoupling

/-- Reindexing the domain of a bijective encoding is itself a bijection on
all encodings. -/
def relabelEquiv {G L : Type*} (σ : Equiv.Perm G) :
    (G ≃ L) ≃ (G ≃ L) where
  toFun enc := σ.symm.trans enc
  invFun enc := σ.trans enc
  left_inv := by
    intro enc
    ext g
    simp [Equiv.trans_apply]
  right_inv := by
    intro enc
    ext g
    simp [Equiv.trans_apply]

/-- Two collision-free indexed group-element traces have a bijective
pairing of all bijective encodings that makes their observed label tuples
identical. -/
theorem injective_trace_label_coupling {G L : Type*} {n : ℕ}
    (x y : Fin n → G) (hx : Function.Injective x)
    (hy : Function.Injective y) :
    ∃ Φ : (G ≃ L) ≃ (G ≃ L),
      ∀ (enc : G ≃ L) (i : Fin n), (Φ enc) (y i) = enc (x i) := by
  obtain ⟨σ, hσ⟩ := Equiv.Perm.exists_extending_pair x y hx hy
  refine ⟨relabelEquiv σ, ?_⟩
  intro enc i
  change enc (σ.symm (y i)) = enc (x i)
  rw [← hσ i, σ.symm_apply_apply]

/-- Every event determined by the visible label tuple has the same number
of encodings on the two collision-free traces. Hence uniform random
bijections give the same event probability. -/
noncomputable def eventCount {G L : Type*} [Fintype G] [Fintype L]
    {n : ℕ} (x : Fin n → G) (event : (Fin n → L) → Prop) : ℕ := by
  classical
  exact Fintype.card {enc : G ≃ L // event (fun i => enc (x i))}

theorem label_event_card_eq {G L : Type*} [Fintype G] [Fintype L]
    {n : ℕ} (x y : Fin n → G) (hx : Function.Injective x)
    (hy : Function.Injective y) (event : (Fin n → L) → Prop) :
    eventCount x event = eventCount y event := by
  classical
  obtain ⟨Φ, hΦ⟩ := injective_trace_label_coupling (L := L) x y hx hy
  have hobs (enc : G ≃ L) :
      (fun i => (Φ enc) (y i)) = (fun i => enc (x i)) := by
    funext i
    exact hΦ enc i
  let e : {enc : G ≃ L // event (fun i => enc (x i))} ≃
      {enc : G ≃ L // event (fun i => enc (y i))} := {
    toFun := fun ⟨enc, henc⟩ => ⟨Φ enc, by simpa [hobs enc] using henc⟩
    invFun := fun ⟨enc, henc⟩ => ⟨Φ.symm enc, by
      have h := hobs (Φ.symm enc)
      simp only [Equiv.apply_symm_apply] at h
      rw [← h]
      exact henc⟩
    left_inv := by
      intro enc
      apply Subtype.ext
      simp
    right_inv := by
      intro enc
      apply Subtype.ext
      simp
  }
  change Fintype.card {enc : G ≃ L // event (fun i => enc (x i))} =
    Fintype.card {enc : G ≃ L // event (fun i => enc (y i))}
  exact Fintype.card_congr e

def affineTrace {F : Type*} [Ring F] {n : ℕ}
    (forms : Fin n → F × F) (w : F) (i : Fin n) : F :=
  (forms i).1 * w + (forms i).2

theorem affine_trace_label_event_card_eq {F L : Type*}
    [Field F] [Fintype F] [Fintype L] {n : ℕ}
    (forms : Fin n → F × F) (w₁ w₂ : F)
    (h₁ : Function.Injective (affineTrace forms w₁))
    (h₂ : Function.Injective (affineTrace forms w₂))
    (event : (Fin n → L) → Prop) :
    eventCount (affineTrace forms w₁) event =
      eventCount (affineTrace forms w₂) event := by
  exact label_event_card_eq
    (affineTrace forms w₁) (affineTrace forms w₂) h₁ h₂ event

#print axioms relabelEquiv
#print axioms injective_trace_label_coupling
#print axioms label_event_card_eq
#print axioms affine_trace_label_event_card_eq

end XedniRandomLabelCoupling
