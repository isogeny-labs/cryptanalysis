"""Generate the exact compressed p1319 observation ledger for Lean checking."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
LABEL={'generic':0,'j0':1,'j1728':2}


def main():
    audit_path=HERE/'audit.json'
    audit=json.loads(audit_path.read_text())
    assert audit['status']=='PASS_P1319_INDEPENDENT_EXCEPTION_AUDIT'
    assert len(audit['observed_classes'])==6
    rows=[]
    for cell in audit['observed_classes']:
        rows.append('  { sourceClass := %d, critical := %s, multiplicity := %d, signBranch := %s, count := %d }' %
                    (LABEL[cell['source_class']],str(cell['predicted_double']).lower(),
                     cell['observed_multiplicity'],str(cell['sign_branch']).lower(),cell['count']))
    source='''import Mathlib.Data.Nat.Basic

/- Generated from audit.json SHA-256 %s. Source classes: 0 generic, 1 j=0, 2 j=1728. -/
namespace P1319Observed

structure Cell where
  sourceClass : Nat
  critical : Bool
  multiplicity : Nat
  signBranch : Bool
  count : Nat
  deriving DecidableEq

def cells : List Cell := [
%s
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
''' % (sha256(audit_path.read_bytes()).hexdigest(),',\n'.join(rows))
    path=HERE/'formal'/'ObservedClasses.lean'
    path.write_text(source)
    print(sha256(path.read_bytes()).hexdigest())


if __name__=='__main__': main()
