import Mathlib.NumberTheory.LucasLehmer
import Mathlib.RingTheory.RootsOfUnity.PrimitiveRoots

namespace M31CosetInverse
abbrev F := ZMod 2147483647
local instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩
abbrev gen : F := 1448159583

/-- For i = 0,...,32 choose y = gen^i and store (y * reverse(y))⁻¹ at
the slot computed below. The remaining slots contain zero. The native C++
representation uses one 32-bit word per slot. -/
def table : Array Nat := #[
  0, 365509334, 1312777282, 0, 0, 0, 1873629346, 0,
  983828630, 0, 785363387, 1282665135, 1106308876, 1918578825, 1028857939, 0,
  1933321282, 593018460, 0, 0, 0, 0, 972790648, 924222493,
  0, 1274273817, 0, 0, 0, 1, 0, 0,
  1205713946, 1587327902, 1699724, 486785834, 1562616383, 0, 0, 0,
  1186767135, 0, 0, 0, 1744189987, 0, 0, 325103453,
  0, 1429248167, 0, 940541589, 0, 1282838597, 1629983734, 191921757,
  419445506, 0, 1590094663, 0, 1581736606, 1177716559, 0, 1466920800]

/-- Half the Hamming distance from a cyclic shift of a 31-bit field word. -/
def distance (v k : Nat) : Nat :=
  let rotated := ((v <<< k) &&& 2147483647) ||| (v >>> (31-k))
  ((List.range 31).countP (fun i => (v ^^^ rotated).testBit i)) / 2

def corrected (y : F) : F :=
  let v := y.val
  let slot := (distance v 1 + 23 * distance v 9 + 5 * distance v 13) % 64
  let r := (BitVec.ofNat 32 v).reverse
  let rev := ((r &&& 2147483647) ||| (r >>> 31)).toNat
  ((rev * table[slot]! : Nat) : F)

theorem generator_order : IsPrimitiveRoot gen 2046 := by
  apply IsPrimitiveRoot.iff_orderOf.mpr
  apply orderOf_eq_of_pow_and_pow_div_prime (by decide)
  · native_decide
  intro q prime dvd
  change q ∣ 2 * 3 * 11 * 31 at dvd
  rw [prime.dvd_mul, prime.dvd_mul, prime.dvd_mul] at dvd
  rcases dvd with ((h | h) | h) | h <;>
    (obtain rfl := (Nat.prime_dvd_prime_iff_eq prime (by decide)).mp h; native_decide)

/-- The finite certificate checks every projected key, including the correction
selected by the three rotation distances. -/
theorem inverse_correct (x : F) (hx : x ≠ 0) :
    x^1049600 * corrected (x^1049601) = x⁻¹ := by
  have hpow : (x^1049601)^2046 = 1 := by
    rw [← pow_mul]
    simpa only [ZMod.card] using FiniteField.pow_card_sub_one_eq_one x hx
  obtain ⟨i,hi,e⟩ := generator_order.eq_pow_of_pow_eq_one hpow
  have cert : ∀ j : Fin 2046, corrected (gen^j.val) * (gen^j.val) = 1 := by native_decide
  have hk := cert ⟨i,hi⟩
  change corrected (gen^i) * gen^i = 1 at hk
  rw [e] at hk
  apply (mul_left_inj' hx).mp
  calc
    _ = corrected (x^1049601) * (x^1049600 * x) := by rw [mul_right_comm, mul_comm (x^1049600 * x)]
    _ = 1 := by rwa [← pow_succ]
    _ = x⁻¹ * x := (inv_mul_cancel₀ hx).symm

end M31CosetInverse
