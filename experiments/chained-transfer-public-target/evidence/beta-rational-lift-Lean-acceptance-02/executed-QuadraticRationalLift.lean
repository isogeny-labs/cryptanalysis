import Std.Tactic

/-! Conditional group-theoretic rational lifting. These are ordinary group and
homomorphism laws; no actual Picard/Weil-restriction bridge is assumed proved. -/
set_option autoImplicit false
namespace QuadraticRationalLift

structure Abelian (A : Type) where
  add : A → A → A
  zero : A
  neg : A → A
  assoc : ∀ a b c, add (add a b) c = add a (add b c)
  comm : ∀ a b, add a b = add b a
  zero_right : ∀ a, add a zero = a
  neg_right : ∀ a, add a (neg a) = zero

structure Hom {A B : Type} (g : Abelian A) (h : Abelian B) where
  toFun : A → B
  add_map : ∀ a b, toFun (g.add a b) = h.add (toFun a) (toFun b)
  zero_map : toFun g.zero = h.zero
  neg_map : ∀ a, toFun (g.neg a) = h.neg (toFun a)

theorem zero_left {A : Type} (g : Abelian A) (a : A) :
    g.add g.zero a = a := (g.comm _ _).trans (g.zero_right _)

theorem neg_left {A : Type} (g : Abelian A) (a : A) :
    g.add (g.neg a) a = g.zero := (g.comm _ _).trans (g.neg_right _)

theorem quadratic_fixed_lift {A J : Type} (g : Abelian A) (h : Abelian J)
    (phi : Hom g h) (FA : Hom g g) (FJ : Hom h h)
    (commutes : ∀ a, phi.toFun (FA.toFun a) = FJ.toFun (phi.toFun a))
    (surjective : ∀ x, ∃ a, phi.toFun a = x)
    (kernel_two : ∀ c, phi.toFun c = h.zero → g.add c c = g.zero)
    (kernel_cube : ∀ c, phi.toFun c = h.zero →
      FA.toFun (FA.toFun (FA.toFun c)) = c)
    (x : J) (fixed : FJ.toFun x = x) :
    ∃ b, phi.toFun b = x ∧ FA.toFun (FA.toFun b) = b := by
  obtain ⟨a, ha⟩ := surjective x
  let c := g.add (FA.toFun a) (g.neg a)
  have hc : phi.toFun c = h.zero := by
    change phi.toFun (g.add (FA.toFun a) (g.neg a)) = h.zero
    rw [phi.add_map, commutes, phi.neg_map, ha, fixed, h.neg_right]
  have hc2 : g.add c c = g.zero := kernel_two c hc
  have hc3 : FA.toFun (FA.toFun (FA.toFun c)) = c := kernel_cube c hc
  have hfa : FA.toFun a = g.add a c := by
    symm
    change g.add a (g.add (FA.toFun a) (g.neg a)) = FA.toFun a
    calc
      _ = g.add (g.add a (FA.toFun a)) (g.neg a) := (g.assoc _ _ _).symm
      _ = g.add (g.add (FA.toFun a) a) (g.neg a) := by rw [g.comm a (FA.toFun a)]
      _ = g.add (FA.toFun a) (g.add a (g.neg a)) := g.assoc _ _ _
      _ = FA.toFun a := by rw [g.neg_right, g.zero_right]
  refine ⟨g.add a (FA.toFun c), ?_, ?_⟩
  · rw [phi.add_map, commutes, hc, FJ.zero_map, h.zero_right, ha]
  · rw [FA.add_map, FA.add_map, hc3, hfa, FA.add_map, hfa]
    rw [g.assoc a c (FA.toFun c), g.assoc a (g.add c (FA.toFun c)) c]
    rw [g.comm c (FA.toFun c), g.assoc (FA.toFun c) c c, hc2, g.zero_right]

