import Std.Tactic.BVDecide
import Init.Data.BitVec.Lemmas

namespace M31MaskEmit

abbrev Word := BitVec 64

theorem clear_decreases (m : Word) (h : m ≠ 0) :
    m &&& (m-1) < m := by bv_decide

theorem clear_exact (m : Word) (h : m ≠ 0) :
    m &&& (m-1) = m ^^^ (1#64 <<< m.ctz) := by bv_decide

theorem upper_lane (i : BitVec 8) (h : i < 64) :
    ((127 - i) ^^^ 64) = 63 - i := by bv_decide

def present (m i : Word) : Prop := (m >>> i) &&& 1 = 1

theorem clear_spec (m i : Word) (h : m ≠ 0) :
    present (m &&& (m-1)) i ↔ present m i ∧ i ≠ m.ctz := by
  unfold present
  bv_decide

theorem least (m i : Word) (h : present m i) : m.ctz ≤ i := by
  unfold present at h
  bv_decide

theorem first_present (m : Word) (h : m ≠ 0) : present m m.ctz := by
  unfold present
  bv_decide

def emit (m : Word) : List Word :=
  if h : m = 0 then [] else m.ctz :: emit (m &&& (m-1))
termination_by m.toNat
decreasing_by exact clear_decreases m h

theorem emit_spec (m : Word) :
    (∀ i, i ∈ emit m ↔ present m i) ∧ (emit m).Pairwise (· < ·) := by
  induction m using emit.induct with
  | case1 =>
    simp [emit, present]
  | case2 m h ih =>
    rw [emit]
    simp only [h, ↓reduceDIte]
    obtain ⟨mem, ordered⟩ := ih
    constructor
    · intro i
      rw [List.mem_cons, mem, clear_spec m i h]
      by_cases eq : i = m.ctz
      · subst i
        simp [first_present m h]
      · simp [eq]
    · apply List.pairwise_cons.mpr
      refine ⟨?_, ordered⟩
      intro i hi
      have atBit := (clear_spec m i h).mp ((mem i).mp hi)
      have le := least m i atBit.1
      have ne := atBit.2
      bv_decide

/-- A four-lane acceptance flag goes into exactly its assigned mask positions. -/
theorem insert_lanes (old nibble start lane : Word) (width : nibble < 16)
    (fits : start ≤ 60) :
    present (old ||| (nibble <<< start)) lane ↔
      present old lane ∨ (start ≤ lane ∧ lane < start + 4 ∧ present nibble (lane-start)) := by
  unfold present
  bv_decide

/-- Reading a reversed upper mask enumerates the corresponding original upper lanes. -/
theorem reverse_lane (m : Word) (i : Nat) (hi : i < 64) :
    m.reverse.getLsbD i = m.getLsbD (63-i) := by
  rw [BitVec.getLsbD_reverse, BitVec.getMsbD_eq_getLsbD]
  simp only [hi, decide_true, Bool.true_and]

end M31MaskEmit
