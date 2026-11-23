import Mathlib.Data.Set.Card
import Mathlib.Data.Sym.NatCard
import Mathlib.Algebra.BigOperators.Group.Multiset.Basic
import Mathlib.Tactic

namespace M31TripleCoverage

abbrev Index := Fin 500
abbrev Form := Sym Index 3 ⊕ (Σ i : Index, Sym {j : Index // j ≠ i} 2) ⊕ Index

variable {G : Type*} [AddCommGroup G]

def eval (f : Index → G) : Form → G
  | .inl s => (s.val.map f).sum
  | .inr (.inl ⟨i, s⟩) => (s.val.map (fun j => f j.val)).sum - f i
  | .inr (.inr i) => f i

def signed (b : Bool) (x : G) := if b then -x else x

private theorem allPos (f : Index → G) (i j k : Index) :
    ∃ s, eval f s = f i + f j + f k := by
  refine ⟨.inl ⟨{i,j,k}, by simp⟩, ?_⟩
  simp [eval, add_assoc]

private theorem mixed (f : Index → G) (i j k : Index) :
    ∃ s, eval f s = f i + f j - f k := by
  by_cases hi : i = k
  · exact ⟨.inr (.inr j), by simp [eval, hi]⟩
  by_cases hj : j = k
  · exact ⟨.inr (.inr i), by simp [eval, hj]⟩
  let a : {x : Index // x ≠ k} := ⟨i, hi⟩
  let b : {x : Index // x ≠ k} := ⟨j, hj⟩
  exact ⟨.inr (.inl ⟨k, ⟨{a,b}, by simp⟩⟩), by simp [eval, a, b]⟩

def value (f : Index → G) (code : Bool × Form) := signed code.1 (eval f code.2)

theorem covers (f : Index → G) (i j k : Index) (a b c : Bool) :
    ∃ code, value f code = signed a (f i) + signed b (f j) + signed c (f k) := by
  cases a <;> cases b <;> cases c
  · obtain ⟨s, h⟩ := allPos f i j k
    exact ⟨(false, s), by simp [value, signed, h]⟩
  · obtain ⟨s, h⟩ := mixed f i j k
    exact ⟨(false, s), by simp [value, signed, h]; abel⟩
  · obtain ⟨s, h⟩ := mixed f i k j
    exact ⟨(false, s), by simp [value, signed, h]; abel⟩
  · obtain ⟨s, h⟩ := mixed f j k i
    exact ⟨(true, s), by simp [value, signed, h]; abel⟩
  · obtain ⟨s, h⟩ := mixed f j k i
    exact ⟨(false, s), by simp [value, signed, h]; abel⟩
  · obtain ⟨s, h⟩ := mixed f i k j
    exact ⟨(true, s), by simp [value, signed, h]; abel⟩
  · obtain ⟨s, h⟩ := mixed f i j k
    exact ⟨(true, s), by simp [value, signed, h]; abel⟩
  · obtain ⟨s, h⟩ := allPos f i j k
    exact ⟨(true, s), by simp [value, signed, h]; abel⟩

theorem code_count : Nat.card (Bool × Form) = 166668000 := by
  have count (i : Index) : Nat.card {j : Index // j ≠ i} = 499 := by
    rw [Nat.card_eq_fintype_card, Fintype.card_subtype_compl fun j : Index => j = i]
    simp [Index]
  have cb : Nat.card Bool = 2 := by rw [Nat.card_eq_fintype_card, Fintype.card_bool]
  simp only [Form, Nat.card_prod, cb, Nat.card_sum, Nat.card_sigma,
    Sym.natCard_sym_eq_choose, count, Nat.card_fin, Finset.sum_const,
    Finset.card_univ, Fintype.card_fin, smul_eq_mul]
  simp only [Nat.choose_eq_descFactorial_div_factorial]
  decide

/-- All group elements representable by exactly three signed basis terms,
allowing repeated indices and cancellations. -/
def represented (f : Index → G) : Set G :=
  {x | ∃ i j k a b c, x = signed a (f i) + signed b (f j) + signed c (f k)}

theorem coverage_bound (f : Index → G) : (represented f).ncard ≤ 166668000 := by
  classical
  have sub : represented f ⊆ value f '' Set.univ := by
    rintro x ⟨i,j,k,a,b,c,rfl⟩
    obtain ⟨s, h⟩ := covers f i j k a b c
    exact ⟨s, Set.mem_univ _, h⟩
  calc
    _ ≤ (value f '' Set.univ).ncard := Set.ncard_le_ncard sub
    _ ≤ (Set.univ : Set (Bool × Form)).ncard := Set.ncard_image_le
    _ = 166668000 := by rw [Set.ncard_univ, code_count]

#print axioms coverage_bound
end M31TripleCoverage
