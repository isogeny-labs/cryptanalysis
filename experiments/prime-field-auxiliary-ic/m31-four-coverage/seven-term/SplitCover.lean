import Mathlib

namespace M31SplitCover
open Finset
variable {G ι : Type*} [AddCommGroup G] [DecidableEq G]

def triples : Finset (Finset (Fin 7)) := (univ : Finset (Fin 7)).powersetCard 3

theorem triples_card : triples.card = 35 := by
  rw [triples, card_powersetCard]
  decide

def endpoints (row : Fin 7 → G) : Finset G :=
  ((univ : Finset Bool) ×ˢ triples).image (fun (choice : Bool × Finset (Fin 7)) =>
    let point := ∑ j ∈ choice.2, row j
    if choice.1 then -point else point)

theorem endpoints_card (row : Fin 7 → G) : (endpoints row).card ≤ 70 := by
  unfold endpoints
  apply le_trans card_image_le
  simp [card_product, triples_card]

theorem cover_bound (classes : Finset ι) (row : ι → Fin 7 → G) (points : Finset G)
    (covers : ∀ x ∈ points, ∃ c ∈ classes, x ∈ endpoints (row c)) :
    points.card ≤ classes.card * 70 := by
  have sub : points ⊆ classes.biUnion (fun c => endpoints (row c)) := by
    intro x hx
    exact mem_biUnion.mpr (covers x hx)
  calc
    points.card ≤ _ := card_le_card sub
    _ ≤ ∑ c ∈ classes, (endpoints (row c)).card := card_biUnion_le
    _ ≤ ∑ _c ∈ classes, 70 := sum_le_sum fun c _ => endpoints_card (row c)
    _ = _ := by simp

theorem m31_floor (classes : Finset ι) (row : ι → Fin 7 → G) (points : Finset G)
    (size : points.card = 3439976)
    (covers : ∀ x ∈ points, ∃ c ∈ classes, x ∈ endpoints (row c)) :
    49143 ≤ classes.card := by
  have h := cover_bound classes row points covers
  rw [size] at h
  omega

end M31SplitCover
