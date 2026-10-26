module

public import Mathlib.Tactic.Abel

/-! The order-five affine involution transports the degree-2 and degree-3
Hecke row equations with coefficients `a₂=-2` and `a₃=-1`. -/
namespace AffineTransport

variable {A : Type*} [AddCommGroup A]

/-- Three neighbors summing to `-2P` retain that equation after the
coordinate involution `Q ↦ T-Q`, provided `5T=0`. -/
public theorem degree_two (T P q₀ q₁ q₂ : A)
    (hT : T + T + T + T + T = 0)
    (hrow : q₀ + q₁ + q₂ = -(P + P)) :
    (T - q₀) + (T - q₁) + (T - q₂) = -((T - P) + (T - P)) := by
  calc
    (T - q₀) + (T - q₁) + (T - q₂)
        = (T + T + T) - (q₀ + q₁ + q₂) := by abel
    _ = (T + T + T) + (P + P) := by rw [hrow]; abel
    _ = ((T + T + T + T + T) - (T + T)) + (P + P) := by abel
    _ = -(T + T) + (P + P) := by rw [hT]; abel
    _ = -((T - P) + (T - P)) := by abel

/-- Four neighbors summing to `-P` retain that equation after the same
order-five affine involution. -/
public theorem degree_three (T P q₀ q₁ q₂ q₃ : A)
    (hT : T + T + T + T + T = 0)
    (hrow : q₀ + q₁ + q₂ + q₃ = -P) :
    (T - q₀) + (T - q₁) + (T - q₂) + (T - q₃) = -(T - P) := by
  calc
    (T - q₀) + (T - q₁) + (T - q₂) + (T - q₃)
        = (T + T + T + T) - (q₀ + q₁ + q₂ + q₃) := by abel
    _ = (T + T + T + T) + P := by rw [hrow]; abel
    _ = (T + T + T + T + T) - T + P := by abel
    _ = -T + P := by rw [hT]; abel
    _ = -(T - P) := by abel

end AffineTransport

#print axioms AffineTransport.degree_two
#print axioms AffineTransport.degree_three
