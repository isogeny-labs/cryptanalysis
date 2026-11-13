import Init.Grind.Ring.Basic
import Init.Grind.Module.Basic

/-! Algebra and conditional finite-group structure for the fixed C0/T20
adapter. These theorems do not define the actual curves, Picard functors,
completed covers, balanced reducer or normalized Richelot chain. Their
identification with the hypotheses below remains written/native evidence.
No global inverse isogeny is asserted. -/
set_option autoImplicit false
namespace PrimeFieldChain
open Lean.Grind

theorem actual_c0_first_cover {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    z^6+6*z^4+13*z^2+56=(z^2+2)^3+(z^2+2)+46 := by grind

theorem actual_c0_reciprocal_cover {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    (z^6+6*z^4+13*z^2+56)*56^2 =
      (56+38*z^2)^3+44*(56+38*z^2)*z^4+21*z^6 := by grind

theorem actual_repeated_finite_fibre {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    (z^2+2)-2=z^2 ∧
    z^6+6*z^4+13*z^2+56-37^2=z^2*(z^4+6*z^2+13) ∧
    (37 : K)^2=2^3+2+46 ∧ (-37 : K)^2=2^3+2+46 := by grind

theorem actual_empty_finite_fibre_and_infinity_targets
    {K : Type} [CommRing K]
    (z : K) (characteristic : (101 : K)=0) :
    (56+38*z^2)-38*z^2=56 ∧ (56 : K)*92=1 ∧
    (56 : K)^2=38^3+44*38+21 ∧ (-56 : K)^2=38^3+44*38+21 := by grind

theorem completed_degree_two_balanced_accounting
    (d nplus nminus : Int) (degree_two : d+nplus+nminus=2) :
    nminus-1=1-d-nplus := by grind

theorem actual_public_constants :
    (2 : Nat)*6159%12317=1 ∧ (4 : Nat)*9238%12317=1 ∧
    (2 : Nat)*55%109=1 ∧ (2 : Nat)*57%113=1 ∧
    (4 : Nat)*82%109=1 ∧ (4 : Nat)*85%113=1 ∧
    (98 : Nat)*99%109=1 ∧ (196 : Nat)*104%109=1 := by decide

theorem nonuniform_component_recovery
    {E F : Type} [IntModule E] [IntModule F]
    (e : E) (f : F)
    (order_e : (109 : Int) • e=0) (order_f : (113 : Int) • f=0) :
    (104 : Int) • ((196 : Int) • e)=e ∧
    (85 : Int) • ((4 : Int) • f)=f := by
  constructor <;> grind

theorem inverse_norm_component_recovery
    {E F : Type} [IntModule E] [IntModule F]
    (e : E) (f : F)
    (order_e : (109 : Int) • e=0) (order_f : (113 : Int) • f=0) :
    (99 : Int) • ((98 : Int) • e)=e ∧
    (57 : Int) • ((2 : Int) • f)=f := by
  constructor <;> grind

theorem forward_component_normalization
    {E F : Type} [IntModule E] [IntModule F]
    (e : E) (f : F)
    (order_e : (109 : Int) • e=0) (order_f : (113 : Int) • f=0) :
    (4 : Int) • ((55 : Int) • e)=(2 : Int) • e ∧
    (4 : Int) • ((57 : Int) • f)=(2 : Int) • f := by
  constructor <;> grind

theorem norm_diagram_uniqueness
    {C J A : Type} [IntModule J]
    (norm : J → A) (pull : A → J)
    (composition : ∀ x, pull (norm x)=(4 : Int) • x)
    (order : ∀ x : J, (12317 : Int) • x=0)
    (f g : C → J) (same_diagram : ∀ x, norm (f x)=norm (g x)) :
    ∀ x, f x=g x := by
  intro x
  have hx := order (f x)
  have hy := order (g x)
  have hfour : (4 : Int) • f x=(4 : Int) • g x := by
    rw [← composition, ← composition, same_diagram]
  have rx : (9238 : Int) • ((4 : Int) • f x)=f x := by grind
  have ry : (9238 : Int) • ((4 : Int) • g x)=g x := by grind
  rw [← rx, ← ry, hfour]

/- The map hypotheses are the separate norm/pullback and elliptic dual
facts, not an assumed inverse. The proof derives both inverse directions
with the different 104/85 components. Actual curve interpretations and
joint norm injectivity still require the written/native bridges. -/
theorem conditional_two_way_inverse
    {C T E E2 F : Type} [IntModule E] [IntModule E2] [IntModule F]
    (n0 : C → E) (n1 : C → F) (m0 : T → E2) (m1 : T → F)
    (alpha : E → E2) (beta : E2 → E)
    (forward : C → T) (reverse : T → C)
    (n_injective : ∀ x y, n0 x=n0 y → n1 x=n1 y → x=y)
    (m_injective : ∀ x y, m0 x=m0 y → m1 x=m1 y → x=y)
    (order_e : ∀ x : E, (109 : Int) • x=0)
    (order_e2 : ∀ x : E2, (109 : Int) • x=0)
    (order_f : ∀ x : F, (113 : Int) • x=0)
    (alpha_linear : ∀ (k : Int) x, alpha (k • x)=k • alpha x)
    (beta_linear : ∀ (k : Int) x, beta (k • x)=k • beta x)
    (beta_alpha : ∀ x, beta (alpha x)=(49 : Int) • x)
    (alpha_beta : ∀ x, alpha (beta x)=(49 : Int) • x)
    (forward0 : ∀ x, m0 (forward x)=(2 : Int) • alpha (n0 x))
    (forward1 : ∀ x, m1 (forward x)=(2 : Int) • n1 x)
    (reverse0 : ∀ t, n0 (reverse t)=(2 : Int) • ((104 : Int) • beta (m0 t)))
    (reverse1 : ∀ t, n1 (reverse t)=(2 : Int) • ((85 : Int) • m1 t)) :
    (∀ x, reverse (forward x)=x) ∧ (∀ t, forward (reverse t)=t) := by
  constructor
  · intro x
    apply n_injective
    · rw [reverse0, forward0, beta_linear, beta_alpha]
      have h := order_e (n0 x)
      grind
    · rw [reverse1, forward1]
      have h := order_f (n1 x)
      grind
  · intro t
    apply m_injective
    · rw [forward0, reverse0, alpha_linear, alpha_linear, alpha_beta]
      have h := order_e2 (m0 t)
      grind
    · rw [forward1, reverse1]
      have h := order_f (m1 t)
      grind

end PrimeFieldChain
#print axioms PrimeFieldChain.actual_c0_first_cover
#print axioms PrimeFieldChain.actual_c0_reciprocal_cover
#print axioms PrimeFieldChain.actual_repeated_finite_fibre
#print axioms PrimeFieldChain.actual_empty_finite_fibre_and_infinity_targets
#print axioms PrimeFieldChain.completed_degree_two_balanced_accounting
#print axioms PrimeFieldChain.actual_public_constants
#print axioms PrimeFieldChain.nonuniform_component_recovery
#print axioms PrimeFieldChain.inverse_norm_component_recovery
#print axioms PrimeFieldChain.forward_component_normalization
#print axioms PrimeFieldChain.norm_diagram_uniqueness
#print axioms PrimeFieldChain.conditional_two_way_inverse
