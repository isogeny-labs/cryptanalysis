"""Generate the exact three-term scalar and conditional transport proof."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
REPO=ROOT.parent.parent
PLAN=json.loads((ROOT/'inputs.json').read_text())
POST=json.loads((ROOT/'post-run.json').read_text())


def parent(name):
    item=PLAN['frozen'][name]
    raw=(REPO/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def main():
    raw=(ROOT/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    result=json.loads(raw)
    logs=parent('class-logs.json')['q_logs']
    i,a,j,b,k,c=result['witness']
    assert (a,b,c)==(1,1,1) and len({i,j,k})==3
    values=[logs[i],logs[j],logs[k]]
    scalar=result['recovered_scalar']
    assert sum(values)%PLAN['q']==scalar
    lines=['module','','public import Init','','namespace TargetTriple',
           'public theorem triple_transport {G H : Type}',
           '    (addG : G → G → G) (addH : H → H → H) (φ : G → H)',
           '    (B7 B28 B2 Q : G)',
           '    (map_add : ∀ x y, φ (addG x y) = addH (φ x) (φ y))',
           '    (triple_relation : Q = addG (addG B7 B28) B2) :',
           '    φ Q = addH (addH (φ B7) (φ B28)) (φ B2) := by',
           '  rw [triple_relation, map_add, map_add]',
           f'public def log7 : Nat := {values[0]}',
           f'public def log28 : Nat := {values[1]}',
           f'public def log2 : Nat := {values[2]}',
           f'public def targetScalar : Nat := {scalar}',
           f'public theorem scalar_certificate : (log7 + log28 + log2) % {PLAN["q"]} = targetScalar := by decide',
           '#print axioms triple_transport','#print axioms scalar_certificate',
           'end TargetTriple','']
    (HERE/'TargetTriple.lean').write_text('\n'.join(lines))
    cert={'schema':'hecke-d79-p63317-target-triple-cert-v1','witness':result['witness'],
          'logs':values,'q':PLAN['q'],'recovered_scalar':scalar,
          'result_sha256':POST['result_sha256']}
    (HERE/'certificate.json').write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n')
    print(json.dumps(cert))


if __name__=='__main__':
    main()
