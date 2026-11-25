import Mathlib.Tactic

namespace M31Exceptional

def modulus : Nat := 2147483647
def coordinates : List Nat := [
    0, 1, 33359769, 139984982,
    177504693, 244425803, 321862516, 478064842,
    508369663, 637231878, 705231622, 746452052,
    849551769, 952675664, 1040047656, 1063718422,
    1174338953, 1516123271, 1575660783, 1623230299,
    1668578532, 1729373102, 1753716560, 1825752205,
    1903942232, 1948130974, 1965083199, 1983108407,
    2074043423, 2085125131, 2106326137, 2127360844]

def bucket (x : Nat) := (x ^^^ (x / 16)) % 256

def table := coordinates.foldl (fun t x => t.set (bucket x) x)
  (List.replicate 256 modulus)

def lookup (x : Nat) := (table[bucket x]?).getD modulus

private theorem coverage : coordinates.all (fun x => lookup x == x) = true := by
  native_decide

private theorem provenance : ∀ i : Fin 256,
    let v := (table[i.val]?).getD modulus
    v = modulus ∨ v ∈ coordinates := by
  native_decide

/-- An arbitrary canonical input is accepted exactly when it occurs in the fixed list. -/
theorem exact_lookup (x : Nat) (hx : x < modulus) : lookup x = x ↔ x ∈ coordinates := by
  constructor
  · intro h
    have hv := provenance ⟨bucket x, Nat.mod_lt _ (by decide)⟩
    change lookup x = modulus ∨ lookup x ∈ coordinates at hv
    rw [h] at hv
    exact hv.resolve_left (Nat.ne_of_lt hx)
  · intro h
    exact beq_iff_eq.mp (List.all_eq_true.mp coverage x h)

end M31Exceptional
