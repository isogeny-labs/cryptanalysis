import Mathlib.Tactic

namespace M31OrbitLabels
variable {F : Type*} [Field F]

def rhs (x : F) := x^3+2*x+14
def cleared (n d : F) := n*(n*n+2*d*d)+14*d^3

theorem chord_cleared (x y a b : F) (hne : x ≠ a) :
    let dx := x-a
    let dy := y-b
    let coord := (dy/dx)^2-x-a
    dy^2-(x+a)*dx^2 = coord*dx^2 := by
  dsimp only
  field_simp [sub_ne_zero.mpr hne]
  ring

theorem symmetric_numerator (x y a b : F)
    (left : y^2=x^3+x) (right : b^2=a^3+a) :
    (y-b)^2-(x+a)*(x-a)^2 = (x+a)*(1+x*a)-2*y*b := by
  linear_combination left+right

theorem value (u h : F) : cleared (u*h^2) (h^2) = rhs u*(h^3)^2 := by
  unfold cleared rhs
  ring

theorem label (u h : F) (hn : h ≠ 0) :
    (∃ y, y^2=rhs u) ↔ ∃ y, y^2=cleared (u*h^2) (h^2) := by
  rw [value]
  constructor
  · rintro ⟨y,hy⟩
    exact ⟨y*h^3, by rw [mul_pow,hy]⟩
  · rintro ⟨y,hy⟩
    refine ⟨y/h^3, ?_⟩
    rw [div_pow,hy]
    field_simp

theorem chord_label (x y a b : F) (hne : x≠a) :
    let u := ((y-b)/(x-a))^2-x-a
    (∃ z, z^2=rhs u) ↔ ∃ z, z^2=cleared ((y-b)^2-(x+a)*(x-a)^2) ((x-a)^2) := by
  dsimp only
  rw [chord_cleared x y a b hne]
  exact label _ _ (sub_ne_zero.mpr hne)

end M31OrbitLabels
