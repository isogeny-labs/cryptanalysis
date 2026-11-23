import SignedSquare

namespace M31SignedSquare

theorem iterate_range (x : Int) (lo : -p ≤ x) (hi : x < p) (n : Nat) :
    -p ≤ fold^[n] x ∧ fold^[n] x < p := by
  induction n with
  | zero => exact ⟨lo, hi⟩
  | succ n ih =>
    rw [Function.iterate_succ_apply']
    exact fold_range _ ih.1 ih.2.le

private theorem positive_chain (x : Int) (n : Nat) :
    fold^[n] x ≡ x^(2^n) [ZMOD p] := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [Function.iterate_succ_apply', pow_succ 2 n, pow_mul]
    exact (fold_equiv _).trans (ih.pow 2)

theorem terminal_root_exact (x : Int) (lo : 0 ≤ x) (hi : x < p) :
    canonical (fold^[29] x) = x^(2^29) % p := by
  obtain ⟨a,b⟩ := iterate_range x (by unfold p; omega) hi 29
  rw [canonical_eq _ a b]
  exact positive_chain x 29

end M31SignedSquare
