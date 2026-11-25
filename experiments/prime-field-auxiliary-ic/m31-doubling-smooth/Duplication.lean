import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

namespace SmoothDuplication
variable {K : Type*} [Field K]

def cubic (x : K) := x^3 + 2*x + 14
def doubleX (x : K) := (3*x^2+2)^2 / (4*cubic x) - 2*x
def scale (x : K) := (3*x^2+2)*(x-doubleX x)/(2*cubic x)-1

theorem duplication (x : K) (h2 : (2:K) ≠ 0) (hf : cubic x ≠ 0) :
    cubic (doubleX x) = cubic x * scale x ^ 2 := by
  have h4 : (4:K) ≠ 0 := by simpa only [show (4:K) = 2*2 by ring] using mul_ne_zero h2 h2
  change (doubleX x)^3 + 2*doubleX x + 14 = cubic x * scale x ^ 2
  unfold scale doubleX
  generalize hv : cubic x = v at *
  field_simp [h2,h4,hf]
  rw [← hv]
  unfold cubic
  ring

theorem lift_iff (x : K) (h2 : (2:K) ≠ 0) (hf : cubic x ≠ 0)
    (hd : cubic (doubleX x) ≠ 0) :
    (∃ y : K, y^2 = cubic x) ↔ (∃ z : K, z^2 = cubic (doubleX x)) := by
  have eq := duplication x h2 hf
  have hs : scale x ≠ 0 := by
    intro hz
    simp [hz] at eq
    exact hd eq
  constructor
  · rintro ⟨y,hy⟩
    exact ⟨y*scale x, by rw [mul_pow,hy,eq]⟩
  · rintro ⟨z,hz⟩
    exact ⟨z/scale x, by rw [div_pow,hz,eq,mul_div_cancel_right₀ _ (pow_ne_zero _ hs)]⟩
end SmoothDuplication
