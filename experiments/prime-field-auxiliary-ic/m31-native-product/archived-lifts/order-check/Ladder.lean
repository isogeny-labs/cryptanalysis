import Mathlib.GroupTheory.OrderOfElement

namespace SharedDoubling
variable {G : Type*} [AddCommGroup G]

def doubles : ℕ → G → G
  | 0, x => x
  | n+1, x => let y := doubles n x; y+y

theorem scalar (n : ℕ) (x : G) : doubles n x = (2^n : ℕ) • x := by
  induction n with
  | zero => simp [doubles]
  | succ n ih => simp [doubles, ih, pow_succ, Nat.mul_two, add_nsmul]

private theorem exact_order (n : ℕ) (x : G) (hn : doubles n x ≠ 0)
    (hz : doubles n x + doubles n x = 0) : addOrderOf x = 2^(n+1) := by
  let : Fact (Nat.Prime 2) := ⟨Nat.prime_two⟩
  apply addOrderOf_eq_prime_pow
  · simpa only [scalar] using hn
  · rw [← scalar]
    exact hz

/-- Split the ladder after a doublings. The final nonzero point doubling
to zero certifies both the original order and the intermediate order. -/
theorem shared_orders (a b : ℕ) (x : G)
    (hn : doubles b (doubles a x) ≠ 0)
    (hz : doubles b (doubles a x) + doubles b (doubles a x) = 0) :
    addOrderOf x = 2^(a+b+1) ∧ addOrderOf (doubles a x) = 2^(b+1) := by
  have split : doubles (a+b) x = doubles b (doubles a x) := by
    simp only [scalar, pow_add, smul_smul]
    rw [Nat.mul_comm (2^a) (2^b)]
  exact ⟨exact_order _ _ (split ▸ hn) (split ▸ hz), exact_order _ _ hn hz⟩

end SharedDoubling
#print axioms SharedDoubling.shared_orders
