import Mathlib.Data.Nat.Basic

/- Generated from audit.json SHA-256 97dde1c0a89115ec6664caad6dbdabb28cc22e739dfdee46612afa00047294aa. Source classes: 0 generic, 1 j=0, 2 j=1728. -/
namespace P1319Observed

structure Cell where
  sourceClass : Nat
  critical : Bool
  multiplicity : Nat
  signBranch : Bool
  count : Nat
  deriving DecidableEq

def cells : List Cell := [
  { sourceClass := 0, critical := false, multiplicity := 1, signBranch := false, count := 1272 },
  { sourceClass := 0, critical := true, multiplicity := 2, signBranch := false, count := 4 },
  { sourceClass := 0, critical := true, multiplicity := 2, signBranch := true, count := 4 },
  { sourceClass := 1, critical := false, multiplicity := 1, signBranch := false, count := 8 },
  { sourceClass := 2, critical := false, multiplicity := 0, signBranch := false, count := 4 },
  { sourceClass := 2, critical := false, multiplicity := 2, signBranch := false, count := 4 }
]

def genericRule : Prop :=
  ∀ c ∈ cells, c.sourceClass = 0 → (c.multiplicity = 2 ↔ c.critical = true)

theorem generic_rule : genericRule := by
  simp [genericRule, cells]

theorem observed_totals : (cells.map (·.count)).sum = 1296 := by decide

theorem generic_sign_branch_count :
    ((cells.filter (fun c => c.sourceClass == 0 && c.signBranch)).map (·.count)).sum = 4 := by decide

theorem j1728_exception_count :
    ((cells.filter (fun c => c.sourceClass == 2 && (c.multiplicity == 2 || c.multiplicity == 0))).map (·.count)).sum = 8 := by decide

theorem source_chain_total :
    ((cells.map (fun c => c.count * c.multiplicity)).sum) = 1304 := by decide

#print axioms generic_rule
#print axioms observed_totals
#print axioms generic_sign_branch_count
#print axioms j1728_exception_count
#print axioms source_chain_total

end P1319Observed
