import Std
import Init.Grind.Ring.Basic

open Lean.Grind

namespace QuotientGate

/-- An exact two-family point sum survives every label-membership filter,
    including a label with collisions. -/
theorem sound_two_family_filter {G : Type} {L : Type} [AddCommGroup G]
    (label : G → L) (target suffix : G) (A B : G → Prop)
    (witness : ∃ a, A a ∧ ∃ b, B b ∧ target = suffix + (a + b)) :
    ∃ a, A a ∧ ∃ b, B b ∧ label (target - suffix) = label (a + b) := by
  obtain ⟨a, ha, b, hb, hsum⟩ := witness
  refine ⟨a, ha, b, hb, ?_⟩
  congr 1
  rw [hsum]
  rw [AddCommMonoid.add_comm suffix (a + b)]
  exact AddCommGroup.add_sub_cancel

/-- A finite list of scalar-weighted feature functions. -/
def featureCombination {F : Type} [Field F] {n : Nat} :
    List (F × (Fin n → F)) → (Fin n → F)
  | [] => fun _ => 0
  | (coefficient, feature) :: rest =>
      fun i => coefficient * feature i + featureCombination rest i

/-- A linear functional that vanishes on every feature also vanishes on
    every finite feature combination. A nonzero label syndrome excludes
    a degree-two expression when the features are 1, x_i, x_i*x_j. -/
theorem finite_feature_separation {F : Type} [Field F] {n : Nat}
    (functional : (Fin n → F) → F) (label : Fin n → F)
    (terms : List (F × (Fin n → F)))
    (hzero : functional (fun _ => 0) = 0)
    (hadd : ∀ u v, functional (fun i => u i + v i) =
      functional u + functional v)
    (hscale : ∀ c u, functional (fun i => c * u i) = c * functional u)
    (hfeatures : ∀ term ∈ terms, functional term.2 = 0)
    (hlabel : functional label ≠ 0) :
    label ≠ featureCombination terms := by
  have hvanish : ∀ ts : List (F × (Fin n → F)),
      (∀ term ∈ ts, functional term.2 = 0) →
      functional (featureCombination ts) = 0 := by
    intro ts
    induction ts with
    | nil =>
        intro _
        exact hzero
    | cons term rest ih =>
        intro h
        have hhead : functional term.2 = 0 := h term (by simp)
        have hrest : ∀ t ∈ rest, functional t.2 = 0 := by
          intro t ht
          exact h t (by simp [ht])
        have htail := ih hrest
        change functional (fun i => term.1 * term.2 i +
          featureCombination rest i) = 0
        rw [hadd, hscale, hhead, htail]
        grind +ring
  intro heq
  apply hlabel
  rw [heq]
  exact hvanish terms hfeatures

/-- Solving the Artin–Schreier equation for `v` gives a point `(x,x*v)`
    on the binary model `y²+xy=x³+1`, provided `x` is invertible. -/
theorem artin_schreier_curve_lift {F : Type} [Field F]
    (x v invx2 : F)
    (hinv : x * x * invx2 = 1)
    (hsolve : v * v + v = x + invx2) :
    (x * v) * (x * v) + x * (x * v) = x * x * x + 1 := by
  grind +ring

#print axioms sound_two_family_filter
#print axioms finite_feature_separation
#print axioms artin_schreier_curve_lift

end QuotientGate
