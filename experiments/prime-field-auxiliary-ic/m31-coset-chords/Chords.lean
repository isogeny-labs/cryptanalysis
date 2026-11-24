import Mathlib.AlgebraicGeometry.EllipticCurve.Affine.Point
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.Tactic

namespace M31CosetChords
open WeierstrassCurve.Affine

theorem separated {A : Type*} [AddCommGroup A] {t g : A} {m : ℕ}
    (ht : m • t ≠ 0) (hg : m • g = 0) (i j : ℕ) :
    t + i • g ≠ j • g ∧ t + i • g ≠ -(j • g) := by
  have kill (k : ℕ) : m • (k • g) = 0 := by rw [smul_comm, hg, smul_zero]
  constructor <;> intro h <;> apply ht
  · simpa only [nsmul_add, kill, add_zero] using congrArg (m • ·) h
  · simpa only [nsmul_add, kill, add_zero, smul_neg, neg_zero] using congrArg (m • ·) h

theorem distinct_x {K : Type*} [Field K] [DecidableEq K] {w : WeierstrassCurve.Affine K}
    {x y u v : K} (hp : w.Nonsingular x y) (hq : w.Nonsingular u v)
    (hne : Point.some hp ≠ Point.some hq) (hop : Point.some hp ≠ -Point.some hq) : x ≠ u := by
  rintro rfl
  rcases Y_eq_of_X_eq hp.1 hq.1 rfl with a | b
  · subst v
    exact hne rfl
  · apply hop
    rw [Point.neg_some, Point.some.injEq]
    exact ⟨rfl,b⟩

abbrev F := ZMod 2147483647
instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩
def E : WeierstrassCurve.Affine F := ⟨0,0,0,1,0⟩

private theorem valid (x y : F) (h : y^2=x^3+x) (hy : y ≠ 0) : E.Nonsingular x y := by
  rw [WeierstrassCurve.Affine.nonsingular_iff']
  constructor
  · simpa [WeierstrassCurve.Affine.equation_iff, E] using h
  · right
    simpa [E] using mul_ne_zero (by decide : (2 : F) ≠ 0) hy

def T : E.Point := Point.some (valid 3 615668188 (by decide) (by decide))
def G : E.Point := Point.some (valid 1106623295 606392145 (by decide) (by decide))

def twicePow (a : E.Point) : ℕ → E.Point
  | 0 => a
  | k+1 => let b := twicePow a k; b+b

theorem twicePow_eq (a : E.Point) (k : ℕ) : twicePow a k = (2^k : ℕ) • a := by
  induction k with
  | zero => simp [twicePow]
  | succ k ih => simp [twicePow, ih, pow_succ, Nat.mul_comm, mul_nsmul, two_nsmul, nsmul_add]

private def finite : E.Point → Bool
  | .zero => false
  | .some _ => true

private theorem kernel_killed : (1024 : Nat) • G = 0 := by
  change (2^10 : Nat) • G = 0
  rw [← twicePow_eq]
  have h : finite (twicePow G 10) = false := by native_decide
  cases he : twicePow G 10 with
  | zero => rfl
  | some _ => simp [he,finite] at h

private theorem survives (a : E.Point) (h : finite (twicePow a 10) = true) :
    (1024 : Nat) • a ≠ 0 := by
  rw [show (1024 : Nat) = 2^10 by decide, ← twicePow_eq]
  intro he
  rw [he] at h
  exact Bool.noConfusion h

private theorem coset_survives : (1024 : Nat) • T ≠ 0 :=
  survives T (by native_decide)

theorem coset_finite (i : Nat) : T + i • G ≠ 0 := by
  simpa using (separated coset_survives kernel_killed i 0).1

theorem shift_finite (k : Fin 10) : (2^(k:Nat) : Nat) • G ≠ 0 := by
  have allStages : ∀ j : Fin 10, finite (twicePow G j.val) = true := by native_decide
  have h := allStages k
  rw [← twicePow_eq]
  intro he
  rw [he] at h
  exact Bool.noConfusion h

theorem fixture_chord {x y u v : F} (hp : E.Nonsingular x y) (hq : E.Nonsingular u v)
    (i j : Nat) (p : Point.some hp = T + i • G) (q : Point.some hq = j • G) :
    u-x ≠ 0 := by
  obtain ⟨a,b⟩ := separated coset_survives kernel_killed i j
  have distinct := distinct_x hp hq (by rwa [p,q]) (by rwa [p,q])
  exact sub_ne_zero.mpr distinct.symm

#print axioms fixture_chord
end M31CosetChords
