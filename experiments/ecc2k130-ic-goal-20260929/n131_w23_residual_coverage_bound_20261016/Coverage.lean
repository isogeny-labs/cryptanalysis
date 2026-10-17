import Std

namespace TargetOrbitCoverage

universe u v w

/-- Keep the last occurrence of every element. This is a structurally recursive
list representation of a finite image, independent of hash-table behavior. -/
def unique {α : Type u} [DecidableEq α] : List α → List α
  | [] => []
  | x :: xs => if x ∈ xs then unique xs else x :: unique xs

theorem unique_sublist {α : Type u} [DecidableEq α] (xs : List α) :
    (unique xs).Sublist xs := by
  induction xs with
  | nil => simp [unique]
  | cons x xs ih =>
      simp only [unique]
      split
      · exact ih.cons x
      · exact ih.cons_cons x

theorem unique_mem {α : Type u} [DecidableEq α] (a : α) (xs : List α) :
    a ∈ unique xs ↔ a ∈ xs := by
  induction xs with
  | nil => simp [unique]
  | cons x xs ih =>
      by_cases hx : x ∈ xs
      · simp [unique, hx, ih]
        intro h
        simpa [h] using hx
      · simp [unique, hx, ih]

theorem unique_nodup {α : Type u} [DecidableEq α] (xs : List α) :
    (unique xs).Nodup := by
  induction xs with
  | nil => simp [unique]
  | cons x xs ih =>
      by_cases hx : x ∈ xs
      · simpa [unique, hx] using ih
      · simp [unique, hx, ih, unique_mem]

/-- One orbit orientation and one free tuple produce one target value. -/
def emitted {T : Type u} {J : Type v} {G : Type w}
    (tuples : List T) (orientations : List J) (target : T → J → G) : List G :=
  match tuples with
  | [] => []
  | tuple :: tail => orientations.map (target tuple) ++ emitted tail orientations target

theorem emitted_length {T : Type u} {J : Type v} {G : Type w}
    (tuples : List T) (orientations : List J) (target : T → J → G) :
    (emitted tuples orientations target).length =
      tuples.length * orientations.length := by
  induction tuples with
  | nil => simp [emitted]
  | cons tuple tail ih =>
      simp [emitted, ih, Nat.succ_mul, Nat.add_comm]

/-- The exact distinct-target image of a fixed residual has at most one
element per labeled free tuple and orientation. -/
theorem distinct_target_bound {T : Type u} {J : Type v} {G : Type w}
    [DecidableEq G] (tuples : List T) (orientations : List J)
    (target : T → J → G) :
    (unique (emitted tuples orientations target)).length ≤
      tuples.length * orientations.length := by
  rw [← emitted_length tuples orientations target]
  exact (unique_sublist (emitted tuples orientations target)).length_le

#print axioms TargetOrbitCoverage.unique_mem
#print axioms TargetOrbitCoverage.unique_nodup
#print axioms TargetOrbitCoverage.distinct_target_bound

end TargetOrbitCoverage
