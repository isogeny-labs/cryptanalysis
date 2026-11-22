import Init

namespace XedniAffineCoset

private theorem sum_map_add {α : Type} (xs : List α) (f g : α → Int) :
    (xs.map (fun x => f x + g x)).sum = (xs.map f).sum + (xs.map g).sum := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons, ih]
    ac_rfl

private theorem sum_map_mul (xs : List α) (f : α → Int) (c : Int) :
    (xs.map (fun x => c * f x)).sum = c * (xs.map f).sum := by
  induction xs with
  | nil => simp
  | cons x xs ih =>
    simp only [List.map_cons, List.sum_cons, ih, Int.mul_add]

def dot {n : Nat} (a b : Fin n → Int) : Int :=
  ((List.finRange n).map (fun j => a j * b j)).sum

def linearCombination {n : Nat} : List (Int × (Fin n → Int)) → Fin n → Int
  | [] => fun _ => 0
  | (c, d) :: rest => fun j => c * d j + linearCombination rest j

def candidate {n : Nat} (u : Fin n → Int)
    (terms : List (Int × (Fin n → Int))) : Fin n → Int :=
  fun j => u j + linearCombination terms j

private theorem dot_add {n : Nat} (row a b : Fin n → Int) :
    dot row (fun j => a j + b j) = dot row a + dot row b := by
  simp only [dot, Int.mul_add]
  exact sum_map_add (List.finRange n) (fun j => row j * a j) (fun j => row j * b j)

private theorem dot_scale {n : Nat} (row d : Fin n → Int) (c : Int) :
    dot row (fun j => c * d j) = c * dot row d := by
  simp only [dot]
  have h : (List.finRange n).map (fun j => row j * (c * d j)) =
      (List.finRange n).map (fun j => c * (row j * d j)) := by
    apply List.map_congr_left
    intro j hj
    ac_rfl
  rw [h]
  exact sum_map_mul (List.finRange n) (fun j => row j * d j) c

private theorem dot_zero {n : Nat} (row : Fin n → Int) :
    dot row (fun _ => 0) = 0 := by
  have sum_zeros (xs : List (Fin n)) :
      (xs.map (fun _ => (0 : Int))).sum = 0 := by
    induction xs with
    | nil => simp
    | cons x xs ih => simp [ih]
  simp only [dot, Int.mul_zero]
  exact sum_zeros (List.finRange n)

private theorem dot_combination_zero {n : Nat} (row : Fin n → Int)
    (terms : List (Int × (Fin n → Int)))
    (h : ∀ term ∈ terms, dot row term.2 = 0) :
    dot row (linearCombination terms) = 0 := by
  induction terms with
  | nil => simpa [linearCombination] using dot_zero row
  | cons term rest ih =>
    have hh : dot row term.2 = 0 := h term (by simp)
    have ht : ∀ t ∈ rest, dot row t.2 = 0 := by
      intro t ht
      exact h t (by simp [ht])
    cases term with
    | mk c d =>
      simp only [linearCombination]
      rw [dot_add, dot_scale, hh, Int.mul_zero, ih ht, Int.zero_add]

private theorem combination_divisible {n : Nat} (q : Int)
    (terms : List (Int × (Fin n → Int)))
    (h : ∀ term ∈ terms, ∀ j, q ∣ term.2 j) (j : Fin n) :
    q ∣ linearCombination terms j := by
  induction terms with
  | nil => simp [linearCombination]
  | cons term rest ih =>
    have hd : q ∣ term.2 j := h term (by simp) j
    have ht : ∀ t ∈ rest, ∀ k, q ∣ t.2 k := by
      intro t ht k
      exact h t (by simp [ht]) k
    rcases hd with ⟨z, hz⟩
    cases term with
    | mk c d =>
      have hd' : d j = q * z := by simpa using hz
      simp only [linearCombination]
      apply Int.dvd_add
      · refine ⟨z * c, ?_⟩
        calc
          c * d j = c * (q * z) := by rw [hd']
          _ = q * (z * c) := by ac_rfl
      · exact ih ht

/-- Any integer combination of feasible directions is again feasible. This
is the algebraic closure needed when a lattice basis is changed by integral
row operations; the Rust LLL implementation is audited separately. -/
theorem direction_span_closed {n : Nat}
    (terms : List (Int × (Fin n → Int))) (rows : List (Fin n → Int))
    (q : Int) (_hq : 0 < q)
    (hKernel : ∀ row ∈ rows, ∀ term ∈ terms, dot row term.2 = 0)
    (hCongruence : ∀ term ∈ terms, ∀ j, term.2 j % q = 0) :
    (∀ row ∈ rows, dot row (linearCombination terms) = 0) ∧
    (∀ j, linearCombination terms j % q = 0) := by
  constructor
  · intro row hr
    exact dot_combination_zero row terms (hKernel row hr)
  · intro j
    apply Int.emod_eq_zero_of_dvd
    apply combination_divisible q terms
    · intro term ht k
      exact Int.dvd_iff_emod_eq_zero.mpr (hCongruence term ht k)

/-- Every affine candidate formed from accepted directions preserves all exact
incidence rows and the coefficient residue class. The list of terms is the
mathematical image of the Rust `basis.iter().zip(coefficients)` loop. -/
theorem candidate_preserves_divisibility {n : Nat} (u : Fin n → Int)
    (terms : List (Int × (Fin n → Int))) (rows : List (Fin n → Int))
    (q : Int) (_hq : 0 < q)
    (hKernel : ∀ row ∈ rows, ∀ term ∈ terms, dot row term.2 = 0)
    (hCongruence : ∀ term ∈ terms, ∀ j, q ∣ term.2 j) :
    (∀ row ∈ rows, dot row (candidate u terms) = dot row u) ∧
    (∀ j, q ∣ candidate u terms j - u j) := by
  constructor
  · intro row hr
    unfold candidate
    rw [dot_add, dot_combination_zero row terms (hKernel row hr), Int.add_zero]
  · intro j
    change q ∣ u j + linearCombination terms j - u j
    have heq : u j + linearCombination terms j - u j =
        linearCombination terms j := by omega
    rw [heq]
    exact combination_divisible q terms hCongruence j

#print axioms candidate_preserves_divisibility
#print axioms direction_span_closed

/-- This is the form tested by the Rust certifier: every exact incidence row
stays fixed and every coefficient difference has zero remainder modulo `q`. -/
theorem candidate_preserves {n : Nat} (u : Fin n → Int)
    (terms : List (Int × (Fin n → Int))) (rows : List (Fin n → Int))
    (q : Int) (hq : 0 < q)
    (hKernel : ∀ row ∈ rows, ∀ term ∈ terms, dot row term.2 = 0)
    (hCongruence : ∀ term ∈ terms, ∀ j, term.2 j % q = 0) :
    (∀ row ∈ rows, dot row (candidate u terms) = dot row u) ∧
    (∀ j, (candidate u terms j - u j) % q = 0) := by
  have hDiv : ∀ term ∈ terms, ∀ j, q ∣ term.2 j := by
    intro term ht j
    exact Int.dvd_iff_emod_eq_zero.mpr (hCongruence term ht j)
  obtain ⟨hExact, hResidue⟩ :=
    candidate_preserves_divisibility u terms rows q hq hKernel hDiv
  exact ⟨hExact, fun j => Int.emod_eq_zero_of_dvd (hResidue j)⟩

#print axioms candidate_preserves
end XedniAffineCoset
