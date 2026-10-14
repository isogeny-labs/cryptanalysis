import Std

/-! Exact Boolean form of the squarefree quadratic ideal used for the
    local reciprocal-coordinate families.  `parity` is the GF(2) linear
    equation and `quadratic` forbids every pair of nonzero coordinates. -/

namespace PartialIdeal

def parity (xs : List Bool) : Bool := xs.foldr Bool.xor false

def allZero (xs : List Bool) : Prop := ∀ b ∈ xs, b = false

def quadratic : List Bool → Prop
  | [] => True
  | b :: xs => quadratic xs ∧ (b = true → allZero xs)

def unit : List Bool → Prop
  | [] => False
  | b :: xs => if b then allZero xs else unit xs

theorem allZero_parity_false : ∀ xs, allZero xs → parity xs = false := by
  intro xs
  induction xs with
  | nil => intro _; rfl
  | cons b xs ih =>
    intro h
    have hb : b = false := h b (by simp)
    have ht : allZero xs := by
      intro c hc
      exact h c (by simp [hc])
    change b.xor (parity xs) = false
    simp [hb, ih ht]

theorem allZero_quadratic : ∀ xs, allZero xs → quadratic xs := by
  intro xs
  induction xs with
  | nil => intro _; trivial
  | cons b xs ih =>
    intro hz
    have hb : b = false := hz b (by simp)
    have ht : allZero xs := by
      intro c hc
      exact hz c (by simp [hc])
    simpa [quadratic, hb] using ih ht

theorem quadratic_onehot : ∀ xs,
    (parity xs = true ∧ quadratic xs) ↔ unit xs := by
  intro xs
  induction xs with
  | nil => simp [parity, quadratic, unit]
  | cons b xs ih =>
    cases b with
    | false =>
      simpa [parity, quadratic, unit] using ih
    | true =>
      constructor
      · rintro ⟨hp, ⟨_, hz⟩⟩
        exact hz rfl
      · intro hz
        have hp : parity xs = false := allZero_parity_false xs hz
        have hq : quadratic xs := allZero_quadratic xs hz
        refine ⟨?_, ⟨hq, by intro _; exact hz⟩⟩
        change (true.xor (parity xs)) = true
        simp [hp]

#print axioms PartialIdeal.allZero_parity_false
#print axioms PartialIdeal.quadratic_onehot

end PartialIdeal
