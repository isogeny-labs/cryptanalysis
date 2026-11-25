import Lean
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.Group.Basic

namespace M31FourCoverage.Walk

/-- In a symmetric endpoint distribution, the number of ordered returns
formed from two halves is the collision count of their endpoint histogram. -/
theorem return_pairs {G : Type*} [AddCommGroup G] [Fintype G]
    (count : G → Nat) (symm : ∀ x, count (-x) = count x) :
    (∑ x, count x * count (-x)) = ∑ x, count x ^ 2 := by
  simp [symm, pow_two]

elab "walkBins" : term => do
  let rows := ((include_str "walk-four.csv").trimAscii.toString.splitOn "\n").drop 1
  let bins ← rows.mapM fun line => do
    match line.splitOn "," with
    | [k,n] =>
      let some k := k.toNat? | throwError "invalid walk multiplicity"
      let some n := n.toNat? | throwError "invalid point count"
      pure (k,n)
    | _ => throwError "invalid walk histogram row"
  return Lean.toExpr bins

private def bins : List (Nat × Nat) := walkBins
private abbrev paths := 390^4
private abbrev order := 2147505293

/-- The last two sums are the scaled uniform deficit and surplus.
Natural subtraction takes the positive part in each bin. -/
theorem histogram_totals :
    (bins.map Prod.snd).sum = order ∧
    (bins.map (fun (k,n) => n*k)).sum = paths ∧
    (bins.map (fun (k,n) => n*k^2)).sum = 2640817050634 ∧
    (bins.map (fun (k,n) => n*(paths-k*order))).sum = 31711602804266967032 ∧
    (bins.map (fun (k,n) => n*(k*order-paths))).sum = 31711602804266967032 := by
  decide +kernel

-- Upper bound the mass in an arc by paying k per slot and charging all
-- excess above k, even at points outside the arc.
private def outside (j : Nat) : Nat :=
  let cap := 1 + 2*((order*j-1)/128)
  let k := if j ≤ 4 then 48 else if j ≤ 22 then 24 else if j = 23 then 12 else 0
  paths - (cap*k + (bins.map (fun (m,n) => n*(m-k))).sum)

private def price (j : Nat) : Nat :=
  let u := 3*j
  let den := 6*128^3
  2000000*(6*128^2*u-u^3)^2 / den^2

theorem spectral_loss :
    ((List.range 24).map (fun j => (price (j+1) - price j)*outside (j+1))).sum =
      3147515720318076 ∧
    ((List.range 24).all (fun j => price j ≤ price (j+1))) = true := by
  decide +kernel

-- Integer comparisons after squaring the L2 to TV inequality twice.
private def meets (steps denominator : Nat) : Bool :=
  let moment := order * 2640817050634 - paths^2
  moment^2 * 1665574523306827^(steps-4) * denominator^4 ≤
    16 * paths^4 * 1927867500000000^(steps-4)

theorem tv_thresholds :
    meets 54 4 && meets 142 100 && meets 205 1000 && meets 394 1000000 := by
  decide +kernel

end M31FourCoverage.Walk
