import FixtureHash

namespace M31Reflection.CoordinateLookup
open FixtureHash

abbrev Word := UInt32
private def missing : Word := 0xffffffff

inductive Layout | compact | wide

def capacity : Layout → Nat | .compact => 64 | .wide => 256

def slot : Layout → Word → Nat
  | .compact, x => ((x*59649) >>> 26).toNat
  | .wide, x => ((x*49) >>> 24).toNat

def encode (x : F) : Word := UInt32.ofNat (2*x.val + (if liftBit x then 1 else 0))
def refRows : List (Word × Bool) := roots.map fun x => (UInt32.ofNat x.val, liftBit x)

/-- Initialize empty slots and install the 32 packed key and label words. -/
def table (layout : Layout) : Array Word :=
  roots.foldl (fun entries x => entries.set! (slot layout (UInt32.ofNat x.val)) (encode x))
    (Array.replicate (capacity layout) missing)

def lookup (layout : Layout) (x : Word) : Option Bool :=
  let e := (table layout)[slot layout x]!
  if e ≠ missing ∧ e >>> 1 = x then some (e &&& 1 = 1) else none

theorem prepared (layout : Layout) :
    (table layout).size = capacity layout ∧
    (roots.map fun x => slot layout (UInt32.ofNat x.val)).Nodup ∧
    (roots.all fun x => (table layout)[slot layout (UInt32.ofNat x.val)]! == encode x) = true ∧
    (∀ i : Fin (capacity layout), (table layout)[i.val]! ≠ missing →
      ((table layout)[i.val]! >>> 1, decide ((table layout)[i.val]! &&& 1 = 1)) ∈ refRows) := by
  cases layout <;> native_decide

private theorem slot_bound (layout : Layout) (x : Word) : slot layout x < capacity layout := by
  have bound (w : Word) : w.toNat < 4294967296 := w.toBitVec.isLt
  cases layout with
  | compact =>
    change ((x*59649).toNat >>> 26) < 64
    rw [Nat.shiftRight_eq_div_pow]
    have h := bound (x*59649)
    omega
  | wide =>
    change ((x*49).toNat >>> 24) < 256
    rw [Nat.shiftRight_eq_div_pow]
    have h := bound (x*49)
    omega

/-- Exact membership and lift status for arbitrary 32-bit inputs, including
noncanonical words and off-list inputs hashing to an occupied slot. -/
theorem exact_lookup (layout : Layout) (x : Word) (b : Bool) :
    lookup layout x = some b ↔ (x,b) ∈ refRows := by
  constructor
  · simp only [lookup]
    split
    next ok =>
      intro hb
      have mem := (prepared layout).2.2.2 ⟨slot layout x, slot_bound layout x⟩ ok.1
      rw [ok.2, Option.some.inj hb] at mem
      exact mem
    next => simp
  · have complete : (refRows.all fun row => lookup layout row.1 == some row.2) = true := by
      cases layout <;> native_decide
    intro mem
    exact eq_of_beq (List.all_eq_true.mp complete (x,b) mem)

end M31Reflection.CoordinateLookup

namespace M31Reflection.CoordinateLookup

/-- In the archived input, columns zero and one have different coordinates
and both lift. A decoder of the returned status alone cannot recover both indices. -/
theorem status_does_not_identify_column (layout : Layout) (decode : Option Bool → Option Nat) :
    ¬ (decode (lookup layout 3) = some 0 ∧ decode (lookup layout 98625645) = some 1) := by
  have left := (exact_lookup layout 3 true).mpr (by native_decide)
  have right := (exact_lookup layout 98625645 true).mpr (by native_decide)
  rw [left, right]
  rintro ⟨h₀,h₁⟩
  simp_all

end M31Reflection.CoordinateLookup
