import Mathlib.Tactic
import Std.Tactic.BVDecide

namespace M31XorCompress

-- A word is a sequence of bits. Its address is the XOR of one seven-bit
-- mask for each set bit, hence a binary linear function of the word.
def Word : Nat → Type
  | 0 => Unit
  | n+1 => Bool × Word n

def Masks : Nat → Type
  | 0 => Unit
  | n+1 => BitVec 7 × Masks n

def address : (n : Nat) → Masks n → Word n → BitVec 7
  | 0, _, _ => 0
  | n+1, m, x => (address n m.2 x.2) ^^^ (if x.1 then m.1 else 0)

private theorem cross_bound (a b : Nat) (h : a+b = 17) : a*b ≤ 72 := by
  have bound : a ≤ 17 := by omega
  interval_cases a <;> simp_all <;> omega

private theorem xor_collision (a b m : BitVec 7) (h : a = b ^^^ m) :
    a ^^^ b = m := by bv_decide

theorem separates (n : Nat) (keys : Fin 17 → Word n) :
    ∃ masks : Masks n, ∀ i j, address n masks (keys i) = address n masks (keys j) →
      keys i = keys j := by
  classical
  induction n with
  | zero => exact ⟨(), fun _ _ _ => @Subsingleton.elim Unit _ _ _⟩
  | succ n ih =>
    obtain ⟨m,hm⟩ := ih (fun i => (keys i).2)
    let h := fun i => address n m (keys i).2
    let lo := Finset.univ.filter (fun i => (keys i).1 = false)
    let hi := Finset.univ \ lo
    let bad := (lo ×ˢ hi).image (fun ij => h ij.1 ^^^ h ij.2)
    have partition : lo.card + hi.card = 17 := by
      have := Finset.card_sdiff_add_card_eq_card (show lo ⊆ Finset.univ from Finset.subset_univ _)
      simpa [hi, Nat.add_comm] using this
    have small : bad.card ≤ 72 := by
      exact Finset.card_image_le.trans ((Finset.card_product lo hi) ▸ cross_bound _ _ partition)
    let equiv : Fin 128 ≃ BitVec 7 := ⟨fun i => (⟨i⟩ : BitVec 7), fun b => b.toFin, fun _ => rfl, fun _ => rfl⟩
    let : Fintype (BitVec 7) := Fintype.ofEquiv _ equiv
    have missing : ∃ mask : BitVec 7, mask ∉ bad := by
      by_contra! all
      have eq : bad = Finset.univ := Finset.eq_univ_of_forall all
      rw [eq] at small
      have card := Fintype.card_congr equiv
      simp only [Finset.card_univ] at small
      simp only [Fintype.card_fin] at card
      omega
    obtain ⟨mask,free⟩ := missing
    have apart (i j : Fin 17) (a : (keys i).1 = false) (b : (keys j).1 = true) :
        h i ≠ h j ^^^ mask := by
      intro eq
      apply free
      apply Finset.mem_image.mpr
      refine ⟨(i,j), Finset.mem_product.mpr ⟨?_,?_⟩, xor_collision _ _ _ eq⟩
      · simp [lo,a]
      · simp [hi,lo,b]
    refine ⟨(mask,m), fun i j eq => ?_⟩
    change h i ^^^ (if (keys i).1 then mask else 0) =
      h j ^^^ (if (keys j).1 then mask else 0) at eq
    have bits : (keys i).1 = (keys j).1 := by
      cases a : (keys i).1 <;> cases b : (keys j).1
      · rfl
      · exact False.elim (apart i j a b (by simpa [a,b] using eq))
      · exact False.elim (apart j i b a (by simpa [a,b] using eq.symm))
      · rfl
    apply Prod.ext bits
    apply hm i j
    rw [bits] at eq
    change h i = h j
    exact (show ∀ x y z : BitVec 7, x ^^^ z = y ^^^ z → x = y by
      intro x y z heq
      bv_decide) _ _ _ eq
end M31XorCompress
