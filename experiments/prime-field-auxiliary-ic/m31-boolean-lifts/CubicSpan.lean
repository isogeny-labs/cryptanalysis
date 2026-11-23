import Mathlib.LinearAlgebra.Span.Basic

namespace M31CubicSpan

private def p : Nat := 2147483647

/-- In each degree bound, append terms containing the new highest bit after the
terms omitting it. The appended values come from the previous degree bound. -/
private def features (x : Nat) : Nat := Id.run do
  let mut a := 1
  let mut b := 1
  let mut c := 1
  let mut wa := 1
  let mut wb := 1
  let mut wc := 1
  for i in [:31] do
    if x.testBit i then
      c := c ||| (b <<< wc)
      b := b ||| (a <<< wb)
      a := a ||| (1 <<< wa)
    wc := wc + wb
    wb := wb + wa
    wa := wa + 1
  return c

private def lifts (x : Nat) : Bool := Id.run do
  let rhs := (x*x*x + 2*x + 14) % p
  let mut y := rhs
  for _ in [:29] do y := (y*y) % p
  return (y*y) % p == rhs

/-- Eliminate the highest remaining column. Each nonzero XOR step strictly
lowers this column, so 4992 steps suffice. -/
private def residual (ps : Array Nat) : Nat → Nat → Nat
  | 0, row => row
  | fuel+1, row =>
    if row = 0 then 0 else
      match ps[row.log2]? with
      | none => row
      | some pivot =>
        if pivot = 0 then row else residual ps fuel (row ^^^ pivot)

private def build (label : Bool) : Nat → Nat → Array Nat → Array Nat
  | 0, _, ps => ps
  | fuel+1, x, ps =>
    let y := (1103515245*x + 12345) % (2^31)
    let next := if y < p ∧ lifts y = label then
      let r := residual ps 4992 (features y)
      if r = 0 then ps else ps.setIfInBounds r.log2 r
    else ps
    build label fuel y next

private def basis (label : Bool) := build label 9989 1 (Array.replicate 4992 0)
private def rankFor (label : Bool) := ((basis label).filter (· != 0)).size

theorem both_eliminations_full : rankFor true = 4992 ∧ rankFor false = 4992 := by
  native_decide

private theorem residual_preserves (f : Nat → Bool) (hx : ∀ a b, f (a ^^^ b) = (f a ^^ f b))
    (ps : Array Nat) (hp : ∀ v ∈ ps, f v = false) (fuel row : Nat) :
    f (residual ps fuel row) = f row := by
  induction fuel generalizing row with
  | zero => rfl
  | succ n ih =>
    simp only [residual]
    split
    · rename_i h; simp [h]
    · split
      · rfl
      · rename_i v hv
        split
        · rfl
        · rw [ih, hx, hp v (Array.mem_of_getElem? hv), Bool.xor_false]

private theorem build_preserves (f : Nat → Bool) (hx : ∀ a b, f (a ^^^ b) = (f a ^^ f b))
    (label : Bool) (agree : ∀ y < p, lifts y = label → f (features y) = false)
    (fuel x : Nat) (ps : Array Nat) (hp : ∀ v ∈ ps, f v = false) :
    ∀ v ∈ build label fuel x ps, f v = false := by
  induction fuel generalizing x ps with
  | zero => exact hp
  | succ n ih =>
    unfold build
    apply ih
    split
    · rename_i h
      dsimp only
      split
      · exact hp
      · intro v hv
        rcases Array.mem_or_eq_of_mem_setIfInBounds hv with old | rfl
        · exact hp v old
        · rw [residual_preserves f hx ps hp, agree _ h.1 h.2]
    · exact hp

private theorem units_reduce (label : Bool) :
    (let ps := basis label; (List.range 4992).all (fun i => residual ps 4992 (2^i) == 0)) = true := by
  cases label <;> native_decide

/-- Any XOR-linear evaluator zero on one class is zero on every coefficient unit. -/
theorem packed_units_vanish (f : Nat → Bool) (h0 : f 0 = false)
    (hx : ∀ a b, f (a ^^^ b) = (f a ^^ f b)) (label : Bool)
    (agree : ∀ y < p, lifts y = label → f (features y) = false)
    (i : Nat) (hi : i < 4992) : f (2^i) = false := by
  have hp : ∀ v ∈ basis label, f v = false := by
    apply build_preserves f hx label agree
    intro v hv
    simpa [Array.mem_replicate.mp hv |>.2] using h0
  have hu := List.all_eq_true.mp (units_reduce label) i (List.mem_range.mpr hi)
  have hz : residual (basis label) 4992 (2^i) = 0 := by simpa using hu
  rw [← residual_preserves f hx _ hp 4992, hz, h0]

/-- A linear evaluation vanishing on spanning feature rows vanishes everywhere. -/
theorem vanishes_on_span {K V : Type*} [Field K] [AddCommGroup V] [Module K V]
    (rows : Set V) (full : Submodule.span K rows = ⊤)
    (eval : V →ₗ[K] K) (agree : ∀ v ∈ rows, eval v = 0) (x : V) : eval x = 0 := by
  have h : Submodule.span K rows ≤ LinearMap.ker eval := Submodule.span_le.mpr agree
  exact h (by rw [full]; trivial : x ∈ Submodule.span K rows)

end M31CubicSpan
