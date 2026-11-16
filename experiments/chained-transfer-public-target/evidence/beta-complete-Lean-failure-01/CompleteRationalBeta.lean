import Std.Tactic

/-! Conditional group-theoretic rational lifting. These are ordinary group and
homomorphism laws; no actual Picard/Weil-restriction bridge is assumed proved. -/
set_option autoImplicit false
namespace CompleteRationalBeta

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

-- Natural multiplication is defined from ordinary addition, not an assumed API.
def nsmul {A : Type} (g : Abelian A) : Nat → A → A
  | 0, _ => g.zero
  | n + 1, x => g.add (nsmul g n x) x

theorem nsmul_zero {A : Type} (g : Abelian A) (n : Nat) :
    nsmul g n g.zero = g.zero := by
  induction n with
  | zero => rfl
  | succ n ih => simp only [nsmul, ih, g.zero_right]

theorem nsmul_add {A : Type} (g : Abelian A) (m n : Nat) (x : A) :
    nsmul g (m + n) x = g.add (nsmul g m x) (nsmul g n x) := by
  induction n with
  | zero => simp only [Nat.add_zero, nsmul, g.zero_right]
  | succ n ih => simp only [Nat.add_succ, nsmul, ih, g.assoc]

theorem nsmul_mul {A : Type} (g : Abelian A) (m n : Nat) (x : A) :
    nsmul g (m * n) x = nsmul g m (nsmul g n x) := by
  induction m with
  | zero => simp only [Nat.zero_mul, nsmul]
  | succ m ih => rw [Nat.succ_mul, nsmul_add, ih]; rfl

theorem add_shuffle {A : Type} (g : Abelian A) (a b c d : A) :
    g.add (g.add a b) (g.add c d) = g.add (g.add a c) (g.add b d) := by
  rw [g.assoc a b (g.add c d), ← g.assoc b c d, g.comm b c,
    g.assoc c b d, ← g.assoc a c (g.add b d)]

theorem nsmul_addpoint {A : Type} (g : Abelian A) (n : Nat) (a b : A) :
    nsmul g n (g.add a b) = g.add (nsmul g n a) (nsmul g n b) := by
  induction n with
  | zero => simp only [nsmul, g.zero_right]
  | succ n ih => simp only [nsmul, ih, add_shuffle]

theorem inverse_unique {A : Type} (g : Abelian A) (a b : A)
    (right_inverse : g.add a b = g.zero) : b = g.neg a := by
  calc
    b = g.add g.zero b := (zero_left g b).symm
    _ = g.add (g.add (g.neg a) a) b := by rw [neg_left]
    _ = g.add (g.neg a) (g.add a b) := g.assoc _ _ _
    _ = g.neg a := by rw [right_inverse, g.zero_right]

theorem neg_zero {A : Type} (g : Abelian A) : g.neg g.zero = g.zero := by
  have h := g.neg_right g.zero
  simpa only [zero_left] using h

theorem neg_add {A : Type} (g : Abelian A) (a b : A) :
    g.neg (g.add a b) = g.add (g.neg a) (g.neg b) := by
  symm
  apply inverse_unique
  rw [add_shuffle, g.neg_right, g.neg_right, g.zero_right]

theorem nsmul_neg {A : Type} (g : Abelian A) (n : Nat) (x : A) :
    nsmul g n (g.neg x) = g.neg (nsmul g n x) := by
  induction n with
  | zero => simp only [nsmul, neg_zero]
  | succ n ih => simp only [nsmul, ih, neg_add]

theorem hom_nsmul {A B : Type} (g : Abelian A) (h : Abelian B)
    (f : Hom g h) (n : Nat) (x : A) :
    f.toFun (nsmul g n x) = nsmul h n (f.toFun x) := by
  induction n with
  | zero => exact f.zero_map
  | succ n ih => simp only [nsmul, f.add_map, ih]

theorem double_as_nsmul {A : Type} (g : Abelian A) (x : A) :
    g.add x x = nsmul g 2 x := by simp only [nsmul, zero_left]

theorem rational_decomposition {A : Type} (g : Abelian A) (ell m : Nat)
    (ell_form : ell = 4 * m + 1) (x : A)
    (annihilated : nsmul g (4 * ell) x = g.zero) :
    nsmul g 4 (nsmul g ell x) = g.zero ∧
    nsmul g ell (g.add x (g.neg (nsmul g ell x))) = g.zero ∧
    g.add (g.add x (g.neg (nsmul g ell x))) (nsmul g ell x) = x := by
  let x2 := nsmul g ell x
  have four : nsmul g 4 x2 = g.zero := by
    change nsmul g 4 (nsmul g ell x) = g.zero
    rw [← nsmul_mul]
    exact annihilated
  have killed_multiple : nsmul g (4 * m) x2 = g.zero := by
    rw [Nat.mul_comm 4 m, nsmul_mul, four, nsmul_zero]
  have ell_two : nsmul g ell x2 = x2 := by
    calc
      nsmul g ell x2 = g.add (nsmul g (4 * m) x2) x2 := by
        conv_lhs => rw [ell_form]
        rfl
      _ = x2 := by rw [killed_multiple, zero_left]
  refine ⟨four, ?_, ?_⟩
  · change nsmul g ell (g.add x (g.neg x2)) = g.zero
    rw [nsmul_addpoint, nsmul_neg, ell_two]
    exact g.neg_right x2
  · change g.add (g.add x (g.neg x2)) x2 = x
    rw [g.assoc, neg_left, g.zero_right]

