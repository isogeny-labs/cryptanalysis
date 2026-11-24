import Std.Tactic.BVDecide

namespace M31XorLookup

abbrev Chunk := BitVec 6
abbrev Label := BitVec 7

def clear (v : Chunk) := v &&& (v-1)
def low (v : Chunk) := v &&& (-v)

private theorem split_bits (v : Chunk) : clear v ^^^ low v = v := by
  unfold clear low
  bv_decide

private theorem prior (v : Chunk) (nz : v ≠ 0) : clear v < v := by
  unfold clear
  bv_decide

-- The least set bit selects one of the initially assigned entries.
private theorem singleton (v : Chunk) : clear (low v) = 0 := by
  unfold clear low
  bv_decide

-- The loop writes only the current entry. At a power of two the low-bit
-- read aliases that entry, so both operands must come from the old table.
def update (t : Chunk → Label) (v i : Chunk) : Label :=
  if i = v then t (clear v) ^^^ t (low v) else t i

def build (initial : Chunk → Label) : Nat → Chunk → Label
  | 0 => initial
  | n+1 => update (build initial n) (BitVec.ofNat 6 (n+1))

-- All non-singleton contents at entry may be arbitrary.
theorem build_correct (h : Chunk → Label)
    (linear : ∀ a b, h (a ^^^ b) = h a ^^^ h b)
    (initial : Chunk → Label) (seeded : ∀ i, clear i = 0 → initial i = h i) :
    ∀ n ≤ 63, ∀ i, i.toNat ≤ n ∨ clear i = 0 → build initial n i = h i := by
  intro n
  induction n with
  | zero =>
    intro _ i covered
    apply seeded
    rcases covered with small | single
    · have z : i = 0 := BitVec.toNat_inj.mp (by simpa using small)
      simp [z,clear]
    · exact single
  | succ n ih =>
    intro bound i covered
    let v := BitVec.ofNat 6 (n+1)
    have val : v.toNat = n+1 := by
      change (n+1)%64 = n+1
      exact Nat.mod_eq_of_lt (by omega)
    change update (build initial n) v i = h i
    by_cases eq : i = v
    · subst i
      rw [update, ite_eq_left rfl, ih (by omega) _ (Or.inl ?_), ih (by omega) _ (Or.inr (singleton v)),
          ← linear, split_bits]
      have nz : v ≠ 0 := by intro z; simp [z] at val
      have less := prior v nz
      change (clear v).toNat < v.toNat at less
      omega
    · rw [update, ite_eq_right eq]
      apply ih (by omega)
      rcases covered with small | single
      · have ne : i.toNat ≠ v.toNat := fun e => eq (BitVec.toNat_inj.mp e)
        exact Or.inl (by omega)
      · exact Or.inr single

def chunk (x : BitVec 31) (s : Nat) : Chunk := (x >>> s).setWidth 6
def embed (v : Chunk) (s : Nat) : BitVec 31 := v.setWidth 31 <<< s

private theorem embed_xor (s : Nat) (a b : Chunk) :
    embed (a ^^^ b) s = embed a s ^^^ embed b s := by
  simp [embed, BitVec.shiftLeft_xor_distrib, BitVec.setWidth_xor]

private theorem table_read (h : BitVec 31 → Label)
    (linear : ∀ a b, h (a ^^^ b) = h a ^^^ h b) (s : Nat)
    (t : Chunk → Label) (seeded : ∀ i, clear i = 0 → t i = h (embed i s))
    (v : Chunk) : build t 63 v = h (embed v s) := by
  apply build_correct (fun i => h (embed i s)) _ t seeded 63 (by decide) v
  · exact Or.inl (by have := v.isLt; omega)
  · intro a b
    rw [embed_xor, linear]

private theorem unpack (x : BitVec 31) :
    (x &&& 127) ^^^ embed (chunk x 7) 7 ^^^ embed (chunk x 13) 13 ^^^
    embed (chunk x 19) 19 ^^^ embed (chunk x 25) 25 = x := by
  unfold embed chunk
  bv_decide

theorem lookup (h : BitVec 31 → Label)
    (linear : ∀ a b, h (a ^^^ b) = h a ^^^ h b)
    (low_identity : ∀ x : BitVec 31, h (x &&& 127) = x.setWidth 7)
    (tables : Nat → Chunk → Label)
    (seeded : ∀ s i, clear i = 0 → tables s i = h (embed i s))
    (x : BitVec 31) :
    x.setWidth 7 ^^^ build (tables 7) 63 (chunk x 7) ^^^
    build (tables 13) 63 (chunk x 13) ^^^ build (tables 19) 63 (chunk x 19) ^^^
    build (tables 25) 63 (chunk x 25) = h x := by
  rw [← low_identity x,
      table_read h linear 7 (tables 7) (seeded 7) (chunk x 7),
      table_read h linear 13 (tables 13) (seeded 13) (chunk x 13),
      table_read h linear 19 (tables 19) (seeded 19) (chunk x 19),
      table_read h linear 25 (tables 25) (seeded 25) (chunk x 25)]
  simp only [← linear]
  exact congrArg h (unpack x)

end M31XorLookup
