import Mathlib

namespace M31BooleanDegree

abbrev F := ZMod 2147483647

def liftBit (b x : Nat) : Bool :=
  let u : F := x
  decide ((u^3 + 2*u + (b : F))^1073741823 = 1)

/-- High bits fixed by the aligned origin; all low bits vary independently. -/
def cubeWeight (b origin width : Nat) : Nat :=
  ((List.range (2^width)).filter fun i => liftBit b (origin+i)).length

theorem smallWitness : cubeWeight 14 8 3 = 3 ∧ cubeWeight 36 8 3 = 5 := by
  native_decide

theorem largeWitness : cubeWeight 14 0 16 = 32495 ∧ cubeWeight 36 131072 16 = 32887 := by
  native_decide

/-- Each monomial involving fewer than all free variables has zero total
over the Boolean cube in characteristic two: its number of ones is 2^(d-k).
The same holds for any finite sum of these monomial weights. -/
theorem parityLower {I : Type*} (terms : Finset I) (width : Nat) (arity : I → Nat)
    (proper : ∀ i ∈ terms, arity i < width) :
    ∑ i ∈ terms, (2 : ZMod 2)^(width-arity i) = 0 := by
  apply Finset.sum_eq_zero
  intro i hi
  have pos := Nat.sub_pos_of_lt (proper i hi)
  exact (congrArg (fun t : ZMod 2 => t^(width-arity i)) (show (2 : ZMod 2) = 0 by decide)).trans (zero_pow (Nat.ne_of_gt pos))

/-- Pack a five-bit truth table in increasing input order. -/
def word (f : Nat → Bool) : UInt32 :=
  (List.range 32).foldl (fun w i => if f i then w ||| (1 <<< i.toUInt32) else w) 0

private def byteWeights : Array Nat := (List.range 256).toArray.map fun v =>
  ((List.range 8).filter v.testBit).length

def weight (w : UInt32) : Nat :=
  byteWeights[(w &&& 255).toNat]! + byteWeights[((w >>> 8) &&& 255).toNat]! +
  byteWeights[((w >>> 16) &&& 255).toNat]! + byteWeights[(w >>> 24).toNat]!

def pairs := (List.range 5).flatMap fun a => ((List.range 5).filter (a < ·)).map (a, ·)

def quadratic (q : Fin 1024) : UInt32 := word fun i =>
  (pairs.zipIdx.filter fun ((a,b),k) => q.val.testBit k && i.testBit a && i.testBit b).length % 2 == 1

def linearWords : List UInt32 := (List.range 32).map fun a => word fun i =>
  ((List.range 5).filter (fun k => a.testBit k && i.testBit k)).length % 2 == 1

def signedDistance (residual linear : UInt32) : Nat :=
  let d := weight (residual ^^^ linear)
  min d (32-d)

def best (residual : UInt32) : Nat :=
  linearWords.foldl (fun acc w => min acc (signedDistance residual w)) 32

private theorem foldBound (r : UInt32) (ws : List UInt32) (a : Nat) :
    let v := ws.foldl (fun acc w => min acc (signedDistance r w)) a
    v ≤ a ∧ ∀ w ∈ ws, v ≤ signedDistance r w := by
  induction ws generalizing a with
  | nil => simp
  | cons x xs ih =>
    obtain ⟨h, tail⟩ := ih (min a (signedDistance r x))
    constructor
    · exact h.trans (min_le_left ..)
    · intro w hw
      rcases List.mem_cons.mp hw with rfl | hw
      · exact h.trans (min_le_right ..)
      · exact tail w hw

def blocks (b start : Nat) := Array.ofFn fun j : Fin 2048 =>
  word fun i => liftBit b (start + 32*j.val + i)

def relaxedCost (rows : Array UInt32) (q : Fin 1024) : Nat :=
  let pattern := quadratic q
  ∑ j : Fin 2048, best (rows[j.val]! ^^^ pattern)

def firstBlocks := blocks 14 0
def secondBlocks := blocks 36 131072

theorem intervalBounds : ∀ q : Fin 1024,
    18861 ≤ relaxedCost firstBlocks q ∧ 18879 ≤ relaxedCost secondBlocks q := by native_decide

theorem totalBound (rows : Array UInt32) (q : Fin 1024) (w : Fin 2048 → UInt32)
    (allowed : ∀ j, w j ∈ linearWords) :
    relaxedCost rows q ≤ ∑ j : Fin 2048, signedDistance (rows[j.val]! ^^^ quadratic q) (w j) := by
  exact Finset.sum_le_sum fun j _ => (foldBound _ linearWords 32).2 _ (allowed j)

end M31BooleanDegree
