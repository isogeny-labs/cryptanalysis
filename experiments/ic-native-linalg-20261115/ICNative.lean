import Mathlib

/- Algebraic invariants for the native implementation. The program's graph
traversal, memory bounds and Euclidean loop termination are checked separately
by executable tests; these declarations do not encode a full program proof. -/
namespace ICNative

theorem euclid_initial (p : ℕ) (value : ℤ) :
    ((p : ℤ) : ZMod p) = (0 : ZMod p) * (value : ZMod p) := by simp

theorem euclid_step (p : ℕ) (value r₀ r₁ t₀ t₁ k : ℤ)
    (h₀ : (r₀ : ZMod p) = (t₀ : ZMod p) * (value : ZMod p))
    (h₁ : (r₁ : ZMod p) = (t₁ : ZMod p) * (value : ZMod p)) :
    ((r₀ - k * r₁ : ℤ) : ZMod p) =
      ((t₀ - k * t₁ : ℤ) : ZMod p) * (value : ZMod p) := by
  push_cast
  rw [h₀, h₁]
  ring

theorem tree_edge_substitute {R : Type*} [CommRing R]
    (prime hu hv root s f rhs : R) (hu_expr : hu = s * root + f) :
    prime + hu + hv = rhs ↔ hv = -s * root + (rhs - prime - f) := by
  rw [hu_expr]
  constructor <;> intro h <;> linear_combination h

theorem cycle_row_substitute {R : Type*} [CommRing R]
    (prime hu hv root su sv fu fv rhs : R)
    (hu_expr : hu = su * root + fu) (hv_expr : hv = sv * root + fv) :
    prime + hu + hv = rhs ↔ prime + (su + sv) * root + fu + fv = rhs := by
  rw [hu_expr, hv_expr]
  constructor <;> intro h <;> linear_combination h

theorem rational_log_extract {G : Type*} [CommGroup G]
    (g h a b : G) (A B e : ℤ)
    (ha : a = g ^ A) (hb : b = g ^ B)
    (split : a = b * (h * g ^ e)) : h = g ^ (A - B - e) := by
  calc
    h = b⁻¹ * a * (g ^ e)⁻¹ := by rw [split]; group
    _ = g ^ (-B) * g ^ A * g ^ (-e) := by rw [ha, hb]; simp only [zpow_neg]
    _ = g ^ (-B + A + -e) := by rw [zpow_add, zpow_add]
    _ = g ^ (A - B - e) := by congr 1; omega

end ICNative

#print axioms ICNative.euclid_initial
#print axioms ICNative.euclid_step
#print axioms ICNative.tree_edge_substitute
#print axioms ICNative.cycle_row_substitute
#print axioms ICNative.rational_log_extract
