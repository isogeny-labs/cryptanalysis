import Mathlib.Tactic
import Std.Tactic.BVDecide
import XorLookup

namespace M31XorCompress

-- A word is a sequence of bits. Its address is the XOR of one seven-bit
-- mask for each set bit, hence a binary linear function of the word.
def WordOver (α : Type) : Nat → Type
  | 0 => α
  | n+1 => Bool × WordOver α n

abbrev Word := WordOver Unit

def Masks : Nat → Type
  | 0 => Unit
  | n+1 => BitVec 7 × Masks n

def addressFrom {α : Type} (base : α → BitVec 7) : (n : Nat) → Masks n → WordOver α n → BitVec 7
  | 0, _, x => base x
  | n+1, m, x => (addressFrom base n m.2 x.2) ^^^ (if x.1 then m.1 else 0)

abbrev address := addressFrom (fun _ : Unit => 0)

private theorem cross_bound (a b : Nat) (h : a+b = 17) : a*b ≤ 72 := by
  have bound : a ≤ 17 := by omega
  interval_cases a <;> simp_all <;> omega

private theorem xor_collision (a b m : BitVec 7) (h : a = b ^^^ m) :
    a ^^^ b = m := by bv_decide

private theorem extends_base {α : Type} (base : α → BitVec 7) (inj : Function.Injective base)
    (n : Nat) (keys : Fin 17 → WordOver α n) :
    ∃ masks : Masks n, ∀ i j, addressFrom base n masks (keys i) = addressFrom base n masks (keys j) →
      keys i = keys j := by
  classical
  induction n with
  | zero => exact ⟨(), fun _ _ eq => inj eq⟩
  | succ n ih =>
    obtain ⟨m,hm⟩ := ih (fun i => (keys i).2)
    let h := fun i => addressFrom base n m (keys i).2
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

theorem separates (n : Nat) (keys : Fin 17 → Word n) :
    ∃ masks : Masks n, ∀ i j, address n masks (keys i) = address n masks (keys j) →
      keys i = keys j :=
  extends_base _ (fun _ _ _ => Subsingleton.elim _ _) n keys

-- The base case takes the low seven bits verbatim. Each further stage
-- can only add the mask associated with its new high bit.
def splitWord : (n : Nat) → BitVec (7+n) → WordOver (BitVec 7) n
  | 0, x => x
  | n+1, x => (x.msb, splitWord n (x.setWidth (7+n)))

private theorem split_injective (n : Nat) : Function.Injective (splitWord n) := by
  induction n with
  | zero => exact fun _ _ eq => eq
  | succ n ih =>
    intro x y eq
    have halves := Prod.mk.inj eq
    have low := ih halves.2
    exact (BitVec.cons_msb_setWidth x).symm.trans
      ((congrArg₂ BitVec.cons halves.1 low).trans (BitVec.cons_msb_setWidth y))

def hash (n : Nat) (m : Masks n) (x : BitVec (7+n)) : BitVec 7 :=
  addressFrom id n m (splitWord n x)

theorem hash_linear (n : Nat) (m : Masks n) (x y : BitVec (7+n)) :
    hash n m (x ^^^ y) = hash n m x ^^^ hash n m y := by
  induction n with
  | zero => rfl
  | succ n ih =>
    change hash n m.2 ((x ^^^ y).setWidth (7+n)) ^^^ (if (x ^^^ y).msb then m.1 else 0) =
      (hash n m.2 (x.setWidth (7+n)) ^^^ (if x.msb then m.1 else 0)) ^^^
      (hash n m.2 (y.setWidth (7+n)) ^^^ (if y.msb then m.1 else 0))
    rw [BitVec.setWidth_xor, ih, BitVec.msb_xor]
    exact (show ∀ (a b z : BitVec 7) (i j : Bool),
        (a ^^^ b) ^^^ (if i ^^ j then z else 0) =
        (a ^^^ (if i then z else 0)) ^^^ (b ^^^ (if j then z else 0)) by
      intro a b z i j
      bv_decide) _ _ _ _ _

theorem hash_low (n : Nat) (m : Masks n) (x : BitVec 7) :
    hash n m (x.setWidth (7+n)) = x := by
  induction n with
  | zero => simp [hash, addressFrom, splitWord]
  | succ n ih =>
    change hash n m.2 ((x.setWidth (7+n+1)).setWidth (7+n)) ^^^
      (if (x.setWidth (7+n+1)).msb then m.1 else 0) = x
    simp [BitVec.msb_setWidth, BitVec.getLsbD_of_ge, ih]

theorem fixed_low_separates (keys : Fin 17 → BitVec 31) :
    ∃ masks : Masks 24, ∀ i j, hash 24 masks (keys i) = hash 24 masks (keys j) →
      keys i = keys j := by
  obtain ⟨m,hm⟩ := extends_base id Function.injective_id 24 (fun i => splitWord 24 (keys i))
  exact ⟨m, fun i j eq => split_injective 24 (hm i j eq)⟩

-- The four-table implementation can use the very same separating masks.
-- Its zero and singleton seed entries must represent those masks.
theorem separating_lookup (keys : Fin 17 → BitVec 31) :
    ∃ m : Masks 24,
      (∀ i j, hash 24 m (keys i) = hash 24 m (keys j) → keys i = keys j) ∧
      ∀ (tables : Nat → M31XorLookup.Chunk → BitVec 7),
        (∀ s i, M31XorLookup.clear i = 0 → tables s i = hash 24 m (M31XorLookup.embed i s)) →
        ∀ x : BitVec 31, x.setWidth 7 ^^^
          M31XorLookup.build (tables 7) 63 (M31XorLookup.chunk x 7) ^^^
          M31XorLookup.build (tables 13) 63 (M31XorLookup.chunk x 13) ^^^
          M31XorLookup.build (tables 19) 63 (M31XorLookup.chunk x 19) ^^^
          M31XorLookup.build (tables 25) 63 (M31XorLookup.chunk x 25) = hash 24 m x := by
  obtain ⟨m,sep⟩ := fixed_low_separates keys
  refine ⟨m,sep, M31XorLookup.lookup _ (hash_linear 24 m) ?_⟩
  intro x
  have eq : x &&& 127 = (x.setWidth 7).setWidth 31 := by bv_decide
  rw [eq]
  exact hash_low 24 m (x.setWidth 7)

end M31XorCompress
