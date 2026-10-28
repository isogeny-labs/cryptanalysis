"""Generate the checked seven-row p1439 27-by-16 product ledger."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    audit_path=HERE/'audit.json'
    audit=json.loads(audit_path.read_text())
    assert audit['status']=='PASS_P1439_INDEPENDENT_PRODUCT_AUDIT'
    rows=audit['observed_primary_rows']
    assert len(rows)==7
    lean_rows=[]
    for row in rows:
        triple=', '.join(map(str,row['triple']))
        lean_rows.append('  { triple := [%s], paths27 := %d, factor16 := %d, predicted := %d, observed := %d }' %
                         (triple,row['rational_27_path_count'],row['prior_16_path_B_factor'],
                          row['predicted_multiplicity'],row['observed_multiplicity']))
    source='''import Mathlib.Data.Nat.Basic

/- Generated from audit.json SHA-256 %s. Each triple is [x_C,y_C,x_E,y_E,x_B,y_B] over F_1439. -/
namespace P1439ProductLedger

structure Row where
  triple : List Nat
  paths27 : Nat
  factor16 : Nat
  predicted : Nat
  observed : Nat
  deriving DecidableEq

def rows : List Row := [
%s
]

theorem seven_fibers : rows.length = 7 := by decide

theorem frozen_product_rule :
    ∀ r ∈ rows, r.predicted = r.paths27 * r.factor16 := by
  simp [rows]

theorem all_predictions_match : ∀ r ∈ rows, r.predicted = r.observed := by
  simp [rows]

theorem three_empty_fibers : (rows.filter (fun r => r.observed == 0)).length = 3 := by decide

theorem four_double_fibers : (rows.filter (fun r => r.observed == 2)).length = 4 := by decide

theorem eight_source_chains : (rows.map (·.observed)).sum = 8 := by decide

#print axioms seven_fibers
#print axioms frozen_product_rule
#print axioms all_predictions_match
#print axioms three_empty_fibers
#print axioms four_double_fibers
#print axioms eight_source_chains

end P1439ProductLedger
''' % (sha256(audit_path.read_bytes()).hexdigest(),',\n'.join(lean_rows))
    path=HERE/'formal'/'ProductLedger.lean'
    path.write_text(source)
    print(sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':main()
