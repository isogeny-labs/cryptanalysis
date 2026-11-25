import Mathlib.Data.Finset.Card
namespace PublicOverlap
variable {α : Type*} [DecidableEq α]

theorem erase_all (triples : Finset α) (stream : List α) :
    stream.foldl Finset.erase triples = triples \ stream.toFinset := by
  induction stream generalizing triples with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons, ih, List.toFinset_cons]
    ext a
    simp [and_assoc, and_left_comm]

theorem count (triples : Finset α) (stream : List α) :
    triples.card - (stream.foldl Finset.erase triples).card =
    (triples ∩ stream.toFinset).card := by
  rw [erase_all]
  have h := Finset.card_sdiff_add_card_inter triples stream.toFinset
  omega
end PublicOverlap
