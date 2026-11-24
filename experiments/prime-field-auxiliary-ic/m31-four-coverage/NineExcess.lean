import Mathlib.Tactic
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

end M31NineExcess
