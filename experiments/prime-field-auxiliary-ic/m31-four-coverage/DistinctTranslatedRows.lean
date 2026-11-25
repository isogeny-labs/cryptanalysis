import TranslatedMarginals

namespace M31DistinctTranslatedRows
open M31TranslatedMarginals

variable {G : Type*} [AddCommGroup G] [Fintype G] [DecidableEq G]

/-- With path translated by -h, the row represented by ±x occurs if
either h+x or h-x is in the set of distinct path positions. -/
def seen (path : Finset G) (x h : G) : ℕ :=
  if h+x ∈ path ∨ h+(-x) ∈ path then 1 else 0

theorem one_row (path : Finset G) (x : G) :
    (∑ h : G, seen path x h) +
      (path.filter (fun y => y + (-x-x) ∈ path)).card = 2*path.card := by
  rw [← joint path x (-x), ← Finset.sum_add_distrib]
  calc
    _ = ∑ h : G, ((if h+x ∈ path then 1 else 0 : ℕ) +
                   (if h+(-x) ∈ path then 1 else 0)) := by
      apply Finset.sum_congr rfl
      intro h _
      by_cases a : h+x ∈ path <;> by_cases b : h+(-x) ∈ path <;> simp [seen, a, b]
    _ = _ := by rw [Finset.sum_add_distrib, single, single, Nat.two_mul]

/-- Take one representative for each row, and divide by the group size to
obtain the uniform-shift expectation. -/
theorem all_rows (path reps : Finset G) :
    (∑ h : G, ∑ x ∈ reps, seen path x h) +
      (∑ x ∈ reps, (path.filter (fun y => y + (-x-x) ∈ path)).card) =
      reps.card * (2 * path.card) := by
  rw [Finset.sum_comm, ← Finset.sum_add_distrib]
  simp_rw [one_row]
  simp

end M31DistinctTranslatedRows
