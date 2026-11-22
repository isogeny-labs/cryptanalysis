import Std
open Lean.Grind

namespace RightQuotient

variable {K : Type} [CommRing K]

def L (lam x : K) : K := x^2 + lam*x

def vanisher (vs : List K) (x : K) : K :=
  (vs.map (fun v => x + v)).prod

def imageVanisher (vs : List K) (lam y : K) : K :=
  (vs.map (fun v => y + L lam v)).prod

theorem factor (h2 : (2 : K) = 0) (lam x v : K) :
    L lam x + L lam v = (x + v) * (x + v + lam) := by
  unfold L
  grind +ring

theorem composition (h2 : (2 : K) = 0) (vs : List K) (lam x : K) :
    imageVanisher vs lam (L lam x) =
      vanisher vs x * vanisher vs (x+lam) := by
  induction vs with
  | nil => simp [imageVanisher, vanisher]; grind +ring
  | cons v vs ih =>
      change (L lam x + L lam v) * imageVanisher vs lam (L lam x) =
        ((x+v)*vanisher vs x) * ((x+lam+v)*vanisher vs (x+lam))
      rw [factor h2]
      rw [ih]
      grind +ring

theorem membership (h2 : (2 : K) = 0)
    (hne : (1 : K) ≠ 0)
    (hmul : ∀ a b : K, a*b=0 → a=0 ∨ b=0)
    (vs : List K) (lam y : K) :
    imageVanisher vs lam y = 0 ↔ ∃ v ∈ vs, y = L lam v := by
  induction vs with
  | nil => simp [imageVanisher, hne]
  | cons v vs ih =>
      simp only [List.mem_cons]
      change (y+L lam v)*imageVanisher vs lam y = 0 ↔
        ∃ w, (w=v ∨ w∈vs) ∧ y=L lam w
      constructor
      · intro h
        rcases hmul _ _ h with h | h
        · refine ⟨v, Or.inl rfl, ?_⟩
          grind +ring
        · rcases ih.mp h with ⟨w, hw, hy⟩
          exact ⟨w, Or.inr hw, hy⟩
      · rintro ⟨w, hw, hy⟩
        rcases hw with rfl | hw
        · have hz : y + L lam w = 0 := by grind +ring
          rw [hz]
          grind +ring
        · have hz : imageVanisher vs lam y = 0 :=
            ih.mpr ⟨w, hw, hy⟩
          rw [hz]
          grind +ring

#print axioms RightQuotient.factor
#print axioms RightQuotient.composition
#print axioms RightQuotient.membership

end RightQuotient

namespace ChartQuartic
variable {K : Type} [CommRing K]

theorem chart_A (h2 : (2 : K) = 0) (u t : K) :
    t^2 + u*(u+1)*t*(t+1) + (t+1)^2 =
      1 + u*(u+1)*t*(t+1) := by
  grind +ring

theorem chart_D (h2 : (2 : K) = 0) (u t : K) :
    (u+1)^2*t^2 + u^2*(t+1)^2 = t^2+u^2 := by
  grind +ring

theorem resultant_simplified (h2 : (2 : K) = 0) (B D S p : K) :
    (D+S*(1+B))^2 + S*B^2 + p*B*(D+S*((1+B)+B)) +
       p^2*D*((1+B)+B+D) =
    D^2 + S^2 + (S^2+S)*B^2 + p*B*(D+S) + p^2*D*(D+1) := by
  grind +ring

#print axioms ChartQuartic.chart_A
#print axioms ChartQuartic.chart_D
#print axioms ChartQuartic.resultant_simplified
end ChartQuartic
