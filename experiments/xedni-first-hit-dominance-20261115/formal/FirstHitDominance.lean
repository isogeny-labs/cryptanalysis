import Mathlib

namespace XedniFirstHitDominance

variable {H A : Type*} [AddCommGroup H] [AddCommGroup A]
variable {n r : ℕ}

/-- A relation found on the rational lift at query `i`. The coefficients may
depend on the query. -/
def rationalEvent (L : Fin n → Fin r → H) (c : Fin n → Fin r → ℤ)
    (i : Fin n) : Prop :=
  ∑ j : Fin r, c i j • L i j = 0

/-- The same coefficient vector can be checked on the public group points. -/
def publicEvent (P : Fin n → Fin r → A) (c : Fin n → Fin r → ℤ)
    (i : Fin n) : Prop :=
  ∑ j : Fin r, c i j • P i j = 0

/-- Every rational relation reduces to a public relation at the same query. -/
theorem relation_reduces (ρ : H →+ A) (L : Fin n → Fin r → H)
    (P : Fin n → Fin r → A) (c : Fin n → Fin r → ℤ)
    (hpoint : ∀ i j, ρ (L i j) = P i j) (i : Fin n)
    (h : rationalEvent L c i) : publicEvent P c i := by
  unfold rationalEvent at h
  unfold publicEvent
  calc
    (∑ j : Fin r, c i j • P i j) =
        ∑ j : Fin r, ρ (c i j • L i j) := by
      apply Finset.sum_congr rfl
      intro j hj
      rw [map_zsmul, hpoint i j]
    _ = ρ (∑ j : Fin r, c i j • L i j) := by rw [map_sum]
    _ = 0 := by rw [h]; simp

/-- All relation queries belong to the public relation support for the same
query-dependent coefficient schedule. -/
theorem relation_support_subset_public (ρ : H →+ A)
    (L : Fin n → Fin r → H) (P : Fin n → Fin r → A)
    (c : Fin n → Fin r → ℤ) (hpoint : ∀ i j, ρ (L i j) = P i j) :
    {i : Fin n | rationalEvent L c i} ⊆
      {i : Fin n | publicEvent P c i} := by
  intro i hi
  exact relation_reduces ρ L P c hpoint i hi

/-- No rational relation occurs before a prefix free of public relations. -/
theorem no_early_rational_relation (ρ : H →+ A)
    (L : Fin n → Fin r → H) (P : Fin n → Fin r → A)
    (c : Fin n → Fin r → ℤ) (hpoint : ∀ i j, ρ (L i j) = P i j)
    (first : Fin n)
    (hbefore : ∀ j : Fin n, j < first → ¬ publicEvent P c j)
    (j : Fin n) (hj : j < first) : ¬ rationalEvent L c j := by
  intro h
  exact hbefore j hj (relation_reduces ρ L P c hpoint j h)

/-- If `first` is the first public relation query, every rational relation
query has index at least `first`. -/
theorem first_hit_dominance (ρ : H →+ A)
    (L : Fin n → Fin r → H) (P : Fin n → Fin r → A)
    (c : Fin n → Fin r → ℤ) (hpoint : ∀ i j, ρ (L i j) = P i j)
    (first : Fin n) (_hfirst : publicEvent P c first)
    (hbefore : ∀ j : Fin n, j < first → ¬ publicEvent P c j)
    (hit : Fin n) (hhit : rationalEvent L c hit) : first ≤ hit := by
  by_contra hn
  have hlt : hit < first := lt_of_not_ge hn
  exact (no_early_rational_relation ρ L P c hpoint first hbefore hit hlt) hhit

#print axioms relation_reduces
#print axioms relation_support_subset_public
#print axioms no_early_rational_relation
#print axioms first_hit_dominance

end XedniFirstHitDominance
