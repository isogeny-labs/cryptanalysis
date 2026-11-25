import PointTriangles
import TriangleTrace

namespace TriangleBudget
open PointTriangles

abbrev Triple := P × P × P

def weight (H : Matrix P L ℤ) (t : Triple) : ℤ :=
  let G := H * H.transpose
  G t.1 t.2.1 * G t.2.1 t.2.2 * G t.2.2 t.1

def positive (H : Matrix P L ℤ) :=
  ((triangleSet .cycle).filter (fun t => weight H t = 1)).card

variable (H : Matrix P L ℤ) (outside : ∀ a l, onLine a l = false → H a l = 0)
    (unit : ∀ a l, onLine a l = true → H a l ^ 2 = 1)

include outside unit in
private theorem pair_square {a b : P} (h : a ≠ b) :
    ((H * H.transpose) a b)^2 = (if (joinLine a b).isSome then 1 else 0) := by
  rw [overlap H outside h]
  cases he : joinLine a b with
  | none => simp
  | some k =>
    obtain ⟨ha,hb⟩ := (join_exact a b h k).mp he
    simp [mul_pow, unit _ _ ha, unit _ _ hb]

include outside unit in
private theorem weight_square {a b c : P} (ab : a < b) (bc : b < c) :
    weight H (a,b,c)^2 = (if classify a b c = .absent then 0 else 1) := by
  unfold weight
  simp only [mul_pow, pair_square H outside unit ab.ne, pair_square H outside unit bc.ne,
    pair_square H outside unit (ab.trans bc).ne.symm]
  unfold classify
  cases joinLine a b <;> cases joinLine b c <;> cases joinLine c a <;>
    simp <;> (split_ifs <;> decide)

attribute [local irreducible] classify joinLine weight

include outside unit in
set_option linter.constructorNameAsVariable false in
theorem ordered_budget :
    (∑ t ∈ Finset.univ.filter (fun t : Triple => t.1 < t.2.1 ∧ t.2.1 < t.2.2), weight H t)
      = 3808 + 2 * (positive H : ℤ) - 31360 := by
  have splitSum :
      (∑ t ∈ Finset.univ.filter (fun t : Triple => t.1 < t.2.1 ∧ t.2.1 < t.2.2), weight H t)
        = (∑ _t ∈ triangleSet .same, (1 : ℤ)) + ∑ t ∈ triangleSet .cycle, weight H t := by
    simp only [triangleSet, Finset.sum_filter, ← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    rintro ⟨a,b,c⟩ _
    by_cases ab : a < b <;> by_cases bc : b < c <;> simp [ab,bc]
    cases h : classify a b c with
    | same => simpa [h, weight] using same_weight H outside unit ab bc h
    | cycle => simp
    | absent =>
      have hw := weight_square H outside unit ab bc
      simp [h] at hw ⊢
      exact hw
    | mixed =>
      have hz : triangleSet .mixed = ∅ := Finset.card_eq_zero.mp partition_sizes.2.2.2
      have hm : (a,b,c) ∈ triangleSet .mixed := by simp [triangleSet,ab,bc,h]
      simp [hz] at hm
  have signedRows (t : Triple) (ht : t ∈ triangleSet .cycle) :
      weight H t = 1 ∨ weight H t = -1 := by
    simp only [triangleSet, Finset.mem_filter, Finset.mem_univ, true_and] at ht
    have hw := weight_square H outside unit ht.1 ht.2.1
    rw [ht.2.2] at hw
    exact sq_eq_one_iff.mp (by simpa using hw)
  rw [splitSum, TriangleTrace.signed_sum (triangleSet .cycle) (weight H) signedRows]
  simp only [Finset.sum_const, nsmul_eq_mul, mul_one, partition_sizes.1, partition_sizes.2.1]
  unfold positive
  push_cast
  ring

#print axioms ordered_budget
end TriangleBudget
