import Std

/-! A target-independent two-half join with `L` stored left states,
`R` right probes, and `J` tested automorphism images reaches at most
`L*R*J` distinct public targets. The cofactor and automorphism maps
are explicit in `orbit_join_coverage_bound`. -/
namespace JoinCoverage

universe u v w x

private theorem flatMap_length_const {A : Type u} {B : Type v}
    (xs : List A) (f : A → List B) (n : Nat)
    (hlen : ∀ a, (f a).length = n) :
    (xs.flatMap f).length = xs.length * n := by
  induction xs with
  | nil => simp
  | cons a rest ih =>
      simp only [List.flatMap_cons, List.length_append, hlen a,
        List.length_cons, ih, Nat.succ_mul]
      omega

def outcomes {A : Type u} {B : Type v} {J : Type w} {Q : Type x}
    (left : List A) (right : List B) (rotations : List J)
    (output : A → B → J → Q) : List Q :=
  left.flatMap fun a =>
    right.flatMap fun b =>
      rotations.map fun j => output a b j

theorem outcomes_length {A : Type u} {B : Type v} {J : Type w} {Q : Type x}
    (left : List A) (right : List B) (rotations : List J)
    (output : A → B → J → Q) :
    (outcomes left right rotations output).length =
      left.length * right.length * rotations.length := by
  unfold outcomes
  have hright (a : A) :
      (right.flatMap fun b => rotations.map fun j => output a b j).length =
        right.length * rotations.length := by
    apply flatMap_length_const
    intro b
    simp
  rw [flatMap_length_const left _ (right.length * rotations.length) hright]
  simp [Nat.mul_assoc]

theorem mem_outcomes {A : Type u} {B : Type v} {J : Type w} {Q : Type x}
    {left : List A} {right : List B} {rotations : List J}
    {output : A → B → J → Q} {a : A} {b : B} {j : J}
    (ha : a ∈ left) (hb : b ∈ right) (hj : j ∈ rotations) :
    output a b j ∈ outcomes left right rotations output := by
  simp only [outcomes, List.mem_flatMap, List.mem_map]
  exact ⟨a, ha, b, hb, j, hj, rfl⟩

theorem distinct_successes_bound
    {A : Type u} {B : Type v} {J : Type w} {Q : Type x}
    (left : List A) (right : List B) (rotations : List J)
    (output : A → B → J → Q) (hits : List Q)
    (hnodup : hits.Nodup)
    (hhit : ∀ q ∈ hits, ∃ a ∈ left, ∃ b ∈ right,
      ∃ j ∈ rotations, output a b j = q) :
    hits.length ≤ left.length * right.length * rotations.length := by
  have hsub : hits ⊆ outcomes left right rotations output := by
    intro q hq
    obtain ⟨a, ha, b, hb, j, hj, heq⟩ := hhit q hq
    rw [← heq]
    exact mem_outcomes ha hb hj
  calc
    hits.length ≤ (outcomes left right rotations output).length :=
      List.Nodup.length_le_of_subset hnodup hsub
    _ = left.length * right.length * rotations.length :=
      outcomes_length left right rotations output

theorem orbit_join_coverage_bound
    {P : Type u} {Q : Type v} {J : Type w}
    (left right : List P) (rotations : List J)
    (add : P → P → P) (cofactor : P → Q)
    (frob undo : J → Q → Q)
    (hundo : ∀ j q, undo j (frob j q) = q)
    (hits : List Q) (hnodup : hits.Nodup)
    (hhit : ∀ q ∈ hits, ∃ a ∈ left, ∃ b ∈ right,
      ∃ j ∈ rotations, cofactor (add a b) = frob j q) :
    hits.length ≤ left.length * right.length * rotations.length := by
  apply distinct_successes_bound left right rotations
    (fun a b j => undo j (cofactor (add a b))) hits hnodup
  intro q hq
  obtain ⟨a, ha, b, hb, j, hj, heq⟩ := hhit q hq
  exact ⟨a, ha, b, hb, j, hj, by rw [heq, hundo]⟩

#print axioms JoinCoverage.orbit_join_coverage_bound

end JoinCoverage
