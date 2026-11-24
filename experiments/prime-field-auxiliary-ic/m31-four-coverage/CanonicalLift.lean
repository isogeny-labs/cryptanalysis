import FiberLift
import TerminalRoot
import PackedTraversal
import Mathlib.Data.List.Sort

namespace M31CanonicalLift

open M31FiberLift M31PairedCubic

private instance : Fact (Nat.Prime 2147483647) :=
  ⟨lucas_lehmer_sufficiency 31 (by decide) (by norm_num)⟩

def lower (z : F31) := if z.val ≤ (-z).val then z else -z

theorem lower_val (z : F31) : (lower z).val = min z.val (-z).val := by
  unfold lower
  split <;> rename_i h
  · rw [min_eq_left h]
  · rw [min_eq_right (by omega)]

private theorem lower_sq (z : F31) : (lower z)^2 = z^2 := by
  unfold lower
  split <;> simp

private theorem lower_bound (z : F31) : (lower z).val ≤ 1073741823 := by
  rw [lower_val]
  by_cases hz : z = 0
  · simp [hz]
  · let : NeZero z := ⟨hz⟩
    rw [ZMod.val_neg_of_ne_zero]
    omega

private theorem unique_low {a b : F31} (ha : a.val ≤ 1073741823) (hb : b.val ≤ 1073741823)
    (eq : a^2 = b^2) : a = b := by
  rcases sq_eq_sq_iff_eq_or_eq_neg.mp eq with same | opposite
  · exact same
  · by_cases h : b = 0
    · simpa [h] using opposite
    · let : NeZero b := ⟨h⟩
      rw [opposite, ZMod.val_neg_of_ne_zero] at ha
      omega

def ordinate (r : F31) : Option F31 :=
  let z := r^(2^29 : Nat)
  if z^2 = r then some (lower z) else none

theorem ordinate_spec (r y : F31) :
    ordinate r = some y ↔ y^2 = r ∧ y.val ≤ 1073741823 := by
  have accepts := lift_exact (fun _ : Unit => r) ()
  rw [lane_power] at accepts
  unfold ordinate
  dsimp only
  split <;> rename_i hz
  · simp only [Option.some.injEq]
    constructor
    · rintro rfl
      exact ⟨(lower_sq _).trans hz, lower_bound _⟩
    · rintro ⟨hy, bound⟩
      exact unique_low (lower_bound _) bound ((lower_sq _).trans (hz.trans hy.symm))
  · constructor
    · simp
    · rintro ⟨hy, _⟩
      exact (hz (accepts.mpr ⟨y, hy⟩)).elim

theorem signed_candidate (r : F31) :
    (M31SignedSquare.canonical (M31SignedSquare.fold^[29] (r.val : Int)) : F31) =
      r^(2^29 : Nat) := by
  have hi : (r.val : Int) < M31SignedSquare.p := by unfold M31SignedSquare.p; exact_mod_cast r.val_lt
  rw [M31SignedSquare.terminal_root_exact _ (by positivity) hi]
  change (((r.val : Int)^(2^29 : Nat) % (2147483647 : Nat) : Int) : ZMod 2147483647) = _
  rw [ZMod.intCast_mod, Int.cast_pow, Int.cast_natCast, ZMod.natCast_zmod_val]

def key (eval : F31 → F31) (x : F31) : Option Nat :=
  (ordinate (eval x)).map (fun y => pack x.val y.val)

theorem keys_spec (eval : F31 → F31) (xs : List F31) (x y : F31) :
    pack x.val y.val ∈ xs.filterMap (key eval) ↔
      x ∈ xs ∧ y^2 = eval x ∧ y.val ≤ 1073741823 := by
  rw [List.mem_filterMap]
  constructor
  · rintro ⟨u, hu, h⟩
    unfold key at h
    cases hit : ordinate (eval u) with
    | none => simp [hit] at h
    | some v =>
      simp [hit] at h
      have same := M31PackedTraversal.no_alias v.val_lt y.val_lt h
      have ux : u = x := ZMod.val_injective _ (congrArg Prod.fst same)
      have vy : v = y := ZMod.val_injective _ (congrArg Prod.snd same)
      subst u
      subst v
      exact ⟨hu, (ordinate_spec _ _).mp hit⟩
  · rintro ⟨hx, hy⟩
    exact ⟨x, hx, by simp [key, (ordinate_spec _ _).mpr hy]⟩

private theorem emitted_high (eval : F31 → F31) (x : F31) (k : Nat)
    (hit : k ∈ key eval x) : k >>> 31 = x.val := by
  cases h : ordinate (eval x) with
  | none => simp [key,h] at hit
  | some y =>
    have eq : pack x.val y.val = k := by simpa [key,h] using hit
    exact eq ▸ (unpack x.val y.val y.val_lt).1

theorem sorted_keys (eval : F31 → F31) (xs : List F31) (distinct : xs.Nodup) :
    let table := (xs.filterMap (key eval)).mergeSort
    table.Nodup ∧ ∀ x y : F31, pack x.val y.val ∈ table ↔
      x ∈ xs ∧ y^2 = eval x ∧ y.val ≤ 1073741823 := by
  dsimp only
  constructor
  · apply (List.mergeSort_perm _ _).nodup_iff.mpr
    apply distinct.filterMap
    intro a b k ha hb
    exact ZMod.val_injective _ ((emitted_high _ _ _ ha).symm.trans (emitted_high _ _ _ hb))
  · intro x y
    rw [List.mem_mergeSort]
    exact keys_spec _ _ _ _

theorem word_spec (eval : F31 → F31) (xs : List F31) (k : Nat) :
    k ∈ (xs.filterMap (key eval)).mergeSort ↔
      ∃ x ∈ xs, ∃ y : F31, y^2 = eval x ∧ y.val ≤ 1073741823 ∧ k = pack x.val y.val := by
  rw [List.mem_mergeSort]
  constructor
  · intro h
    obtain ⟨x, hx, hit⟩ := List.mem_filterMap.mp h
    cases hh : ordinate (eval x) with
    | none => simp [key, hh] at hit
    | some y =>
      have spec := (ordinate_spec _ _).mp hh
      exact ⟨x, hx, y, spec.1, spec.2, by simpa [key, hh] using hit.symm⟩
  · rintro ⟨x, hx, y, hy, bound, rfl⟩
    exact (keys_spec _ _ _ _).mpr ⟨hx, hy, bound⟩

theorem traversal_independent (eval : F31 → F31) (xs : Nat → F31) (v : Nat)
    (hv : v ∈ [4,8,16,32]) :
    let indices := List.range 128
    let build := fun (positions : List Nat) => ((positions.map xs).filterMap (key eval)).mergeSort
    build (indices.map (M31PackedTraversal.slot v)) = build indices := by
  dsimp only
  have perm := ((M31PackedTraversal.all_slots v hv).map xs).filterMap (key eval)
  exact ((List.mergeSort_perm _ _).trans (perm.trans (List.mergeSort_perm _ _).symm)).eq_of_pairwise'
    (List.pairwise_mergeSort' (· ≤ ·) _) (List.pairwise_mergeSort' (· ≤ ·) _)

end M31CanonicalLift
