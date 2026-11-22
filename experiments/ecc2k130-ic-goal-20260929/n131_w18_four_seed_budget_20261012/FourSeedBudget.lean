import JoinCoverage

/-! A fixed four-seed schedule is bounded by the two half-list sizes.
The numeric constants are the maximum audited signed W18 seed-family count
and the ECC2K-130 prime subgroup order. -/
namespace FourSeedBudget

def maxBucket : Nat := 133152
def subgroupOrder : Nat := 680564733841876926932320129493409985129
def tupleCap : Nat := maxBucket ^ 4
def halfCeilingCells : Nat := 1082551755296979644

theorem fixed_tuple_coverage {A B Q : Type}
    (left : List A) (right : List B) (output : A → B → Q)
    (hits : List Q) (hnodup : hits.Nodup)
    (hhit : ∀ q ∈ hits, ∃ a ∈ left, ∃ b ∈ right, output a b = q)
    (hleft : left.length ≤ maxBucket * maxBucket)
    (hright : right.length ≤ maxBucket * maxBucket) :
    hits.length ≤ tupleCap := by
  have h := JoinCoverage.distinct_successes_bound left right [()]
    (fun a b _ => output a b) hits hnodup
    (by
      intro q hq
      obtain ⟨a, ha, b, hb, heq⟩ := hhit q hq
      exact ⟨a, ha, b, hb, (), by simp, heq⟩)
  simp only [List.length_singleton, Nat.mul_one] at h
  have hprod : left.length * right.length ≤
      (maxBucket * maxBucket) * (maxBucket * maxBucket) :=
    Nat.mul_le_mul hleft hright
  have heq : (maxBucket * maxBucket) * (maxBucket * maxBucket) = tupleCap := by
    decide
  exact Nat.le_trans h (by simpa only [heq] using hprod)

structure Family (A B Q : Type) where
  left : List A
  right : List B
  output : A → B → Q

def familyOutcomes {A B Q : Type} (f : Family A B Q) : List Q :=
  JoinCoverage.outcomes f.left f.right [()] (fun a b _ => f.output a b)

private theorem family_length {A B Q : Type} (f : Family A B Q)
    (hl : f.left.length ≤ maxBucket * maxBucket)
    (hr : f.right.length ≤ maxBucket * maxBucket) :
    (familyOutcomes f).length ≤ tupleCap := by
  rw [familyOutcomes, JoinCoverage.outcomes_length]
  simp only [List.length_singleton, Nat.mul_one]
  have hp := Nat.mul_le_mul hl hr
  have heq : (maxBucket * maxBucket) * (maxBucket * maxBucket) = tupleCap := by
    decide
  simpa only [heq] using hp

private theorem schedule_length {A B Q : Type} (families : List (Family A B Q))
    (hsize : ∀ f ∈ families,
      f.left.length ≤ maxBucket * maxBucket ∧
      f.right.length ≤ maxBucket * maxBucket) :
    (families.flatMap familyOutcomes).length ≤ families.length * tupleCap := by
  induction families with
  | nil => simp
  | cons f rest ih =>
      have hf := hsize f (by simp)
      have ht : ∀ g ∈ rest,
          g.left.length ≤ maxBucket * maxBucket ∧
          g.right.length ≤ maxBucket * maxBucket := by
        intro g hg
        exact hsize g (by simp [hg])
      have hfirst := family_length f hf.1 hf.2
      have htail := ih ht
      simp only [List.flatMap_cons, List.length_append, List.length_cons, Nat.succ_mul]
      omega

theorem fixed_schedule_coverage {A B Q : Type}
    (families : List (Family A B Q)) (hits : List Q)
    (hnodup : hits.Nodup)
    (hsize : ∀ f ∈ families,
      f.left.length ≤ maxBucket * maxBucket ∧
      f.right.length ≤ maxBucket * maxBucket)
    (hhit : ∀ q ∈ hits, ∃ f ∈ families,
      ∃ a ∈ f.left, ∃ b ∈ f.right, f.output a b = q) :
    hits.length ≤ families.length * tupleCap := by
  have hsub : hits ⊆ families.flatMap familyOutcomes := by
    intro q hq
    obtain ⟨f, hf, a, ha, b, hb, heq⟩ := hhit q hq
    simp only [List.mem_flatMap]
    refine ⟨f, hf, ?_⟩
    rw [← heq]
    exact JoinCoverage.mem_outcomes (j := ()) ha hb (by simp)
  have hcount := List.Nodup.length_le_of_subset hnodup hsub
  exact Nat.le_trans hcount (schedule_length families hsize)

theorem half_ceiling_is_minimal :
    (halfCeilingCells - 1) * (2 * tupleCap) < subgroupOrder ∧
    subgroupOrder ≤ halfCeilingCells * (2 * tupleCap) := by
  decide

#print axioms FourSeedBudget.fixed_tuple_coverage
#print axioms FourSeedBudget.fixed_schedule_coverage
#print axioms FourSeedBudget.half_ceiling_is_minimal

end FourSeedBudget
