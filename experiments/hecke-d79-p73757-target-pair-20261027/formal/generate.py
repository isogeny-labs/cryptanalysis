"""Generate conditional pair transport and finite scalar certificates."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
REPO=ROOT.parent.parent
PLAN=json.loads((ROOT/'inputs.json').read_text())
POST=json.loads((ROOT/'post_run.json').read_text())


def frozen(name):
    item=PLAN['frozen'][name]
    raw=(REPO/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def main():
    raw=(ROOT/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    result=json.loads(raw)
    logs=frozen('anchor-solve.json')['recovered_q_logs']
    i,a,j,b=result['witness']
    assert a==-1 and b==1 and i<j
    q=PLAN['q'];scalar=result['recovered_scalar']
    assert (-logs[i]+logs[j])%q==scalar
    lines=['module','','public import Init','','namespace TargetPair',
           'public theorem pair_transport {G H : Type}',
           '    (addG : G → G → G) (negG : G → G)',
           '    (addH : H → H → H) (negH : H → H)',
           '    (φ : G → H) (B1 B4 Q : G)',
           '    (map_add : ∀ x y, φ (addG x y) = addH (φ x) (φ y))',
           '    (map_neg : ∀ x, φ (negG x) = negH (φ x))',
           '    (pair_relation : Q = addG (negG B1) B4) :',
           '    φ Q = addH (negH (φ B1)) (φ B4) := by',
           '  rw [pair_relation, map_add, map_neg]',
           f'public def firstLog : Nat := {logs[i]}',
           f'public def secondLog : Nat := {logs[j]}',
           f'public def recovered : Nat := {scalar}',
           f'public theorem scalar_certificate : (({q} - firstLog) + secondLog) % {q} = recovered := by decide',
           '#print axioms pair_transport',
           '#print axioms scalar_certificate',
           'end TargetPair','']
    (HERE/'TargetPair.lean').write_text('\n'.join(lines))
    cert={'schema':'hecke-d79-p73757-target-pair-cert-v1','witness':result['witness'],
          'q':q,'logs':[logs[i],logs[j]],'recovered_scalar':scalar,
          'result_sha256':POST['result_sha256']}
    (HERE/'certificate.json').write_text(json.dumps(cert,indent=2,sort_keys=True)+'\n')
    print(json.dumps(cert))


if __name__=='__main__':
    main()
