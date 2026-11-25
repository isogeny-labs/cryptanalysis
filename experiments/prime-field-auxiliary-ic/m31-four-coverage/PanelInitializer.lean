import Lean
import Mathlib.Data.ZMod.Basic
import Mathlib.Tactic

namespace M31PanelInitializer

open Lean
elab "archivedTerminals" : term => do
  let rows := ((include_str "fiber-masks.csv").trimAscii.toString.splitOn "\n").drop 1
  let values ← rows.mapM fun row => do
    match row.splitOn "," with
    | [_, terminal, _] =>
      match terminal.toNat? with
      | some t => pure t
      | none => throwError "invalid terminal"
    | _ => throwError "invalid panel row"
  return toExpr values

abbrev M := ZMod 2147483647
def terminals : List Nat := archivedTerminals
def squareRoot (x : M) := (fun v : M => v*v)^[29] x
private theorem iter_square (x : M) (k : Nat) :
    (fun v : M => v*v)^[k] x = x^(2^k) := by
  induction k with
  | zero => simp
  | succ k ih => rw [Function.iterate_succ_apply', ih, pow_succ 2 k, pow_mul, sq]

theorem squareRoot_eq_pow (x : M) : squareRoot x = x^536870912 := iter_square x 29

def forward (x : M) := x*x-2
def descend (x : M) := squareRoot (x+2)

def leaf (t : M) := descend^[7] t
def step (t : M) := forward^[24] (leaf t)
def delta (t : M) := ((leaf t)^2-4)*((step t)^2-4)
def neighbor (t : M) := (leaf t * step t + squareRoot (delta t)) * 1073741824

def Valid (t : M) : Prop :=
  forward^[7] (leaf t) = t ∧ forward^[23] t = -2 ∧
  (squareRoot (delta t))^2 = delta t ∧
  2 * neighbor t = leaf t * step t + squareRoot (delta t)

instance (t : M) : Decidable (Valid t) := by unfold Valid; infer_instance

theorem panel_identity : terminals.length = 32 ∧ terminals.Nodup := by decide +kernel

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
theorem panel_valid : ∀ t ∈ terminals, Valid (t : M) := by decide +kernel

set_option maxRecDepth 32768 in
set_option maxHeartbeats 8000000 in
theorem inverse_edges : ∀ n ∈ terminals, ∀ i : Fin 7,
    forward (descend^[i.val+1] (n : M)) = descend^[i.val] (n : M) := by decide +kernel

end M31PanelInitializer
