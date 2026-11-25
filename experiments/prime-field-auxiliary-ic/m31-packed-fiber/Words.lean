import Std.Tactic.BVDecide
import Init.Data.BitVec.Lemmas

namespace M31PackedFiber.Words

abbrev p : Nat := 2147483647
abbrev w : BitVec 32 := 2147483647

def add (x y : BitVec 32) := if x+y ≥ w then x+y-w else x+y
def sub (x y : BitVec 32) := if x ≥ y then x-y else w-(y-x)
def mul (x y : BitVec 32) :=
  ((x.setWidth 64 * y.setWidth 64) % (2147483647 : BitVec 64)).setWidth 32

theorem add_spec (x y : BitVec 32) (hx : x.toNat < p) (hy : y.toNat < p) :
    (add x y).toNat = (x.toNat + y.toNat) % p := by
  have hs := BitVec.toNat_add_of_lt (x := x) (y := y) (by unfold p at *; omega)
  unfold add
  split
  next h =>
    rw [BitVec.toNat_sub_of_le h, hs]
    change 2147483647 ≤ (x+y).toNat at h
    rw [hs] at h
    change _ - 2147483647 = _ % 2147483647
    unfold p at hx hy
    omega
  next h =>
    rw [hs]
    change ¬ 2147483647 ≤ (x+y).toNat at h
    rw [hs] at h
    exact (Nat.mod_eq_of_lt (Nat.lt_of_not_ge h)).symm

theorem sub_spec (x y : BitVec 32) (hx : x.toNat < p) (hy : y.toNat < p) :
    (sub x y).toNat = (x.toNat + p - y.toNat) % p := by
  unfold sub
  split
  next h =>
    rw [BitVec.toNat_sub_of_le h]
    change y.toNat ≤ x.toNat at h
    unfold p at *
    omega
  next h =>
    have hxy : x ≤ y := by change x.toNat ≤ y.toNat; change ¬ y.toNat ≤ x.toNat at h; omega
    have hd := BitVec.toNat_sub_of_le hxy
    have hw : y-x ≤ w := by change (y-x).toNat ≤ p; rw [hd]; omega
    rw [BitVec.toNat_sub_of_le hw, hd]
    change ¬ y.toNat ≤ x.toNat at h
    change p - _ = _
    unfold p at *
    omega

theorem mul_spec (x y : BitVec 32) :
    (mul x y).toNat = x.toNat * y.toNat % p := by
  have h := BitVec.toNat_mul_toNat_lt (x := x) (y := y)
  have hx := BitVec.toNat_setWidth_of_le (b := x) (show 32 ≤ 64 by decide)
  have hy := BitVec.toNat_setWidth_of_le (b := y) (show 32 ≤ 64 by decide)
  unfold mul
  rw [BitVec.toNat_setWidth, BitVec.toNat_umod, BitVec.toNat_mul, hx, hy, Nat.mod_eq_of_lt h]
  change (_ % p) % 4294967296 = _
  exact Nat.mod_eq_of_lt (Nat.lt_trans (Nat.mod_lt _ (by decide : 0 < p)) (by decide))

/-- One iteration of the unsigned maximum scan in distinct.c. -/
def scanStep (acc x : BitVec 32) := if x > acc then x else acc

theorem scanStep_lt (acc x : BitVec 32) :
    scanStep acc x < w ↔ acc < w ∧ x < w := by
  unfold scanStep
  split <;> bv_decide

/-- Characterize the loop from any incoming accumulator, including SIMD chunks. -/
theorem scan_lt (xs : List (BitVec 32)) (acc : BitVec 32) :
    xs.foldl scanStep acc < w ↔ acc < w ∧ ∀ x ∈ xs, x < w := by
  induction xs generalizing acc with
  | nil => simp
  | cons x xs ih =>
    simp only [List.foldl_cons, ih, scanStep_lt, List.mem_cons]
    constructor
    · rintro ⟨⟨ha, hx⟩, ht⟩
      exact ⟨ha, fun y hy => hy.elim (fun e => e ▸ hx) (ht y)⟩
    · rintro ⟨ha, hall⟩
      exact ⟨⟨ha, hall x (Or.inl rfl)⟩, fun y hy => hall y (Or.inr hy)⟩

theorem canonical_scan (xs : List (BitVec 32)) :
    xs.foldl scanStep 0 < w ↔ ∀ x ∈ xs, x.toNat < p := by
  rw [scan_lt, and_iff_right (by decide : (0 : BitVec 32) < w)]
  rfl

/-- Reducing each lane separately preserves the same acceptance predicate. -/
theorem canonical_chunks (chunks : List (List (BitVec 32))) :
    (chunks.map (fun xs => xs.foldl scanStep 0)).foldl scanStep 0 < w ↔
    chunks.flatten.foldl scanStep 0 < w := by
  simp only [canonical_scan, List.forall_mem_map, List.mem_flatten]
  change (∀ xs ∈ chunks, xs.foldl scanStep 0 < w) ↔ _
  constructor
  · intro h x hx
    obtain ⟨xs, hxs, hx⟩ := hx
    exact (canonical_scan xs).mp (h xs hxs) x hx
  · intro h xs hxs
    exact (canonical_scan xs).mpr (fun x hx => h x ⟨xs, hxs, hx⟩)

end M31PackedFiber.Words
