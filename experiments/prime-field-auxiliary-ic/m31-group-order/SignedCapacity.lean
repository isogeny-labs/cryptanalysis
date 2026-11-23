import Mathlib

namespace SignedCapacity

/-- Signed coefficient vectors of length k and exact absolute sum m.
At the first coordinate choose zero, or a sign and magnitude i+1. -/
def Shell : ℕ → ℕ → Type
  | 0, m => Fin (if m = 0 then 1 else 0)
  | k+1, m => Shell k m ⊕ (Σ i : Fin m, Bool × Shell k (m-(i.val+1)))

instance shellFinite : (k m : ℕ) → Fintype (Shell k m)
  | 0, m => inferInstanceAs (Fintype (Fin _))
  | k+1, m => by
    letI (j : ℕ) : Fintype (Shell k j) := shellFinite k j
    unfold Shell
    infer_instance

def count : ℕ → ℕ → ℕ
  | 0, m => if m = 0 then 1 else 0
  | k+1, m => count k m + ∑ i : Fin m, 2 * count k (m-(i.val+1))

theorem card_shell (k m : ℕ) : Fintype.card (Shell k m) = count k m := by
  induction k generalizing m with
  | zero => simp [Shell, count]
  | succ k ih =>
    unfold Shell
    simp [count, Fintype.card_prod, ih]

def weight : List ℤ → ℕ
  | [] => 0
  | a :: tail => a.natAbs + weight tail

def coefficients : (k m : ℕ) → Shell k m → List ℤ
  | 0, _, _ => []
  | k+1, m, .inl tail => 0 :: coefficients k m tail
  | k+1, m, .inr ⟨i, pos, tail⟩ =>
    let a := Int.ofNat (i.val+1)
    (if pos then a else -a) :: coefficients k (m-(i.val+1)) tail

/-- Every integer vector is represented at its own length and exact absolute weight. -/
theorem covers (v : List ℤ) (k m : ℕ) (hk : v.length = k) (hm : weight v = m) :
    ∃ s : Shell k m, coefficients k m s = v := by
  induction v generalizing k m with
  | nil =>
    subst k; subst m
    exact ⟨(0 : Fin 1), rfl⟩
  | cons a t ih =>
    subst k
    change a.natAbs + weight t = m at hm
    cases a with
    | ofNat n =>
      cases n with
      | zero =>
        simp at hm
        obtain ⟨s, h⟩ := ih t.length m rfl hm
        exact ⟨Sum.inl s, by simp [coefficients, h]⟩
      | succ n =>
        change (n+1) + weight t = m at hm
        let i : Fin m := ⟨n, by omega⟩
        obtain ⟨s, h⟩ := ih t.length (m-(i.val+1)) rfl (by dsimp [i]; omega)
        exact ⟨Sum.inr ⟨i, true, s⟩, by simp [coefficients, h, i]⟩
    | negSucc n =>
      change (n+1) + weight t = m at hm
      let i : Fin m := ⟨n, by omega⟩
      obtain ⟨s, h⟩ := ih t.length (m-(i.val+1)) rfl (by dsimp [i]; omega)
      exact ⟨Sum.inr ⟨i, false, s⟩, by simp [coefficients, h, i]; omega⟩

abbrev Three := Shell 56 3 ⊕ Shell 56 1
abbrev Four := Shell 56 4 ⊕ Shell 56 2 ⊕ Shell 56 0

theorem three_card : Fintype.card Three = 234304 := by
  simp only [Three, Fintype.card_sum, card_shell]
  native_decide

theorem four_card : Fintype.card Four = 6566785 := by
  simp only [Four, Fintype.card_sum, card_shell]
  native_decide

theorem four_image_bound {G : Type*} [DecidableEq G] (eval : Four → G) :
    (Finset.univ.image eval).card ≤ 6566785 := by
  exact Finset.card_image_le.trans_eq ((Finset.card_univ).trans four_card)

private def decodeThreeShells (k a b c : ℕ) :
    Shell k a ⊕ Shell k b ⊕ Shell k c → List ℤ :=
  Sum.elim (coefficients k a) (Sum.elim (coefficients k b) (coefficients k c))

private theorem vector_image_bound {G : Type*} [DecidableEq G] (k a b c : ℕ)
    (vs : Finset (List ℤ)) (eval : List ℤ → G)
    (shape : ∀ v ∈ vs, v.length = k ∧ (weight v = a ∨ weight v = b ∨ weight v = c)) :
    (vs.image eval).card ≤ Fintype.card (Shell k a ⊕ Shell k b ⊕ Shell k c) := by
  let f := eval ∘ decodeThreeShells k a b c
  have sub : vs.image eval ⊆ Finset.univ.image f := by
    intro x hx
    obtain ⟨v, hv, rfl⟩ := Finset.mem_image.mp hx
    obtain ⟨hl, hw⟩ := shape v hv
    rcases hw with h | h | h
    · obtain ⟨s, hs⟩ := covers v k a hl h
      exact Finset.mem_image.mpr ⟨Sum.inl s, Finset.mem_univ _, congrArg eval hs⟩
    · obtain ⟨s, hs⟩ := covers v k b hl h
      exact Finset.mem_image.mpr ⟨Sum.inr (Sum.inl s), Finset.mem_univ _, congrArg eval hs⟩
    · obtain ⟨s, hs⟩ := covers v k c hl h
      exact Finset.mem_image.mpr ⟨Sum.inr (Sum.inr s), Finset.mem_univ _, congrArg eval hs⟩
  exact (Finset.card_le_card sub).trans (Finset.card_image_le.trans_eq Finset.card_univ)

theorem four_vector_image_bound {G : Type*} [DecidableEq G]
    (vs : Finset (List ℤ)) (eval : List ℤ → G)
    (shape : ∀ v ∈ vs, v.length = 56 ∧ (weight v = 4 ∨ weight v = 2 ∨ weight v = 0)) :
    (vs.image eval).card ≤ 6566785 :=
  (vector_image_bound 56 4 2 0 vs eval shape).trans_eq four_card

end SignedCapacity
