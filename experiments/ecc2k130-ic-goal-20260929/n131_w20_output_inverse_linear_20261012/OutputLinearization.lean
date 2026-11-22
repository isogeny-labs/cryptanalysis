import Std

/-! The characteristic-two pair equation is equivalent to a linear
source-product equation once the output inverse witness is checked. -/
namespace OutputLinearization

structure BinaryCommRing (F : Type) where
  add : F → F → F
  mul : F → F → F
  zero : F
  one : F
  add_assoc : ∀ x y z, add (add x y) z = add x (add y z)
  add_comm : ∀ x y, add x y = add y x
  add_self : ∀ x, add x x = zero
  zero_add : ∀ x, add zero x = x
  mul_assoc : ∀ x y z, mul (mul x y) z = mul x (mul y z)
  mul_comm : ∀ x y, mul x y = mul y x
  one_mul : ∀ x, mul one x = x
  mul_zero : ∀ x, mul x zero = zero
  mul_add : ∀ x y z, mul x (add y z) = add (mul x y) (mul x z)

variable {F : Type} (R : BinaryCommRing F)

private theorem add_zero (x : F) : R.add x R.zero = x := by
  calc
    R.add x R.zero = R.add R.zero x := R.add_comm x R.zero
    _ = x := R.zero_add x

private theorem mul_one (x : F) : R.mul x R.one = x := by
  calc
    R.mul x R.one = R.mul R.one x := R.mul_comm x R.one
    _ = x := R.one_mul x

private theorem xor_zero_iff_eq (x y : F) :
    R.add x y = R.zero ↔ x = y := by
  constructor
  · intro h
    calc
      x = R.add x R.zero := (add_zero R x).symm
      _ = R.add x (R.add x y) := congrArg (R.add x) h.symm
      _ = R.add (R.add x x) y := (R.add_assoc x x y).symm
      _ = R.add R.zero y := congrArg (fun z => R.add z y) (R.add_self x)
      _ = y := R.zero_add y
  · intro h
    rw [h]
    exact R.add_self y

private theorem mul_cancel_zero (a b s : F)
    (hab : R.mul a b = R.one)
    (has : R.mul a s = R.zero) : s = R.zero := by
  calc
    s = R.mul R.one s := (R.one_mul s).symm
    _ = R.mul (R.mul b a) s :=
      congrArg (fun z => R.mul z s) ((R.mul_comm b a).trans hab).symm
    _ = R.mul b (R.mul a s) := R.mul_assoc b a s
    _ = R.mul b R.zero := congrArg (R.mul b) has
    _ = R.zero := R.mul_zero b

theorem pair_output_linear_iff (a b p c h : F)
    (hab : R.mul a b = R.one) :
    R.add (R.add (R.mul a p) (R.mul c (R.mul a a))) h = R.zero ↔
      p = R.add (R.mul c a) (R.mul h b) := by
  have hca : R.mul a (R.mul c a) = R.mul c (R.mul a a) := by
    calc
      R.mul a (R.mul c a) = R.mul (R.mul a c) a :=
        (R.mul_assoc a c a).symm
      _ = R.mul (R.mul c a) a :=
        congrArg (fun z => R.mul z a) (R.mul_comm a c)
      _ = R.mul c (R.mul a a) := R.mul_assoc c a a
  have hhb : R.mul a (R.mul h b) = h := by
    calc
      R.mul a (R.mul h b) = R.mul (R.mul a h) b :=
        (R.mul_assoc a h b).symm
      _ = R.mul (R.mul h a) b :=
        congrArg (fun z => R.mul z b) (R.mul_comm a h)
      _ = R.mul h (R.mul a b) := R.mul_assoc h a b
      _ = R.mul h R.one := congrArg (R.mul h) hab
      _ = h := mul_one R h
  have hpoly :
      R.mul a (R.add p (R.add (R.mul c a) (R.mul h b))) =
        R.add (R.add (R.mul a p) (R.mul c (R.mul a a))) h := by
    calc
      R.mul a (R.add p (R.add (R.mul c a) (R.mul h b))) =
          R.add (R.mul a p) (R.mul a (R.add (R.mul c a) (R.mul h b))) :=
        R.mul_add a p _
      _ = R.add (R.mul a p)
            (R.add (R.mul a (R.mul c a)) (R.mul a (R.mul h b))) :=
        congrArg (R.add (R.mul a p)) (R.mul_add a _ _)
      _ = R.add (R.mul a p) (R.add (R.mul c (R.mul a a)) h) := by
        rw [hca, hhb]
      _ = R.add (R.add (R.mul a p) (R.mul c (R.mul a a))) h :=
        (R.add_assoc _ _ _).symm
  constructor
  · intro old
    have hs : R.add p (R.add (R.mul c a) (R.mul h b)) = R.zero :=
      mul_cancel_zero R a b _ hab (hpoly.trans old)
    exact (xor_zero_iff_eq R p _).mp hs
  · intro linear
    have hs : R.add p (R.add (R.mul c a) (R.mul h b)) = R.zero :=
      (xor_zero_iff_eq R p _).mpr linear
    calc
      R.add (R.add (R.mul a p) (R.mul c (R.mul a a))) h =
          R.mul a (R.add p (R.add (R.mul c a) (R.mul h b))) :=
        hpoly.symm
      _ = R.mul a R.zero := congrArg (R.mul a) hs
      _ = R.zero := R.mul_zero a

#print axioms OutputLinearization.pair_output_linear_iff

end OutputLinearization
