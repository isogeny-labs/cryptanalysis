module

public import Init

namespace KernelMechanism

public def relationSum {G : Type} (zero : G) (add : G → G → G)
    (scale : Int → G → G) : List (Int × G) → G
  | [] => zero
  | (c, P) :: rest => add (scale c P) (relationSum zero add scale rest)

public theorem map_relation_sum {G H : Type}
    (zeroG : G) (addG : G → G → G) (scaleG : Int → G → G)
    (zeroH : H) (addH : H → H → H) (scaleH : Int → H → H)
    (φ : G → H)
    (map_zero : φ zeroG = zeroH)
    (map_add : ∀ x y, φ (addG x y) = addH (φ x) (φ y))
    (map_scale : ∀ c x, φ (scaleG c x) = scaleH c (φ x))
    (row : List (Int × G)) :
    φ (relationSum zeroG addG scaleG row) =
      relationSum zeroH addH scaleH (row.map fun pair => (pair.1, φ pair.2)) := by
  induction row with
  | nil => simpa [relationSum] using map_zero
  | cons term rest ih =>
      rcases term with ⟨c, P⟩
      simp only [relationSum, List.map_cons]
      rw [map_add, map_scale, ih]

public theorem verified_relation_annihilates {G H : Type}
    (zeroG : G) (addG : G → G → G) (scaleG : Int → G → G)
    (zeroH : H) (addH : H → H → H) (scaleH : Int → H → H)
    (φ : G → H)
    (map_zero : φ zeroG = zeroH)
    (map_add : ∀ x y, φ (addG x y) = addH (φ x) (φ y))
    (map_scale : ∀ c x, φ (scaleG c x) = scaleH c (φ x))
    (row : List (Int × G))
    (group_relation : relationSum zeroG addG scaleG row = zeroG) :
    relationSum zeroH addH scaleH (row.map fun pair => (pair.1, φ pair.2)) = zeroH := by
  rw [← map_relation_sum zeroG addG scaleG zeroH addH scaleH φ map_zero map_add map_scale row,
      group_relation, map_zero]

#print axioms map_relation_sum
#print axioms verified_relation_annihilates

end KernelMechanism
