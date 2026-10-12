import Std

/-! Seven forward roots preserve every source and the terminal target constraint,
provided each root satisfies its corresponding S3 relation. -/
namespace N41FourPairForward

universe u
variable {Coord : Type u}

def ForwardRelation
    (forward : Coord → Coord → Bool → Coord)
    (left right output : Fin 7 → Fin 15)
    (source : (Fin 15 → Coord) → Prop)
    (target : Coord) : Prop :=
  ∃ nodes : Fin 15 → Coord, ∃ branches : Fin 7 → Bool,
    source nodes ∧
    (∀ i, nodes (output i) =
      forward (nodes (left i)) (nodes (right i)) (branches i)) ∧
    nodes ⟨14, by decide⟩ = target

def S3Relation
    (s3 : Coord → Coord → Coord → Prop)
    (left right output : Fin 7 → Fin 15)
    (source : (Fin 15 → Coord) → Prop)
    (target : Coord) : Prop :=
  ∃ nodes : Fin 15 → Coord,
    source nodes ∧
    (∀ i, s3 (nodes (left i)) (nodes (right i)) (nodes (output i))) ∧
    nodes ⟨14, by decide⟩ = target

theorem forward_relation_sound
    (s3 : Coord → Coord → Coord → Prop)
    (forward : Coord → Coord → Bool → Coord)
    (left right output : Fin 7 → Fin 15)
    (source : (Fin 15 → Coord) → Prop)
    (target : Coord)
    (rootSound : ∀ a b branch, s3 a b (forward a b branch)) :
    ForwardRelation forward left right output source target →
      S3Relation s3 left right output source target := by
  rintro ⟨nodes, branches, hsource, hforward, htarget⟩
  refine ⟨nodes, hsource, ?_, htarget⟩
  intro i
  rw [hforward i]
  exact rootSound _ _ _

#print axioms N41FourPairForward.forward_relation_sound

end N41FourPairForward