theorem odd_half {J T : Type} (g : Abelian J) (h : Abelian T)
    (beta : Hom g h) (F : J → T)
    (twice_beta : ∀ x, F x = h.add (beta.toFun x) (beta.toFun x))
    (ell inv : Nat) (inverse : 2 * inv = ell + 1)
    (x : J) (odd : nsmul g ell x = g.zero) :
    nsmul h inv (F x) = beta.toFun x := by
  have killed : nsmul h ell (beta.toFun x) = h.zero := by
    rw [← hom_nsmul, odd, beta.zero_map]
  calc
    nsmul h inv (F x) = nsmul h inv (nsmul h 2 (beta.toFun x)) := by
      rw [twice_beta, double_as_nsmul]
    _ = nsmul h (inv * 2) (beta.toFun x) := (nsmul_mul _ _ _ _).symm
    _ = nsmul h (ell + 1) (beta.toFun x) := by rw [Nat.mul_comm inv 2, inverse]
    _ = h.add (nsmul h ell (beta.toFun x)) (beta.toFun x) := rfl
    _ = beta.toFun x := by rw [killed, zero_left]

-- The actual geometric quotient/norm identities are EXPLICIT hypotheses.
-- The runtime expression never calls beta, which is the comparison homomorphism.
structure Config (A J T : Type) where
  a : Abelian A
  g : Abelian J
  h : Abelian T
  phi : Hom a g
  psi : Hom a h
  beta : Hom g h
  F : J → T
  lift : J → A
  ell : Nat
  m : Nat
  inv : Nat
  ell_form : ell = 4 * m + 1
  inverse : 2 * inv = ell + 1
  order : ∀ x, nsmul g (4 * ell) x = g.zero
  quotient : ∀ a, beta.toFun (phi.toFun a) = psi.toFun a
  twice_beta : ∀ x, F x = h.add (beta.toFun x) (beta.toFun x)
  cofactor_lift : ∀ t, nsmul g 4 t = g.zero → phi.toFun (lift t) = t

def evaluate {A J T : Type} (c : Config A J T) (x : J) : T :=
  let x2 := nsmul c.g c.ell x
  let xo := c.g.add x (c.g.neg x2)
  c.h.add (nsmul c.h c.inv (c.F xo)) (c.psi.toFun (c.lift x2))

theorem evaluate_matches_beta {A J T : Type} (c : Config A J T) (x : J) :
    evaluate c x = c.beta.toFun x := by
  obtain ⟨four, odd, split⟩ := rational_decomposition c.g c.ell c.m c.ell_form x (c.order x)
  have lift_image : c.psi.toFun (c.lift (nsmul c.g c.ell x)) =
      c.beta.toFun (nsmul c.g c.ell x) := by
    rw [← c.quotient, c.cofactor_lift _ four]
  change c.h.add (nsmul c.h c.inv (c.F (c.g.add x (c.g.neg (nsmul c.g c.ell x)))))
    (c.psi.toFun (c.lift (nsmul c.g c.ell x))) = _
  rw [odd_half c.g c.h c.beta c.F c.twice_beta c.ell c.inv c.inverse _ odd,
    lift_image, ← c.beta.add_map, split]

theorem dlp_preservation {A J T : Type} (c : Config A J T) (G : J) (n : Nat) :
    evaluate c (nsmul c.g n G) = nsmul c.h n (evaluate c G) := by
  rw [evaluate_matches_beta, evaluate_matches_beta, hom_nsmul]

theorem full_rational_inverse13 {J T : Type} (g : Abelian J) (h : Abelian T)
    (beta : Hom g h) (dual : Hom h g)
    (composition : ∀ x, dual.toFun (beta.toFun x) = nsmul g 13 x)
    (order : ∀ x, nsmul g 11092292 x = g.zero) (x : J) :
    nsmul g 3413013 (dual.toFun (beta.toFun x)) = x := by
  have killed : nsmul g (11092292 * 4) x = g.zero := by
    rw [Nat.mul_comm 11092292 4, nsmul_mul, order, nsmul_zero]
  have coefficient : 3413013 * 13 = 11092292 * 4 + 1 := by decide
  calc
    nsmul g 3413013 (dual.toFun (beta.toFun x)) = nsmul g 3413013 (nsmul g 13 x) := by rw [composition]
    _ = nsmul g (3413013 * 13) x := (nsmul_mul _ _ _ _).symm
    _ = nsmul g (11092292 * 4 + 1) x := by rw [coefficient]
    _ = g.add (nsmul g (11092292 * 4) x) x := rfl
    _ = x := by rw [killed, zero_left]

end CompleteRationalBeta
