import Std

/-! Structural soundness of replacing nine S3 links by forward roots.
The field-specific root identity and the concrete node topology remain
separate obligations in PROOF_MAP.md. -/
namespace N41ForwardRoot

universe u
variable {Coord : Type u}

def ForwardRelation
    (forward : Coord → Coord → Bool → Coord)
    (left right output : Fin 9 → Fin 19)
    (source : (Fin 19 → Coord) → Prop)
    (target : Coord) : Prop :=
  ∃ nodes : Fin 19 → Coord, ∃ branches : Fin 9 → Bool,
    source nodes ∧
    (∀ i, nodes (output i) =
      forward (nodes (left i)) (nodes (right i)) (branches i)) ∧
    nodes (output ⟨8, by decide⟩) = target

def S3Relation
    (s3 : Coord → Coord → Coord → Prop)
    (left right output : Fin 9 → Fin 19)
    (source : (Fin 19 → Coord) → Prop)
    (target : Coord) : Prop :=
  ∃ nodes : Fin 19 → Coord,
    source nodes ∧
    (∀ i, s3 (nodes (left i)) (nodes (right i)) (nodes (output i))) ∧
    nodes (output ⟨8, by decide⟩) = target

theorem forward_relation_sound
    (s3 : Coord → Coord → Coord → Prop)
    (forward : Coord → Coord → Bool → Coord)
    (left right output : Fin 9 → Fin 19)
    (source : (Fin 19 → Coord) → Prop)
    (target : Coord)
    (rootSound : ∀ a b branch, s3 a b (forward a b branch)) :
    ForwardRelation forward left right output source target →
      S3Relation s3 left right output source target := by
  rintro ⟨nodes, branches, hsource, hforward, htarget⟩
  refine ⟨nodes, hsource, ?_, htarget⟩
  intro i
  rw [hforward i]
  exact rootSound _ _ _

#print axioms N41ForwardRoot.forward_relation_sound

end N41ForwardRoot
