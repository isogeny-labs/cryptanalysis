import Std

/-! An odd GF(2) equation dependency excludes every proposed dual map. -/
namespace ParametricDual

variable {V : Type}

def xorRows (zero : V) (xor : V → V → V) : List V → V
  | [] => zero
  | row :: rows => xor row (xorRows zero xor rows)

def xorBits : List Bool → Bool
  | [] => false
  | bit :: bits => Bool.xor bit (xorBits bits)

theorem map_xorRows (zero : V) (xor : V → V → V) (score : V → Bool)
    (hzero : score zero = false)
    (hxor : ∀ a b, score (xor a b) = Bool.xor (score a) (score b))
    (rows : List V) :
    score (xorRows zero xor rows) = xorBits (rows.map score) := by
  induction rows with
  | nil => simp [xorRows, xorBits, hzero]
  | cons row rows ih => simp [xorRows, xorBits, hxor, ih]

theorem odd_dependency_excludes_dual
    (zero : V) (xor : V → V → V) (rows : List V)
    (hrows : xorRows zero xor rows = zero)
    (hodd : xorBits (rows.map (fun _ => true)) = true)
    (score : V → Bool) (hzero : score zero = false)
    (hxor : ∀ a b, score (xor a b) = Bool.xor (score a) (score b))
    (hall : ∀ row ∈ rows, score row = true) : False := by
  have hmap : rows.map score = rows.map (fun _ => true) := by
    apply List.map_congr_left
    intro row hmem
    exact hall row hmem
  have hscore := map_xorRows zero xor score hzero hxor rows
  rw [hrows, hzero, hmap, hodd] at hscore
  cases hscore

#print axioms ParametricDual.map_xorRows
#print axioms ParametricDual.odd_dependency_excludes_dual

end ParametricDual
