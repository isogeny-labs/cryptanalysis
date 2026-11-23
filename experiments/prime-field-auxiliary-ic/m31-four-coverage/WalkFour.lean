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

end M31FourCoverage.Walk
