import Mathlib

namespace M31Heap
variable {F : Type*} [Field F]

def frontier (original : ℕ → F) (i k : ℕ) : F :=
  if k < 2*i then (original k)⁻¹ else original k

def advance (state : ℕ → F) (i k : ℕ) : F :=
  if k = 2*i then state i * state (2*i+1)
  else if k = 2*i+1 then state i * state (2*i)
  else state k

theorem frontier_step (original : ℕ → F) (i : ℕ) (hi : 0 < i)
    (hprod : original i = original (2*i) * original (2*i+1))
    (hl : original (2*i) ≠ 0) (hr : original (2*i+1) ≠ 0) :
    advance (frontier original i) i = frontier original (i+1) := by
  funext k
  have parent : i < 2*i := by omega
  by_cases left : k = 2*i
  · subst k
    simp only [advance, ite_true, eq_self, frontier, if_pos parent, hprod,
      if_neg (show ¬(2*i+1 < 2*i) by omega), if_pos (show 2*i < 2*(i+1) by omega)]
    field_simp
  by_cases right : k = 2*i+1
  · subst k
    simp only [advance, if_neg left, ite_true, eq_self, frontier, if_pos parent, hprod,
      lt_irrefl, if_false, if_pos (show 2*i+1 < 2*(i+1) by omega)]
    field_simp
  have eqv : k < 2*(i+1) ↔ k < 2*i := by omega
  simp [advance, frontier, left, right, eqv]
/-- Apply the downward sweep in increasing parent index, starting with an inverted root.
Index zero is unused. -/
def sweep (original : ℕ → F) : ℕ → ℕ → F
  | 0 => frontier original 1
  | j+1 => advance (sweep original j) (j+1)

theorem sweep_frontier (original : ℕ → F) (n : ℕ)
    (hprod : ∀ i, 0 < i → i < n → original i = original (2*i) * original (2*i+1))
    (hnz : ∀ k, 0 < k → k < 2*n → original k ≠ 0)
    (j : ℕ) (hj : j < n) : sweep original j = frontier original (j+1) := by
  induction j with
  | zero => rfl
  | succ j ih =>
    rw [sweep, ih (by omega)]
    exact frontier_step original _ (by omega) (hprod _ (by omega) hj)
      (hnz _ (by omega) (by omega)) (hnz _ (by omega) (by omega))

theorem leaf_inverse (original : ℕ → F) (n k : ℕ) (hleaf : n ≤ k) (hend : k < 2*n)
    (hprod : ∀ i, 0 < i → i < n → original i = original (2*i) * original (2*i+1))
    (hnz : ∀ k, 0 < k → k < 2*n → original k ≠ 0) :
    sweep original (n-1) k = (original k)⁻¹ := by
  rw [sweep_frontier original n hprod hnz _ (by omega)]
  exact if_pos (by omega)


/-- Build the product heap by visiting parents from n-1 down to 1. -/
def build (input : ℕ → F) (n : ℕ) : ℕ → ℕ → F
  | 0 => input
  | j+1 => fun k =>
    let prev := build input n j
    let i := n-(j+1)
    if k = i then prev (2*i) * prev (2*i+1) else prev k

theorem build_spec (input : ℕ → F) (n : ℕ)
    (hleaves : ∀ k, n ≤ k → k < 2*n → input k ≠ 0)
    (j : ℕ) (hj : j < n) :
    (∀ k, n ≤ k → build input n j k = input k) ∧
    (∀ k, n-j ≤ k → k < 2*n → build input n j k ≠ 0) ∧
    (∀ k, n-j ≤ k → k < n → build input n j k =
      build input n j (2*k) * build input n j (2*k+1)) := by
  induction j with
  | zero =>
    refine ⟨fun _ _ => rfl, ?_, ?_⟩
    · simpa only [Nat.sub_zero, build] using hleaves
    · intro k hk hk'
      omega
  | succ j ih =>
    obtain ⟨leaves, nz, parents⟩ := ih (by omega)
    refine ⟨?_, ?_, ?_⟩
    · intro k hk
      simpa only [build, if_neg (show k ≠ n-(j+1) by omega)] using leaves k hk
    · intro k hk hend
      by_cases fresh : k = n-(j+1)
      · subst k
        simp only [build]
        exact mul_ne_zero (nz _ (by omega) (by omega)) (nz _ (by omega) (by omega))
      · simpa only [build, if_neg fresh] using nz k (by omega) hend
    · intro k hk hend
      have l : 2*k ≠ n-(j+1) := by omega
      have r : 2*k+1 ≠ n-(j+1) := by omega
      by_cases fresh : k = n-(j+1)
      · subst k
        simp [build, l, r]
      · simpa only [build, if_neg fresh, if_neg l, if_neg r] using parents k (by omega) hend

/-- The two heap loops compose using only nonzero leaf inputs. -/
theorem built_leaf_inverse (input : ℕ → F) (n k : ℕ) (hk : n ≤ k) (hend : k < 2*n)
    (hleaves : ∀ t, n ≤ t → t < 2*n → input t ≠ 0) :
    sweep (build input n (n-1)) (n-1) k = (input k)⁻¹ := by
  obtain ⟨leaves, nz, parents⟩ := build_spec input n hleaves (n-1) (by omega)
  rw [leaf_inverse _ n k hk hend (fun i hi h => parents i (by omega) h)
      (fun i hi h => nz i (by omega) h), leaves k hk]

/-- Replace zero residues by one during the product pass, then restore the zero outputs. -/
theorem masked_leaf_inverse [DecidableEq F] (input : ℕ → F) (n k : ℕ)
    (hk : n ≤ k) (hend : k < 2*n) :
    (if input k = 0 then 0 else
      sweep (build (fun t => if input t = 0 then 1 else input t) n (n-1)) (n-1) k)
      = (input k)⁻¹ := by
  rw [built_leaf_inverse _ n k hk hend (by
    intro t _ _
    by_cases h : input t = 0 <;> simp [h])]
  by_cases h : input k = 0 <;> simp [h]

end M31Heap
