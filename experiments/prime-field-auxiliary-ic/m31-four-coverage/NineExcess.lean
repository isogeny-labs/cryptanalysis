import Mathlib.Tactic
import Mathlib.Data.List.GetD
import Std.Tactic.BVDecide

namespace M31NineExcess

-- A nonzero parity check on seven bits splits the 128 syndromes in half.
-- If w of the 17 keys have odd parity, exactly w*(17-w) unordered pairs
-- cross the split. The nine extra differences contribute the excess over 64.
theorem excess_weight (w e : Nat) (hw : w ≤ 17)
    (counts : w*(17-w) = 64+e) : e = 2 ∨ e = 6 ∨ e = 8 := by
  interval_cases w <;> simp_all <;> omega

private def equiv (n : Nat) : Fin (2^n) ≃ BitVec n :=
  ⟨fun i => ⟨i⟩, fun b => b.toFin, fun _ => rfl, fun _ => rfl⟩
local instance (n : Nat) : Fintype (BitVec n) := Fintype.ofEquiv _ (equiv n)

def weight (x : BitVec 9) := ((List.range 9).filter (fun i => x.getLsbD i)).length
def good (x : BitVec 9) : Prop := weight x = 2 ∨ weight x = 6 ∨ weight x = 8
instance (x : BitVec 9) : Decidable (good x) := inferInstanceAs (Decidable (_ ∨ _ ∨ _))

private def allowed := Finset.univ.filter (fun x : BitVec 9 => x = 0 ∨ good x)
private def four : Finset (BitVec 9) := {3,12,48,192}

private theorem rest_size : (allowed \ four).card = 126 := by decide +kernel
private theorem incompatible : ∀ a ∈ four, ∀ b ∈ four,
    a = b ∨ ¬ good (a ^^^ b) := by decide +kernel

private theorem xor_zero (a b : BitVec 7) (h : a ^^^ b = 0) : a = b := by bv_decide

theorem impossible (f : BitVec 7 → BitVec 9)
    (linear : ∀ x y, f (x ^^^ y) = f x ^^^ f y)
    (weights : ∀ x, x ≠ 0 → good (f x)) : False := by
  classical
  have eqzero : f 0 = 0 := by simpa using linear 0 0
  have nonzero (x) (hx : x ≠ 0) : f x ≠ 0 := by
    intro zero
    have h := weights x hx
    rw [zero] at h
    exact (by decide : ¬ good 0) h
  have inj : Function.Injective f := by
    intro a b eq
    by_contra ne
    have nz : a ^^^ b ≠ 0 := by intro bad; exact ne (xor_zero a b bad)
    exact nonzero _ nz (by simp [linear,eq])
  let image := Finset.univ.image f
  have total : image.card = 128 := by
    rw [show image = Finset.univ.image f from rfl,Finset.card_image_of_injective _ inj,
      Finset.card_univ, ← Fintype.card_congr (equiv 7), Fintype.card_fin]
    decide
  have sub : image ⊆ allowed := by
    intro x hx
    obtain ⟨a,_,rfl⟩ := Finset.mem_image.mp hx
    by_cases z : a = 0
    · exact Finset.mem_filter.mpr ⟨Finset.mem_univ _, Or.inl (z ▸ eqzero)⟩
    · exact Finset.mem_filter.mpr ⟨Finset.mem_univ _,Or.inr (weights a z)⟩
  have sparse : (image ∩ four).card ≤ 1 := by
    apply Finset.card_le_one.mpr
    intro x hx y hy
    obtain ⟨ix,fx⟩ := Finset.mem_inter.mp hx
    obtain ⟨iy,fy⟩ := Finset.mem_inter.mp hy
    obtain ⟨a,_,rfl⟩ := Finset.mem_image.mp ix
    obtain ⟨b,_,rfl⟩ := Finset.mem_image.mp iy
    rcases incompatible _ fx _ fy with eq | bad
    · exact eq
    · by_contra ne
      have nz : a ^^^ b ≠ 0 := by
        intro z
        have ab : a = b := xor_zero a b z
        exact ne (congrArg f ab)
      exact bad (linear a b ▸ weights _ nz)
  have rest : (image \ four).card ≤ (allowed \ four).card := Finset.card_le_card (by
    intro x hx
    exact Finset.mem_sdiff.mpr ⟨sub (Finset.mem_sdiff.mp hx).1,(Finset.mem_sdiff.mp hx).2⟩)
  have split := Finset.card_sdiff_add_card_inter image four
  rw [rest_size] at rest
  omega

-- Keep multiplicities and enumerate each unordered pair by its position.
def diffs : List (BitVec 7) → List (BitVec 7)
  | [] => []
  | x::xs => xs.map (fun y => x ^^^ y) ++ diffs xs

theorem twice_pairs (xs : List (BitVec 7)) :
    2*(diffs xs).length + xs.length = xs.length^2 := by
  induction xs with
  | nil => decide
  | cons x xs ih => simp [diffs]; nlinarith

theorem cross_count (p : BitVec 7 → Bool)
    (lin : ∀ x y, p (x ^^^ y) = (p x ^^ p y)) (xs : List (BitVec 7)) :
    (diffs xs).countP p = xs.countP p * xs.countP (fun x => !(p x)) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    simp only [diffs, List.countP_append, List.countP_map, Function.comp_def,
      List.countP_cons,lin,ih]
    cases p x <;> simp [Nat.add_mul, Nat.mul_add] <;> ac_rfl

