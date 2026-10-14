import Std

/-! Root offset of a characteristic-two quadratic, under explicit ring laws. -/
namespace RootOffset

structure BinaryCommRing (F : Type) where
  add : F → F → F
  mul : F → F → F
  zero : F
  add_assoc : ∀ x y z, add (add x y) z = add x (add y z)
  add_comm : ∀ x y, add x y = add y x
  add_self : ∀ x, add x x = zero
  zero_add : ∀ x, add zero x = x
  mul_assoc : ∀ x y z, mul (mul x y) z = mul x (mul y z)
  mul_comm : ∀ x y, mul x y = mul y x
  mul_add : ∀ x y z, mul x (add y z) = add (mul x y) (mul x z)

variable {F : Type} (R : BinaryCommRing F)

private theorem add_zero (x : F) : R.add x R.zero = x := by
  rw [R.add_comm, R.zero_add]

private theorem add_mul (x y z : F) :
    R.mul (R.add x y) z = R.add (R.mul x z) (R.mul y z) := by
  calc
    R.mul (R.add x y) z = R.mul z (R.add x y) := R.mul_comm _ _
    _ = R.add (R.mul z x) (R.mul z y) := R.mul_add z x y
    _ = R.add (R.mul x z) (R.mul y z) := by rw [R.mul_comm z x, R.mul_comm z y]

private theorem square_add (a d : F) :
    R.mul (R.add a d) (R.add a d) = R.add (R.mul a a) (R.mul d d) := by
  let aa := R.mul a a
  let ad := R.mul a d
  let da := R.mul d a
  let dd := R.mul d d
  have cross : R.add ad da = R.zero := by
    dsimp [ad, da]
    rw [R.mul_comm d a, R.add_self]
  calc
    R.mul (R.add a d) (R.add a d) =
      R.add (R.mul a (R.add a d)) (R.mul d (R.add a d)) := add_mul R a d _
    _ = R.add (R.add aa ad) (R.add da dd) := by
      dsimp [aa, ad, da, dd]
      rw [R.mul_add, R.mul_add]
    _ = R.add aa (R.add ad (R.add da dd)) := R.add_assoc aa ad _
    _ = R.add aa (R.add (R.add ad da) dd) := by rw [← R.add_assoc ad da dd]
    _ = R.add aa (R.add dd (R.add ad da)) := by rw [R.add_comm (R.add ad da) dd]
    _ = R.add (R.add aa dd) (R.add ad da) := (R.add_assoc aa dd _).symm
    _ = R.add (R.add aa dd) R.zero := by rw [cross]
    _ = R.add aa dd := add_zero R _

def quadratic (C p h a : F) : F :=
  R.add (R.add (R.mul C (R.mul a a)) (R.mul p a)) h

theorem root_shift (C p h a d : F)
    (hd : R.mul C d = p)
    (ha : quadratic R C p h a = R.zero) :
    quadratic R C p h (R.add a d) = R.zero := by
  have hdelta : R.add (R.mul C (R.mul d d)) (R.mul p d) = R.zero := by
    calc
      R.add (R.mul C (R.mul d d)) (R.mul p d) =
        R.add (R.mul (R.mul C d) d) (R.mul p d) := by rw [R.mul_assoc]
      _ = R.add (R.mul p d) (R.mul p d) := by rw [hd]
      _ = R.zero := R.add_self _
  have hshift : quadratic R C p h (R.add a d) =
      R.add (quadratic R C p h a)
        (R.add (R.mul C (R.mul d d)) (R.mul p d)) := by
    unfold quadratic
    rw [square_add R a d, R.mul_add, R.mul_add]
    let A := R.mul C (R.mul a a)
    let B := R.mul p a
    let D := R.mul C (R.mul d d)
    let E := R.mul p d
    change R.add (R.add (R.add A D) (R.add B E)) h =
      R.add (R.add (R.add A B) h) (R.add D E)
    calc
      R.add (R.add (R.add A D) (R.add B E)) h =
        R.add (R.add (R.add A B) (R.add D E)) h := by
          congr 1
          calc
            R.add (R.add A D) (R.add B E) = R.add A (R.add D (R.add B E)) := R.add_assoc A D _
            _ = R.add A (R.add B (R.add D E)) := by
              rw [← R.add_assoc D B E, R.add_comm D B, R.add_assoc B D E]
            _ = R.add (R.add A B) (R.add D E) := (R.add_assoc A B _).symm
      _ = R.add (R.add A B) (R.add (R.add D E) h) := R.add_assoc _ _ _
      _ = R.add (R.add A B) (R.add h (R.add D E)) := by rw [R.add_comm (R.add D E) h]
      _ = R.add (R.add (R.add A B) h) (R.add D E) := (R.add_assoc _ _ _).symm
  rw [hshift, ha, hdelta, R.zero_add]

#print axioms RootOffset.root_shift
end RootOffset
