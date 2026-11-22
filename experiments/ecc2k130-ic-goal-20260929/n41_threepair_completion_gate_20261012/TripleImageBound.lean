import Std

/-! Deduplicating a list cannot increase its length. The conditional theorem
    then bounds the image of an enumerated three-state source by `S³`. The
    concrete source enumeration and subgroup cardinality are executable
    certificates outside this module. -/

theorem eraseDups_length_le {α : Type} [BEq α] (xs : List α) :
    xs.eraseDups.length ≤ xs.length := by
  match xs with
  | [] => simp
  | x :: tail =>
    rw [List.eraseDups_cons]
    have hrec := eraseDups_length_le (tail.filter (fun b => !b == x))
    have hfilter := List.length_filter_le (fun b => !b == x) tail
    simp only [List.length_cons]
    omega
termination_by xs.length
decreasing_by
  simp_wf
  have h := List.length_filter_le (fun b => !b == x) tail
  omega

theorem triple_image_card_le (S : Nat) (G : Type) [BEq G] [LawfulBEq G]
    (source : List (Fin S × Fin S × Fin S))
    (hsource : source.length ≤ S * S * S)
    (f : Fin S × Fin S × Fin S → G) :
    ((source.map f).eraseDups).length ≤ S * S * S := by
  have h₁ := eraseDups_length_le (source.map f)
  have h₂ : (source.map f).length = source.length := List.length_map f
  omega

#print axioms eraseDups_length_le
#print axioms triple_image_card_le
