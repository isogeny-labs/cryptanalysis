import Bloom

/-!
M31 Metal screen specification. The arithmetic theorems cover every canonical
field operand and the exact one-fold reduction used in screen.metal. The scan
theorem covers the target-minus-pair / target-plus-pair order and preservation
of the first exact payload under a no-false-negative bitmap. These are semantic
claims; no theorem here asserts that compiled MSL/Swift/Rust code refines this
model or that a measured runtime inequality holds.
-/

namespace MetalScreen

private def p : Nat := 2147483647
private def base : Nat := 2147483648

def fold (x : Nat) : Nat := x % base + x / base
def red (x : Nat) : Nat := if fold x ≥ p then fold x - p else fold x
def redBits (x : Nat) : Nat :=
  let y := (x &&& (2^31 - 1)) + (x >>> 31)
  if y ≥ p then y - p else y

theorem bit_operations_are_fold (x : Nat) : redBits x = red x := by
  have h : x &&& 2147483647 = x % 2147483648 := by
    simpa using Nat.and_two_pow_sub_one_eq_mod x 31
  simp [redBits, red, fold, p, base, h, Nat.shiftRight_eq_div_pow]

theorem one_fold_correct (x : Nat) (hx : x < p * p) : red x = x % p := by
  unfold red fold p base at *
  by_cases h : x % 2147483648 + x / 2147483648 ≥ 2147483647
  · simp [h]
    omega
  · simp [h]
    omega

theorem mul_reduction_correct (a b : Nat) (ha : a < p) (hb : b < p) :
    redBits (a * b) = (a * b) % p ∧ a * b < 2^64 := by
  have hle : a * b ≤ p * b := Nat.mul_le_mul_right b (Nat.le_of_lt ha)
  have hlt : p * b < p * p := Nat.mul_lt_mul_of_pos_left hb (by decide)
  constructor
  · rw [bit_operations_are_fold]
    exact one_fold_correct _ (by omega)
  · unfold p at *
    omega

def fsub (a b : Nat) : Nat := if a ≥ b then a - b else p - (b - a)

theorem sub_reduction_correct (a b : Nat) (ha : a < p) (hb : b < p) :
    fsub a b = (a + p - b) % p := by
  unfold fsub p at *
  by_cases h : a ≥ b
  · simp [h]
    omega
  · simp [h]
    omega

-- PairIndex probes `target - outer` before `target + outer` for each
-- canonical pair point; an identity entry has only one slot.
def signedCandidates {α : Type} (add : Option α → Option α → Option α)
    (neg : α → α) (target : Option α) : List (Option α) → List (Option α)
  | [] => []
  | none :: rest => add target none :: signedCandidates add neg target rest
  | some outer :: rest =>
      add target (some (neg outer)) :: add target (some outer) ::
        signedCandidates add neg target rest

theorem first_exact_witness_preserved {α β : Type} (add : Option α → Option α → Option α)
    (neg : α → α) (target : Option α) (entries : List (Option α))
    (x : α → Nat) (hash : Nat → Nat) (inserted : List Nat)
    (lookup : Option α → Option β) (empty : lookup none = none)
    (support : ∀ point, lookup (some point) ≠ none → x point ∈ inserted) :
    XFilter.firstHit lookup
      ((signedCandidates add neg target entries).map
        (XFilter.reject x (fun q => Bloom.bitmap hash inserted (hash q)))) =
    XFilter.firstHit lookup (signedCandidates add neg target entries) := by
  exact Bloom.first_payload_preserved x hash inserted lookup empty support _

end MetalScreen
