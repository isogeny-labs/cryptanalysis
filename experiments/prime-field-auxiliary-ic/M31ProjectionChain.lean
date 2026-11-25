import Mathlib

namespace M31ProjectionChain

/-- Previous exponents are m :: tail, with m the largest. A multiplication
can introduce the sum of any two available exponents, including equal ones. -/
inductive Reach (target : ℕ) : ℕ → ℕ → List ℕ → Prop
  | done (fuel tail) : Reach target fuel target tail
  | step {fuel m tail a b} (ha : a ∈ m :: tail) (hb : b ∈ m :: tail)
      (grow : m < a+b) (next : Reach target fuel (a+b) (m::tail)) :
      Reach target (fuel+1) m tail

theorem ceiling {t fuel m tail} (r : Reach t fuel m tail)
    (largest : ∀ x ∈ tail, x ≤ m) : t ≤ m * 2^fuel := by
  induction r with
  | done => exact Nat.le_mul_of_pos_right _ (pow_pos (by decide) _)
  | @step fuel m tail a b ha hb grow next ih =>
    have bound (x) (hx : x ∈ m :: tail) : x ≤ m := by
      rcases List.mem_cons.mp hx with rfl | h
      · rfl
      · exact largest _ h
    have h := ih (fun x hx => (bound x hx).trans grow.le)
    calc
      _ ≤ (a+b)*2^fuel := h
      _ ≤ (m+m)*2^fuel := Nat.mul_le_mul_right _ (Nat.add_le_add (bound _ ha) (bound _ hb))
      _ = m*2^(fuel+1) := by ring

def search (t : ℕ) : ℕ → ℕ → List ℕ → Bool
  | 0, m, _ => decide (m = t)
  | n+1, m, tail =>
    decide (m = t) || (decide (t ≤ m*2^(n+1)) &&
      (m::tail).any fun a => (m::tail).any fun b =>
        decide (m < a+b) && search t n (a+b) (m::tail))

theorem complete {t n m tail} (r : Reach t n m tail)
    (largest : ∀ x ∈ tail, x ≤ m) : search t n m tail = true := by
  induction r with
  | done n tail => cases n <;> simp [search]
  | @step n m tail a b ha hb grow next ih =>
    have lim := ceiling (Reach.step ha hb grow next) largest
    simp only [search, Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq, List.any_eq_true]
    refine Or.inr ⟨lim,a,ha,b,hb,grow,ih ?_⟩
    intro x hx
    rcases List.mem_cons.mp hx with rfl | h
    · exact grow.le
    · exact (largest _ h).trans grow.le

theorem uniqueExponent {t : ℕ} (chain : Reach t 16 1 [])
    (odd : t % 2 = 1) (imageSize : 2147483646 / Nat.gcd t 2147483646 ≤ 65534) :
    t = 32769 := by
  have lim := ceiling chain (by simp)
  have mem : t ∈ (List.range 65537).filter (fun e =>
      decide (e % 2 = 1 ∧ 2147483646 / Nat.gcd e 2147483646 ≤ 65534)) := by
    apply List.mem_filter.mpr
    exact ⟨List.mem_range.mpr (by norm_num at lim; omega), by simp [odd,imageSize]⟩
  have candidates : ((List.range 65537).filter fun e =>
      decide (e % 2 = 1 ∧ 2147483646 / Nat.gcd e 2147483646 ≤ 65534)) =
      [32769,34881,42129,49981,51491] := by native_decide
  rw [candidates] at mem
  have found := complete chain (by simp)
  have rejected : [34881,42129,49981,51491].all (fun e => !(search e 16 1 [])) = true := by
    native_decide
  rcases List.mem_cons.mp mem with h | h
  · exact h
  · have bad := List.all_eq_true.mp rejected t h
    simp [found] at bad

theorem sound {t n m tail} (found : search t n m tail = true) : Reach t n m tail := by
  induction n generalizing m tail with
  | zero =>
    have eq : m = t := by simpa [search] using found
    subst m
    exact .done _ _
  | succ n ih =>
    simp only [search, Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq, List.any_eq_true] at found
    rcases found with rfl | ⟨_,a,ha,b,hb,grow,rest⟩
    · exact .done _ _
    · exact .step ha hb grow (ih rest)

theorem attained : Reach 32769 16 1 [] :=
  sound (by native_decide : search 32769 16 1 [] = true)

theorem fifteenInsufficient : ¬ Reach 32769 15 1 [] := by
  intro chain
  have h := ceiling chain (by simp)
  norm_num at h

end M31ProjectionChain
