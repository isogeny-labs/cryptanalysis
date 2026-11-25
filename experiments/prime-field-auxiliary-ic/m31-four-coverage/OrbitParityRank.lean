import FiberLift
import OrbitNorm
import Mathlib.Tactic.Eval
import Mathlib.LinearAlgebra.Matrix.Rank

namespace M31OrbitParityRank
open Matrix
open scoped BigOperators
abbrev I := Fin 31
abbrev J := Fin 32
abbrev G := Fin 4
abbrev B := ZMod 2
abbrev F := ZMod 2147483647

def data : Array (Array Nat) :=
  (((include_str "orbit-parity-rank.csv").splitOn "\n").tail.filterMap
    (fun line => ((line.splitOn ",").mapM String.toNat?).map List.toArray)).toArray

def atCol (g : G) (r : J) (k : Nat) := (data[32*g.val+r.val]!)[k]!
def bit (g : G) (r j : J) : B := (((atCol g r 3).testBit j.val).toNat : Nat)
def x (g : G) (r j : J) : F := atCol g r (5+j.val)
def y (g : G) (r j : J) : F := atCol g r (37+j.val)
def rhs (g : G) (r j : J) := (x g r j)^3+2*x g r j+14

/-- Chord equations for adding the fixed auxiliary point, including the wraparound. -/
def chord (g : G) (r j : J) : Prop :=
  let u := x g r j
  let v := y g r j
  let u' := x g r (j+1)
  let v' := y g r (j+1)
  let dx := u-1965083199
  let dy := v-1854403464
  v^2=u^3+u ∧ dx≠0 ∧ dy^2=(u'+u+1965083199)*dx^2 ∧
    (v'+v)*dx=dy*(u-u')

instance (g : G) (r j : J) : Decidable (chord g r j) := by unfold chord; infer_instance

theorem witnesses : ∀ (g : G) (r j : J), chord g r j ∧ rhs g r j ≠ 0 ∧
    bit g r j = (decide ((M31FiberLift.squares (fun _ : Unit => rhs g r j) 29 ())^2 =
      rhs g r j)).toNat := by native_decide

theorem lift (g : G) (r j : J) : bit g r j = 1 ↔ ∃ z : F, z^2=rhs g r j := by
  rw [(witnesses g r j).2.2]
  have h := M31FiberLift.lift_exact (fun _ : Unit => rhs g r j) ()
  by_cases eq : (M31FiberLift.squares (fun _ : Unit => rhs g r j) 29 ())^2 = rhs g r j <;>
    simp [eq, ← h]

theorem parity_classes : ∀ (g : G) (r : J), ∑ j, bit g r j = (g.val%2 : Nat) := by
  native_decide

def diffs (g : G) : Matrix I J B := fun i j => bit g i.succ j - bit g 0 j
def inv (g : G) : Matrix I I B := fun i j => (((atCol g i.succ 4).testBit j.val).toNat : Nat)
def pairs : Matrix I J B := fun i j =>
  (if j=i.castSucc then 1 else 0) + (if j=31 then 1 else 0)

theorem certificate (g : G) : inv g * diffs g = pairs := by
  have all : ∀ (k : G) (i : I) (j : J), (inv k * diffs k) i j = pairs i j := by
    have verified : (List.finRange 4).all (fun k => (List.finRange 31).all
        (fun i => (List.finRange 32).all (fun j => decide ((inv k * diffs k) i j = pairs i j)))) := by
      native_decide
    intro k i j
    exact of_decide_eq_true (List.all_eq_true.mp
      (List.all_eq_true.mp (List.all_eq_true.mp verified k (by simp)) i (by simp)) j (by simp))
  exact Matrix.ext (all g)

private def differences (values : J → J → B) : Matrix I J B :=
  fun i j => values i.succ j - values 0 j

/-- Any linear statistic that is constant on one class has uniform coefficients. -/
private theorem uniform (values : J → J → B) (a : Matrix I I B)
    (cert : a * differences values = pairs)
    (w : J → B) (c : B) (constant : ∀ r : J, ∑ j, values r j * w j = c) : ∀ j, w j = w 31 := by
  have zero : (differences values).mulVec w = 0 := by
    funext i
    simp [Matrix.mulVec, dotProduct, differences, sub_mul, Finset.sum_sub_distrib, constant]
  have h := congrArg (fun v => a.mulVec v) zero
  simp only [mulVec_mulVec, cert, mulVec_zero] at h
  intro j
  refine Fin.lastCases ?_ (fun i => ?_) j
  · rfl
  · have hi := congrFun h i
    simp [Matrix.mulVec, dotProduct, pairs, add_mul, Finset.sum_add_distrib,
      ite_mul] at hi
    have neg : -w 31 = w 31 := (show ∀ b : B, -b = b by decide) _
    exact (eq_neg_of_add_eq_zero_left hi).trans neg

theorem only_parity (g : G) (w : J → B) (c : B)
    (constant : ∀ r : J, ∑ j, bit g r j * w j = c) : ∀ j, w j = w 31 :=
  uniform (bit g) (inv g) (certificate g) w c constant

def rotateLabels (r j : J) := bit 1 0 (j+r)
def rotateInv : Matrix I I B := fun i j => (((atCol 1 i.succ 69).testBit j.val).toNat : Nat)
def rotateDiff : Matrix I J B := fun i j => rotateLabels i.succ j - rotateLabels 0 j

theorem rotation_certificate : rotateInv * rotateDiff = pairs := by
  have all : (List.finRange 31).all (fun i => (List.finRange 32).all
      (fun j => decide ((rotateInv * rotateDiff) i j = pairs i j))) := by native_decide
  exact Matrix.ext fun i j => of_decide_eq_true (List.all_eq_true.mp
    (List.all_eq_true.mp all i (by simp)) j (by simp))

/-- None propagates a kernel pole; each successful step uses the published quotient map. -/
def terminal (u : F) : Option F := M31OrbitNorm.steps.foldlM (fun x s =>
  if x=s.t then none else some (x-s.t+s.A+s.B/(x-s.t))) u

theorem common_terminal : ∀ r : J, terminal (x 1 0 r) = some 687814895 := by native_decide

/-- A quotient-only decoder for any fixed linear label statistic must use uniform weights,
already on all cyclic starts of this single public orbit. -/
theorem quotient_only (decoder : F → B) (w : J → B)
    (correct : ∀ r : J, ∑ j, rotateLabels r j * w j =
      decoder ((terminal (x 1 0 r)).getD 0)) : ∀ j, w j = w 31 := by
  apply uniform rotateLabels rotateInv rotation_certificate w (decoder 687814895)
  intro r
  simpa [common_terminal] using correct r

theorem rotation_distinct : Function.Injective rotateLabels := by
  have sep : ∀ a b : J, a ≠ b → ∃ j : J, rotateLabels a j ≠ rotateLabels b j := by
    native_decide
  intro a b eq
  by_contra h
  obtain ⟨j,ne⟩ := sep a b h
  exact ne (congrFun eq j)

/-- Even an arbitrary nonlinear decoder needs 32 distinguishable side states to
recover the whole ordered label word from this common quotient coordinate. -/
theorem side_states {S : Type*} [Fintype S] (state : J → S)
    (decode : F → S → J → B)
    (correct : ∀ r, decode ((terminal (x 1 0 r)).getD 0) (state r) = rotateLabels r) :
    32 ≤ Fintype.card S := by
  have inject : Function.Injective state := by
    intro a b same
    apply rotation_distinct
    rw [← correct a, ← correct b, common_terminal, common_terminal, same]
  simpa using Fintype.card_le_of_injective state inject

end M31OrbitParityRank
