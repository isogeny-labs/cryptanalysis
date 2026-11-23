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
/-- Total positive deviation from uniform. For normalized finite probability
masses this equals total variation distance. -/
def excess [Fintype G] (q : G → ℚ) : ℚ :=
  ∑ x, max (q x - 1/2147505293) 0

/-- The accepted points may be any subset of the representable points.
The constant is the uniform point mass on the archived M31 group. -/
theorem conditionalHitBound [Fintype G] (f : Index → G) (s : Finset G)
    (hs : (s : Set G) ⊆ represented f) (q : G → ℚ) :
    ∑ x ∈ s, q x ≤ 166668000/2147505293 + excess q := by
  have hcard : s.card ≤ 166668000 := by
    simpa using (Set.ncard_le_ncard hs).trans (coverage_bound f)
  have hsum : ∑ x ∈ s, max (q x - 1/2147505293) 0 ≤ excess q := by
    apply Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ s)
    intro x _ _
    exact le_max_right _ _
  calc
    _ ≤ ∑ x ∈ s, (1/2147505293 + max (q x - 1/2147505293) 0) := by
      apply Finset.sum_le_sum
      intro x _
      linarith [le_max_left (q x - 1/2147505293) (0:ℚ)]
    _ ≤ _ := by
      rw [Finset.sum_add_distrib, Finset.sum_const, nsmul_eq_mul]
      have hc : (s.card : ℚ) ≤ 166668000 := by exact_mod_cast hcard
      linarith

/-- The history index can include a randomized choice made before the query.
Its weights sum to one. No independence between successive histories is needed. -/
theorem historyHitBound {H : Type*} [Fintype H] [Fintype G]
    (w : H → ℚ) (hw : ∀ h, 0 ≤ w h) (total : ∑ h, w h = 1)
    (f : H → Index → G) (s : H → Finset G)
    (hs : ∀ h, (s h : Set G) ⊆ represented (f h)) (q : H → G → ℚ) :
    ∑ h, w h * (∑ x ∈ s h, q h x) ≤
      166668000/2147505293 + ∑ h, w h * excess (q h) := by
  calc
    _ ≤ ∑ h, w h * (166668000/2147505293 + excess (q h)) :=
      Finset.sum_le_sum (fun h _ => mul_le_mul_of_nonneg_left
        (conditionalHitBound (f h) (s h) (hs h) (q h)) (hw h))
    _ = _ := by simp only [mul_add, Finset.sum_add_distrib, ← Finset.sum_mul, total, one_mul]

/-- Against the measured auxiliary coverage of 160361708 group points,
uniform coverage gain is strictly under 3.933 percent. Doubling its hit
rate requires mean conditional total variation of more than 7.1736 percent. -/
theorem fixtureLimits (hits bias : ℚ) (bound : hits ≤ 166668000/2147505293 + bias) :
    (bias = 0 → hits < (103933/100000)*(160361708/2147505293)) ∧
    (2*(160361708/2147505293) ≤ hits → 71736/1000000 < bias) := by
  constructor <;> intro h <;> linarith

theorem representedNeg (f : Index → G) (x : G) :
    -x ∈ represented f ↔ x ∈ represented f := by
  have flip (z : G) (hz : z ∈ represented f) : -z ∈ represented f := by
    obtain ⟨i,j,k,a,b,c,rfl⟩ := hz
    refine ⟨i,j,k,!a,!b,!c,?_⟩
    have hn (s : Bool) (u : G) : signed (!s) u = -signed s u := by
      cases s <;> simp [signed]
    rw [hn, hn, hn]
    abel
  exact ⟨fun h => by simpa using flip (-x) h, flip x⟩

/-- Both bases have sign-invariant acceptance. If routing flips between x
and its negative on every point where the two bases disagree, total accepted
coverage is exactly the arithmetic mean. Agreement points need no routing
condition, including the identity. The permutation generalizes negation. -/
theorem signRouteMean {X : Type*} [Fintype X] (e : X ≃ X)
    (a b : X → ℕ) (route : X → Bool)
    (ha : ∀ x, a (e x) = a x) (hb : ∀ x, b (e x) = b x)
    (flip : ∀ x, a x ≠ b x → route (e x) = !(route x)) :
    2 * (∑ x, if route x then a x else b x) = (∑ x, a x) + ∑ x, b x := by
  let v (x : X) := if route x then a x else b x
  have h (x : X) : v x + v (e x) = a x + b x := by
    unfold v
    rw [ha, hb]
    by_cases hab : a x = b x
    · simp [hab]
    · rw [flip x hab]
      cases route x <;> simp [add_comm]
  change 2 * (∑ x, v x) = _
  calc
    _ = (∑ x, v x) + ∑ x, v (e x) := by rw [e.sum_comp v, two_mul]
    _ = ∑ x, (a x+b x) := by rw [← Finset.sum_add_distrib]; exact Finset.sum_congr rfl (fun x _ => h x)
    _ = _ := Finset.sum_add_distrib

example (routed : ℕ) (h : 2*routed = 160361708+160352874) : routed = 160357291 := by omega

end M31TripleCoverage