theorem lift_images_equal {A J T : Type}
    (g : Abelian A) (h : Abelian J) (t : Abelian T)
    (phi : Hom g h) (psi : Hom g t)
    (kernel_containment : ∀ c, phi.toFun c = h.zero → psi.toFun c = t.zero)
    (a b : A) (same : phi.toFun a = phi.toFun b) :
    psi.toFun a = psi.toFun b := by
  have hc : phi.toFun (g.add a (g.neg b)) = h.zero := by
    rw [phi.add_map, phi.neg_map, same, h.neg_right]
  have hp : t.add (psi.toFun a) (t.neg (psi.toFun b)) = t.zero := by
    rw [← psi.neg_map, ← psi.add_map]
    exact kernel_containment _ hc
  calc
    psi.toFun a = t.add (psi.toFun a) (t.add (t.neg (psi.toFun b)) (psi.toFun b)) := by
      rw [neg_left, t.zero_right]
    _ = t.add (t.add (psi.toFun a) (t.neg (psi.toFun b))) (psi.toFun b) :=
      (t.assoc _ _ _).symm
    _ = t.add t.zero (psi.toFun b) := by rw [hp]
    _ = psi.toFun b := zero_left _ _

theorem four_torsion_lift_bound {A J : Type} (g : Abelian A)
    (phi : A → J) (N : J → A)
    (norm_pullback : ∀ a, N (phi a) = g.add a a)
    (x : J) (norm_exponent_two : g.add (N x) (N x) = g.zero)
    (a : A) (lift : phi a = x) :
    g.add (g.add a a) (g.add a a) = g.zero := by
  have doubled : N x = g.add a a := by rw [← lift, norm_pullback]
  rw [← doubled]
  exact norm_exponent_two

theorem quadratic_kernel_fixed_is_rational {A : Type} (F : A → A) (c : A)
    (cube : F (F (F c)) = c) (quadratic : F (F c) = c) : F c = c := by
  calc
    F c = F (F (F c)) := congrArg F quadratic.symm
    _ = c := cube

/- A finite-group control: dropping the odd-period kernel hypothesis may fail.
The computation is kernel checked `decide`, not native evaluation. -/
-- Fin8 encodes (a,b) in C4 x C2 by a+4*b; every finite binder is computable.
abbrev Toy := Fin 8
def toyOf (a b : Nat) : Toy := ⟨a % 4 + 4 * (b % 2), by omega⟩
def toyAdd (a b : Toy) : Toy := toyOf (a.val % 4 + b.val % 4) (a.val / 4 + b.val / 4)
def toyF (a : Toy) : Toy := toyOf (a.val % 4 + 2 * (a.val / 4)) (a.val / 4 + a.val % 4)
def toyPhi (a : Toy) : Fin 2 := ⟨a.val % 2, by omega⟩

set_option maxRecDepth 10000 in
set_option maxHeartbeats 4000000 in
theorem finite_group_hypothesis_control :
    (∀ a b c : Toy, toyAdd (toyAdd a b) c = toyAdd a (toyAdd b c)) ∧
    (∀ a b : Toy, toyAdd a b = toyAdd b a) ∧
    (∀ a : Toy, toyAdd a 0 = a) ∧
    (∀ a : Toy, ∃ b, toyAdd a b = 0) ∧
    (∀ a b : Toy, toyF (toyAdd a b) = toyAdd (toyF a) (toyF b)) ∧
    (∀ b : Toy, ∃ a, toyF a = b) ∧
    (∀ x : Fin 2, ∃ a : Toy, toyPhi a = x) ∧
    (∀ a b : Toy, toyPhi (toyAdd a b) = toyPhi a + toyPhi b) ∧
    (∀ a : Toy, toyPhi (toyF a) = toyPhi a) ∧
    (∀ c : Toy, toyPhi c = 0 → toyAdd c c = 0) ∧
    (∃ c : Toy, toyPhi c = 0 ∧ toyF (toyF (toyF c)) ≠ c) ∧
    (∀ a : Toy, toyPhi a = 1 → toyF (toyF a) ≠ a) := by decide

end QuadraticRationalLift
