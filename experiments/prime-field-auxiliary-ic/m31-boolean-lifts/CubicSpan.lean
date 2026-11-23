import Mathlib.LinearAlgebra.Span.Basic
import Mathlib.Data.List.Sublists
import Mathlib.Data.Nat.Bitwise
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.FieldTheory.Finite.Basic

namespace M31CubicSpan

private def p : Nat := 2147483647

/-- Each column is an increasing list of zero to three distinct input bits. -/
def terms := (List.range 4).flatMap (fun d => (List.range 31).sublistsLen d)

theorem term_coverage (t : List Nat) :
    t ∈ terms ↔ t.Sublist (List.range 31) ∧ t.length < 4 := by
  simp only [terms, List.mem_flatMap, List.mem_range, List.mem_sublistsLen]
  aesop

theorem terms_distinct : terms.Nodup := by native_decide

theorem term_count : terms.length = 4992 := by native_decide

private def pack {α : Type} (f : α → Bool) : List α → Nat
  | [] => 0
  | t :: ts => Nat.bit (f t) (pack f ts)

private theorem pack_at {α : Type} (f : α → Bool) (ts : List α) (i : Nat)
    (hi : i < ts.length) : (pack f ts).testBit i = f ts[i] := by
  induction ts generalizing i with
  | nil => simp at hi
  | cons _ _ ih =>
    cases i with
    | zero => exact Nat.testBit_bit_zero _ _
    | succ i => exact (Nat.testBit_bit_succ _ _ _).trans (ih i (by simpa using hi))

private def masks (is : List Nat) :=
  is.map (fun i => (i, pack (fun t : List Nat => !t.contains i) terms))

private def applyMasks (x : Nat) : List (Nat × Nat) → Nat
  | [] => pack (fun _ => true) terms
  | (i,m) :: rest =>
    let tail := applyMasks x rest
    if x.testBit i then tail else tail &&& m

private def features (x : Nat) := applyMasks x (masks (List.range 31))

private theorem apply_at (x j : Nat) (hj : j < terms.length) (is : List Nat) :
    (applyMasks x (masks is)).testBit j = true ↔
      ∀ i ∈ is, i ∈ terms[j] → x.testBit i = true := by
  induction is with
  | nil => simp [masks, applyMasks, pack_at _ _ _ hj]
  | cons i is ih =>
    change (if x.testBit i then applyMasks x (masks is) else
      applyMasks x (masks is) &&& pack (fun t : List Nat => !t.contains i) terms).testBit j = true ↔ _
    cases h : x.testBit i <;> simp [h, pack_at _ _ _ hj, ih]
    all_goals aesop

theorem feature_is_monomial (x j : Nat) (hj : j < terms.length) :
    (features x).testBit j = true ↔ ∀ i ∈ terms[j], x.testBit i = true := by
  rw [features, apply_at _ _ hj]
  have sub := (term_coverage _).mp (List.getElem_mem hj)
  exact ⟨fun h i hi => h i (sub.1.subset hi) hi, fun h i _ hi => h i hi⟩

local instance : Fact (Nat.Prime p) := ⟨by
  change (mersenne 31).Prime
  apply lucas_lehmer_sufficiency 31 (by decide)
  norm_num⟩

private def squareIter (x : ZMod p) : Nat → ZMod p
  | 0 => x
  | k+1 => let y := squareIter x k; y*y

private theorem squareIter_pow (x : ZMod p) (k : Nat) :
    squareIter x k = x^(2^k) := by
  induction k with
  | zero => simp [squareIter]
  | succ n ih => rw [squareIter, ih, pow_succ 2, pow_mul, pow_two]

private def rhs (x : Nat) : ZMod p := (x : ZMod p)^3 + 2*x + 14

private def lifts (x : Nat) : Bool := squareIter (rhs x) 30 == rhs x

/-- A coordinate is accepted exactly when the affine curve has a point above it. -/
theorem lifts_iff_point (x : Nat) : lifts x = true ↔
    ∃ y : ZMod 2147483647, y^2 = (x : ZMod 2147483647)^3 + 2*x + 14 := by
  change (squareIter (rhs x) 30 == rhs x) = true ↔ ∃ y : ZMod p, y^2 = rhs x
  rw [beq_iff_eq, squareIter_pow]
  constructor
  · intro h
    exact ⟨rhs x ^ (2^29 : Nat), by rw [← pow_mul]; exact h⟩
  · rintro ⟨y, hy⟩
    rw [← hy, ← pow_mul, show 2 * 2^30 = p+1 by decide, pow_succ, ZMod.pow_card, pow_two]

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

/-- Sum over GF(2) of the selected monomial columns. -/
def poly (w : Nat) : List Nat → Bool
  | [] => false
  | j :: js => w.testBit j ^^ poly w js

private theorem poly_zero (js : List Nat) : poly 0 js = false := by
  induction js <;> simp_all [poly]

private theorem poly_xor (js : List Nat) (a b : Nat) :
    poly (a ^^^ b) js = (poly a js ^^ poly b js) := by
  induction js with
  | nil => rfl
  | cons j js ih =>
    simp only [poly, Nat.testBit_xor, ih]
    cases a.testBit j <;> cases b.testBit j <;> cases poly a js <;> cases poly b js <;> decide

private theorem poly_unit (js : List Nat) (hd : js.Nodup) (i : Nat) :
    poly (2^i) js = decide (i ∈ js) := by
  induction js with
  | nil => simp [poly]
  | cons j js ih =>
    obtain ⟨fresh, rest⟩ := List.nodup_cons.mp hd
    by_cases eq : i = j
    · subst i; simp [poly, ih rest, fresh]
    · simp [poly, ih rest, eq]

/-- On either lift class, only the empty cubic coefficient list vanishes everywhere. -/
theorem cubic_annihilator_empty (js : List Nat) (hd : js.Nodup)
    (valid : ∀ i ∈ js, i < terms.length) (label : Bool)
    (vanishes : ∀ x < p, lifts x = label → poly (features x) js = false) : js = [] := by
  cases js with
  | nil => rfl
  | cons j js =>
    have hj := valid j (by simp)
    rw [term_count] at hj
    have h := packed_units_vanish (fun w => poly w (j :: js)) (poly_zero _)
      (poly_xor _) label vanishes j hj
    simp [poly_unit _ hd] at h

/-- A linear evaluation vanishing on spanning feature rows vanishes everywhere. -/
theorem vanishes_on_span {K V : Type*} [Field K] [AddCommGroup V] [Module K V]
    (rows : Set V) (full : Submodule.span K rows = ⊤)
    (eval : V →ₗ[K] K) (agree : ∀ v ∈ rows, eval v = 0) (x : V) : eval x = 0 := by
  have h : Submodule.span K rows ≤ LinearMap.ker eval := Submodule.span_le.mpr agree
  exact h (by rw [full]; trivial : x ∈ Submodule.span K rows)

end M31CubicSpan
