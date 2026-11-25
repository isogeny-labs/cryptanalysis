import Mathlib.Tactic

namespace M31FiveBitObstruction

def points : List (Nat × Nat) := [
  (158976,1889078106),(158977,1327219193),(158978,438396208),(158979,650354541),
  (158980,1384328545),(158981,109981729),(158982,1822427524),(158983,48424842),
  (158984,1369741527),(158992,1622955342),(159000,195349168),(159008,1230364892),
  (159016,471148008),(159024,371732470),(159032,1632675978),(11,1885598388),(12,612243971)]

def keys := points.map (fun q => BitVec.ofNat 31 q.1)

theorem valid : keys.eraseDups.length = 17 ∧ ∀ q ∈ points,
    q.1 < 2147483647 ∧ q.2 < 2147483647 ∧
    q.2^2 % 2147483647 = (q.1^3 + 2*q.1 + 14) % 2147483647 := by decide +kernel

private def u (d : BitVec 6) : BitVec 31 := 158976 ^^^ (d &&& 7).setWidth 31
private def v (d : BitVec 6) : BitVec 31 := 158976 ^^^ (d &&& 56).setWidth 31

private theorem members : ∀ d : BitVec 6, u d ∈ keys ∧ v d ∈ keys := by decide +kernel

private theorem diff : ∀ a b : BitVec 6,
    u (a ^^^ b) ^^^ v (a ^^^ b) = a.setWidth 31 ^^^ b.setWidth 31 := by decide +kernel

private theorem apart : ∀ a b : BitVec 6, a ≠ b →
    u (a ^^^ b) ≠ v (a ^^^ b) := by decide +kernel

-- Restrict the hash to the low six-dimensional subspace. Its 64 elements
-- cannot have distinct five-bit images. Every difference from that subspace
-- occurs between stored keys because both complementary three-bit groups occur.
theorem collision (h : BitVec 31 → BitVec 5)
    (linear : ∀ a b, h (a ^^^ b) = h a ^^^ h b) :
    ∃ x ∈ keys, ∃ y ∈ keys, x ≠ y ∧ h x = h y := by
  let f : Fin 64 → Fin 32 := fun a => (h ((⟨a⟩ : BitVec 6).setWidth 31)).toFin
  have pair : ∃ a b, a ≠ b ∧ f a = f b := by
    by_contra! none
    have inj : Function.Injective f := by
      intro a b eq
      by_contra ne
      exact none a b ne eq
    have := Fintype.card_le_of_injective f inj
    simp at this
  obtain ⟨i,j,ne,eq⟩ := pair
  let a : BitVec 6 := ⟨i⟩
  let b : BitVec 6 := ⟨j⟩
  have hne : a ≠ b := fun e => ne (congrArg BitVec.toFin e)
  have same : h (a.setWidth 31) = h (b.setWidth 31) := by
    exact congrArg (fun z : Fin 32 => (⟨z⟩ : BitVec 5)) eq
  obtain ⟨hu,hv⟩ := members (a ^^^ b)
  refine ⟨_,hu,_,hv,apart a b hne,?_⟩
  have he := congrArg h (diff a b)
  rw [linear,linear,same] at he
  rw [BitVec.xor_self] at he
  exact BitVec.xor_eq_zero_iff.mp he

theorem six_suffices : ∀ x ∈ keys, ∀ y ∈ keys,
    x.setWidth 6 = y.setWidth 6 → x = y := by
  have pairs : keys.all (fun x => keys.all (fun y => decide (x.setWidth 6 ≠ y.setWidth 6 ∨ x = y))) := by
    decide +kernel
  intro x hx y hy eq
  exact (of_decide_eq_true (List.all_eq_true.mp (List.all_eq_true.mp pairs x hx) y hy)).resolve_left
    (fun ne => ne eq)

end M31FiveBitObstruction