def syndromes : List (BitVec 7) := (List.range 127).map (fun n => BitVec.ofNat 7 (n+1))

theorem nine_extra (keys : List (BitVec 7)) (size : keys.length = 17)
    (cover : ∀ d : BitVec 7, d ≠ 0 → d ∈ diffs keys) :
    ∃ extra : List (BitVec 7), extra.length = 9 ∧ (diffs keys).Perm (extra ++ syndromes) := by
  classical
  have le : (syndromes : Multiset (BitVec 7)) ≤ (diffs keys : Multiset (BitVec 7)) := by
    apply (Multiset.le_iff_subset (by decide +kernel : (syndromes : Multiset (BitVec 7)).Nodup)).2
    intro d hd
    apply cover
    intro z
    subst d
    exact (by decide +kernel : (0 : BitVec 7) ∉ syndromes) hd
  let m := (diffs keys : Multiset (BitVec 7)) - (syndromes : Multiset (BitVec 7))
  have perm : (diffs keys).Perm (m.toList ++ syndromes) := by
    apply Multiset.coe_eq_coe.mp
    rw [← Multiset.coe_add,Multiset.coe_toList]
    exact (Multiset.sub_add_cancel le).symm
  refine ⟨m.toList,?_,perm⟩
  have h := twice_pairs keys
  rw [size] at h
  have eq := perm.length_eq
  rw [List.length_append,show syndromes.length = 127 by decide +kernel] at eq
  omega

def dot (u x : BitVec 7) : Bool :=
  let z := u &&& x
  (z ^^^ (z >>> 1) ^^^ (z >>> 2) ^^^ (z >>> 3) ^^^
    (z >>> 4) ^^^ (z >>> 5) ^^^ (z >>> 6)).getLsbD 0

private theorem dot_right (u a b : BitVec 7) : dot u (a ^^^ b) = (dot u a ^^ dot u b) := by
  unfold dot
  bv_decide
private theorem dot_left (u v x : BitVec 7) : dot (u ^^^ v) x = (dot u x ^^ dot v x) := by
  unfold dot
  bv_decide

set_option maxRecDepth 8192 in
set_option maxHeartbeats 8000000 in
private theorem balanced : ∀ u : BitVec 7, u ≠ 0 → syndromes.countP (dot u) = 64 := by
  decide +kernel

def signature (extra : List (BitVec 7)) (u : BitVec 7) : BitVec 9 :=
  (BitVec.ofBoolListLE (extra.map (dot u))).setWidth 9

private theorem bit_signature (extra : List (BitVec 7)) (u : BitVec 7) (i : Nat) (hi : i < 9) :
    (signature extra u).getLsbD i = dot u (extra.getD i 0) := by
  have zero : dot u 0 = false := by simp [dot]
  simp only [signature, BitVec.getLsbD_setWidth, decide_eq_true hi, Bool.true_and,
    BitVec.getLsbD_ofBoolListLE]
  simpa only [zero] using List.getD_map (l := extra) (n := i) (d := 0) (dot u)

private theorem signature_linear (extra : List (BitVec 7)) (a b : BitVec 7) :
    signature extra (a ^^^ b) = signature extra a ^^^ signature extra b := by
  apply BitVec.eq_of_getLsbD_eq
  intro i hi
  simp only [BitVec.getLsbD_xor,bit_signature _ _ _ hi,dot_left]

private theorem signature_weight (extra : List (BitVec 7)) (len : extra.length = 9) (u : BitVec 7) :
    weight (signature extra u) = extra.countP (dot u) := by
  have reconstruct : (List.range 9).map (fun i => extra.getD i 0) = extra := by
    apply List.ext_getElem
    · simp [len]
    · intro i h k
      simp [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem k]
  unfold weight
  rw [← List.countP_eq_length_filter]
  calc
    _ = (List.range 9).countP (fun i => dot u (extra.getD i 0)) :=
      List.countP_congr (fun i hi => by rw [bit_signature _ _ _ (List.mem_range.mp hi)])
    _ = _ := by
      have h := List.countP_map (p := dot u) (f := fun i => extra.getD i 0) (l := List.range 9)
      rw [reconstruct] at h
      exact h.symm

theorem missing_direction (keys : List (BitVec 7)) (size : keys.length = 17) :
    ∃ d : BitVec 7, d ≠ 0 ∧ d ∉ diffs keys := by
  by_contra! cover
  obtain ⟨extra,len,perm⟩ := nine_extra keys size cover
  apply impossible (signature extra) (signature_linear extra)
  intro u nz
  unfold good
  rw [signature_weight extra len]
  have count := perm.countP_eq (dot u)
  rw [List.countP_append, balanced u nz, cross_count _ (dot_right u)] at count
  have total := List.length_eq_countP_add_countP (dot u) (l := keys)
  simp only [Bool.not_eq_true, Bool.decide_eq_false] at total
  rw [size] at total
  apply excess_weight (keys.countP (dot u)) _ (by omega)
  have neg : keys.countP (fun x => !(dot u x)) = 17 - keys.countP (dot u) := by omega
  rw [← neg]
  omega

end M31NineExcess
