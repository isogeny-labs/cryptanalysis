import Std

/- An exact superset membership oracle becomes an exact usable-source oracle
   after every recovered root is checked against the usable product list. -/

namespace SupersetFilter

theorem filtered_hit_iff_usable_hit {K : Type} (allProducts usableProducts : List K)
    (allowed : K → Prop) (equation : K → Prop)
    (subset : ∀ q ∈ usableProducts, q ∈ allProducts)
    (allowed_exact : ∀ q, allowed q ↔ q ∈ usableProducts) :
    (∃ q ∈ allProducts, equation q ∧ allowed q) ↔
      ∃ q ∈ usableProducts, equation q := by
  constructor
  · rintro ⟨q, _, heq, hallowed⟩
    exact ⟨q, (allowed_exact q).mp hallowed, heq⟩
  · rintro ⟨q, husable, heq⟩
    exact ⟨q, subset q husable, heq, (allowed_exact q).mpr husable⟩

#print axioms SupersetFilter.filtered_hit_iff_usable_hit

end SupersetFilter
