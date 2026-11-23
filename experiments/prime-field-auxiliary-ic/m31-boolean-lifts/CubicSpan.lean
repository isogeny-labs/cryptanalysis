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
private def residual (pivots : Array Nat) (initial : Nat) : Nat := Id.run do
  let mut row := initial
  for _ in [:4992] do
    if row == 0 then break
    let pivot := pivots[row.log2]!
    if pivot == 0 then break
    row := row ^^^ pivot
  return row

private def rankFor (label : Bool) : Nat := Id.run do
  let mut pivots := Array.replicate 4992 0
  let mut rank := 0
  let mut x := 1
  for _ in [:9989] do
    x := (1103515245*x + 12345) % (2^31)
    if x < p && lifts x == label then
      let row := residual pivots (features x)
      if row != 0 then
        pivots := pivots.set! row.log2 row
        rank := rank + 1
  return rank

theorem both_eliminations_full : rankFor true = 4992 ∧ rankFor false = 4992 := by
  native_decide

/-- A linear evaluation vanishing on spanning feature rows vanishes everywhere. -/
theorem vanishes_on_span {K V : Type*} [Field K] [AddCommGroup V] [Module K V]
    (rows : Set V) (full : Submodule.span K rows = ⊤)
    (eval : V →ₗ[K] K) (agree : ∀ v ∈ rows, eval v = 0) (x : V) : eval x = 0 := by
  have h : Submodule.span K rows ≤ LinearMap.ker eval := Submodule.span_le.mpr agree
  exact h (by rw [full]; trivial : x ∈ Submodule.span K rows)

end M31CubicSpan
