import Mathlib.Algebra.BigOperators.Group.List.Basic

namespace SignedReach
variable {G : Type*} [AddCommGroup G]
def Ball (S : G → Prop) (k : ℕ) (x : G) : Prop :=
  ∃ l : List G, l.length ≤ k ∧ (∀ a ∈ l, S a) ∧ l.sum = x

private theorem sumNeg (u : List G) : (u.map Neg.neg).sum = -u.sum := by
  induction u with
  | nil => simp
  | cons a u ih => simp [ih, add_comm]

theorem double_ball (S : G → Prop) (symm : ∀ a, S a → S (-a)) (k : ℕ) (d : G) :
    Ball S (k+k) d ↔ ∃ x, Ball S k x ∧ Ball S k (x+d) := by
  constructor
  · rintro ⟨l,hlen,hs,rfl⟩
    let u := l.take k
    let v := l.drop k
    have hsplit : u++v=l := List.take_append_drop k l
    have hsum : u.sum+v.sum=l.sum := by rw [← List.sum_append,hsplit]
    refine ⟨-u.sum, ⟨u.map Neg.neg, ?_, ?_, ?_⟩, ⟨v, ?_, ?_, ?_⟩⟩
    · simpa only [List.length_map, u, List.length_take] using (Nat.min_le_left k l.length)
    · intro a ha
      obtain ⟨b,hb,rfl⟩ := List.mem_map.mp ha
      exact symm _ (hs _ (List.mem_of_mem_take hb))
    · exact sumNeg u
    · simp [v]; omega
    · exact fun _ ha => hs _ (List.mem_of_mem_drop ha)
    · rw [← hsum,neg_add_cancel_left]
  · rintro ⟨x,⟨u,hu,su,eu⟩,⟨v,hv,sv,ev⟩⟩
    refine ⟨u.map Neg.neg ++ v, ?_, ?_, ?_⟩
    · simp; omega
    · intro a ha
      rcases List.mem_append.mp ha with ha | ha
      · obtain ⟨b,hb,rfl⟩ := List.mem_map.mp ha
        exact symm _ (su _ hb)
      · exact sv _ ha
    · simp [sumNeg,eu,ev]

#print axioms double_ball
end SignedReach
