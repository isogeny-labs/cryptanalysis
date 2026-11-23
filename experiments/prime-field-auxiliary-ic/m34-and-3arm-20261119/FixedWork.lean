import Lean
import Mathlib.Tactic

namespace M31FixedWork

/-- Rounding total and decomposition independently to 100 us introduces
at most 100 us of downward uncertainty in their difference. -/
theorem residual_floor (total decomp printedTotal printedDecomp : ℕ)
    (ht : printedTotal ≤ total + 50000) (hd : decomp ≤ printedDecomp + 50000) :
    printedTotal - printedDecomp - 100000 ≤ total - decomp := by omega

/-- Even completely free decomposition cannot close a strict residual gap. -/
theorem fixed_work_gap (residual newDecomp rho bound : ℕ) (hr : rho ≤ bound)
    (gap : bound < residual) : rho < residual + newDecomp := by omega

elab "timingRows" : term => do
  let lines := ((include_str "fixed-work.csv").trimAscii.toString.splitOn "\n").drop 1
  let rows ← lines.mapM fun line => do
    match line.splitOn "," with
    | [_,m,_,t,d,lo,_,r,s,_] =>
      match m.toNat?,t.toNat?,d.toNat?,lo.toNat?,r.toNat?,s.toNat? with
      | some m,some t,some d,some lo,some r,some s => pure (m,t,d,lo,r,s)
      | _,_,_,_,_,_ => throwError "bad integer"
    | _ => throwError "bad row"
  return Lean.toExpr rows

private def rows : List (ℕ × ℕ × ℕ × ℕ × ℕ × ℕ) := timingRows

theorem panel_totals :
    rows.length = 46 ∧
    rows.all (fun (_,t,d,lo,r,_) => lo == t-d-100000 && r < lo) = true ∧
    (rows.filter (fun (_,_,_,lo,_,s) => s < lo)).length = 44 ∧
    (rows.filter (fun (m,_,_,lo,_,s) => s ≥ lo && m == 4)).length = 2 := by
  decide +kernel

open Lean

private def nanoseconds (obj : Json) (key : String) (digits : Nat) : Except String Nat := do
  let n ← (← obj.getObjVal? key).getNum?
  if n.mantissa < 0 || n.exponent > digits then throw "unrepresentable interval"
  return n.mantissa.toNat * 10^(digits-n.exponent)

private def onlineGroup (m : Nat) (arms : Json) : Except String (List (Nat × Nat × Nat)) := do
  let ref ← (← arms.getObjVal? "arm_A_auxiliary").getObjVal? "rho"
  let cap := (← nanoseconds ref "online_ms" 6) + 50
  (← arms.getObj?).toList.mapM fun (_,r) => do
    let total ← nanoseconds r "online_s" 9
    let part ← nanoseconds r "decomposition_s" 9
    return (m,total-part-100000,cap)

elab "archivedOnlineRows" : term => do
  let data ← Lean.ofExcept (Json.parse (include_str "end_to_end_solves_summary.json"))
  let targets ← Lean.ofExcept ((data.getObjVal? "e1_m2_5target_solves").bind Json.getArr?)
  let two ← targets.toList.mapM fun (t : Json) => Lean.ofExcept ((t.getObjVal? "arms").bind (onlineGroup 2))
  let higher ← Lean.ofExcept (data.getObjVal? "e1_m3_m4_solves_T0")
  let three ← Lean.ofExcept ((higher.getObjVal? "m3").bind (onlineGroup 3))
  let four ← Lean.ofExcept ((higher.getObjVal? "m4").bind (onlineGroup 4))
  return toExpr (two.flatten ++ three ++ four)

private def onlineRows : List (Nat × Nat × Nat) := archivedOnlineRows

/-- Direct JSON replay, using only the online phase and the same-panel rho. -/
theorem online_floor :
    onlineRows.length = 46 ∧
    onlineRows.all (fun (m,lo,cap) =>
      if m = 2 then 809 * cap < 10 * lo
      else if m = 3 then 738 * cap < 100 * lo
      else m == 4 && 116 * cap < 100 * lo) = true := by
  decide +kernel

end M31FixedWork
