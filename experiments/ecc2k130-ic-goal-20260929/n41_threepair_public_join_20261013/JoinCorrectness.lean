import Std

/-! The residual-search identity for any commutative point group. The standard
    group laws are explicit hypotheses; no curve-specific algebra is assumed. -/
namespace ThreePairJoin

structure Laws (G : Type) where
  op : G → G → G
  neg : G → G
  zero : G
  assoc : ∀ x y z : G, op (op x y) z = op x (op y z)
  comm : ∀ x y : G, op x y = op y x
  leftInv : ∀ x : G, op (neg x) x = zero
  leftId : ∀ x : G, op zero x = x

variable {G : Type}

private theorem rightId (g : Laws G) (x : G) : g.op x g.zero = x := by
  rw [g.comm x g.zero, g.leftId x]

private theorem rightInv (g : Laws G) (x : G) : g.op x (g.neg x) = g.zero := by
  rw [g.comm x (g.neg x), g.leftInv x]

private theorem cancelPosNeg (g : Laws G) (x y : G) :
    g.op (g.op x y) (g.neg y) = x := by
  rw [g.assoc x y (g.neg y), rightInv g y, rightId g x]

private theorem cancelNegPos (g : Laws G) (x y : G) :
    g.op (g.op x (g.neg y)) y = x := by
  rw [g.assoc x (g.neg y) y, g.leftInv y, rightId g x]

private theorem shuffle (g : Laws G) (x y z : G) :
    g.op (g.op x y) z = g.op (g.op x z) y := by
  rw [g.assoc x y z, g.comm y z, ← g.assoc x z y]

def residual (g : Laws G) (q a b : G) : G :=
  g.op (g.op q (g.neg a)) (g.neg b)

theorem residual_of_sum (g : Laws G) (a b c : G) :
    residual g (g.op (g.op a b) c) a b = c := by
  unfold residual
  calc
    g.op (g.op (g.op (g.op a b) c) (g.neg a)) (g.neg b)
        = g.op (g.op (g.op (g.op b a) c) (g.neg a)) (g.neg b) := by rw [g.comm a b]
    _ = g.op (g.op (g.op (g.op b c) a) (g.neg a)) (g.neg b) := by rw [shuffle g b a c]
    _ = g.op (g.op b c) (g.neg b) := by rw [cancelPosNeg g (g.op b c) a]
    _ = g.op (g.op c b) (g.neg b) := by rw [g.comm b c]
    _ = c := cancelPosNeg g c b

theorem sum_of_residual (g : Laws G) (q a b c : G)
    (hit : residual g q a b = c) : g.op (g.op a b) c = q := by
  have recover : g.op (g.op (residual g q a b) b) a = q := by
    unfold residual
    rw [cancelNegPos g (g.op q (g.neg a)) b]
    exact cancelNegPos g q a
  calc
    g.op (g.op a b) c = g.op (g.op a b) (residual g q a b) := by rw [hit]
    _ = g.op (residual g q a b) (g.op a b) := g.comm _ _
    _ = g.op (g.op (residual g q a b) a) b := (g.assoc _ _ _).symm
    _ = g.op (g.op (residual g q a b) b) a := shuffle g _ _ _
    _ = q := recover

theorem residual_hit_iff (g : Laws G) (q a b c : G) :
    residual g q a b = c ↔ g.op (g.op a b) c = q := by
  constructor
  · exact sum_of_residual g q a b c
  · intro h
    rw [← h]
    exact residual_of_sum g a b c

#print axioms ThreePairJoin.residual_hit_iff

end ThreePairJoin
