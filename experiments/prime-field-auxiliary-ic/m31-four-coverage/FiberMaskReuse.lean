import Lean
import Mathlib.Tactic

namespace M31FiberMaskReuse

open Lean
elab "panelMasks" : term => do
  let lines := ((include_str "fiber-masks.csv").trimAscii.toString.splitOn "\n").drop 1
  let rows ← lines.mapM fun line => do
    match line.splitOn "," with
    | [k,t,m] =>
      match k.toNat?, t.toNat?, m.toNat? with
      | some k, some t, some m => pure (k,t,m)
      | _,_,_ => throwError "invalid number"
    | _ => throwError "invalid mask row"
  return toExpr rows

private def records : List (Nat × Nat × Nat) := panelMasks
private def masks := records.map (fun r => r.2.2)
private def positive (k : Nat) := (masks.filter (fun m => m.testBit k)).length
private def negative (k : Nat) := masks.length - positive k
private def keys := List.range 128
private def errors (classify : Nat → Bool) :=
  (keys.map (fun k => if classify k then negative k else positive k)).sum

theorem panel :
    masks.length = 32 ∧ (records.map (·.1)) = (List.range 32).map (2*·+1) ∧
    (records.map (·.2.1)).Nodup ∧ masks.Nodup ∧
    keys.all (fun k => positive k > 0 && negative k > 0) = true ∧
    (keys.map (fun k => min (positive k) (negative k))).sum = 1761 := by decide +kernel

private theorem lower (f : Nat → Bool) (ks : List Nat) :
    (ks.map (fun k => min (positive k) (negative k))).sum ≤
      (ks.map (fun k => if f k then negative k else positive k)).sum := by
  induction ks with
  | nil => rfl
  | cons k ks ih =>
    simp only [List.map_cons, List.sum_cons]
    apply Nat.add_le_add _ ih
    cases f k <;> simp

theorem optimum : (∀ f, 1761 ≤ errors f) ∧ ∃ f, errors f = 1761 := by
  constructor
  · intro f
    rw [← panel.2.2.2.2.2]
    exact lower f keys
  · exact ⟨fun k => positive k > negative k, by decide +kernel⟩

/-- A terminal-blind filter retaining every positive must retain every key. -/
theorem lossless_filter (keep : Nat → Bool)
    (safe : ∀ k ∈ keys, positive k > 0 → keep k = true) :
    ∀ k ∈ keys, keep k = true := by
  intro k hk
  have both := (List.all_eq_true.mp panel.2.2.2.2.1) k hk
  simp at both
  exact safe k hk both.1

-- A paired bank may reject a key if both constituent masks reject it.
private abbrev I := Fin 16
private def weight (i j : I) : Nat :=
  (keys.filter (fun k => !(masks[i.val]!.testBit k || masks[16+j.val]!.testBit k))).length

private def pairing : I → I := ![10,7,6,5,2,4,13,1,15,11,3,0,14,9,8,12]
private def leftPrice : I → Nat := ![28,34,37,34,32,34,30,34,30,34,36,34,34,28,38,34]
private def rightPrice : I → Nat := ![2,0,1,4,0,1,3,2,3,3,1,5,5,3,6,4]

private theorem feasible (i j : I) : weight i j ≤ leftPrice i + rightPrice j := by
  revert i j
  decide +kernel

theorem pairing_attains :
    Function.Injective pairing ∧ (∑ i, weight i (pairing i)) = 574 := by
  unfold Function.Injective
  decide +kernel

theorem pairing_upper_bound (perm : I ≃ I) : (∑ i, weight i (perm i)) ≤ 574 := by
  calc
    _ ≤ ∑ i, (leftPrice i + rightPrice (perm i)) :=
      Finset.sum_le_sum (fun i _ => feasible i (perm i))
    _ = (∑ i, leftPrice i) + ∑ i, rightPrice i := by
      rw [Finset.sum_add_distrib, perm.sum_comp rightPrice]
    _ = 574 := by decide +kernel

end M31FiberMaskReuse
