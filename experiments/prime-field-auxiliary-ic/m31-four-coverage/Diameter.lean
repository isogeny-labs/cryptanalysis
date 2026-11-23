import Mathlib.Data.Finset.Card
import Mathlib.Algebra.BigOperators.Group.List.Basic
import Mathlib.Algebra.Group.Basic
import Mathlib.Data.Fintype.Card
import Mathlib.Tactic

namespace M31FourCoverage

variable {G : Type*} [AddCommGroup G] [Fintype G] [DecidableEq G]

theorem dense_sum (s t : Finset G) (h : Fintype.card G < s.card + t.card) (g : G) :
    ∃ a ∈ s, ∃ b ∈ t, a + b = g := by
  classical
  by_contra miss
  have hd : Disjoint s (t.image (fun b => g-b)) := by
    rw [Finset.disjoint_left]
    intro a ha hi
    obtain ⟨b,hb,rfl⟩ := Finset.mem_image.mp hi
    exact miss ⟨_,ha,b,hb,sub_add_cancel g b⟩
  have cap := Finset.card_le_univ (s ∪ t.image (fun b => g-b))
  rw [Finset.card_union_of_disjoint hd, Finset.card_image_of_injective _ (by
    intro x y he
    simpa using he)] at cap
  omega

def reachable (basis : Finset G) (n : Nat) (x : G) :=
  ∃ terms : List G, terms.length ≤ n ∧ (∀ a ∈ terms, a ∈ basis) ∧ terms.sum = x

theorem diameter_bound (basis s t : Finset G) {r k : Nat}
    (hs : ∀ x ∈ s, reachable basis r x) (ht : ∀ x ∈ t, reachable basis k x)
    (h : Fintype.card G < s.card + t.card) (g : G) : reachable basis (r+k) g := by
  obtain ⟨a,ha,b,hb,rfl⟩ := dense_sum s t h g
  obtain ⟨u,hu,hbu,rfl⟩ := hs a ha
  obtain ⟨v,hv,hbv,rfl⟩ := ht b hb
  refine ⟨u++v, by simpa using Nat.add_le_add hu hv, ?_, List.sum_append⟩
  intro x hx
  exact (List.mem_append.mp hx).elim (hbu x) (hbv x)

/-- Count distinct first summands that can be completed, for any group element. -/
theorem fixture_overlap (s t : Finset G) (hn : Fintype.card G = 2147505293)
    (hs : s.card = 783104641) (ht : t.card = 1586841251) (g : G) :
    222440599 ≤ (s ∩ t.image (fun b => g-b)).card := by
  have cap := Finset.card_le_univ (s ∪ t.image (fun b => g-b))
  have total := Finset.card_union_add_card_inter s (t.image (fun b => g-b))
  rw [Finset.card_image_of_injective _ (by intro x y he; simpa using he)] at total
  omega

theorem fixture_nine (basis s t : Finset G) (hn : Fintype.card G = 2147505293)
    (cs : s.card = 783104641) (ct : t.card = 1586841251)
    (hs : ∀ x ∈ s, reachable basis 4 x) (ht : ∀ x ∈ t, reachable basis 5 x)
    (g : G) : reachable basis 9 g :=
  diameter_bound basis s t hs ht (by omega) g

end M31FourCoverage
