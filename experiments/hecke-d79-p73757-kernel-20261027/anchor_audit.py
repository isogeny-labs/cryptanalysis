"""Check all 40 coordinate anchors against each completed F199 matrix."""
import hashlib
import json
from pathlib import Path

import audit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
POST=json.loads((HERE/'post_run.json').read_text())


def frozen(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def main():
    raw=(HERE/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    result=json.loads(raw)
    cls=frozen('class-result.json')['cases'][0]
    prior=frozen('analysis.json')['cases'][0]
    five=frozen('result.json')
    base=[audit.sparse(x) for x in cls['base_rows']+prior['direct_candidates']+prior['hecke_candidates']]
    direct=[audit.sparse(x) for x in five['arms']['direct']['candidates']]
    hecke=[audit.sparse(x) for x in five['arms']['hecke']['candidates']]
    families={'support4_plus_direct5':base+direct,
              'support4_plus_hecke5':base+hecke,
              'support4_plus_both5':base+direct+hecke}
    output={'schema':'hecke-d79-p73757-anchor-audit-v1','status':'PASS','families':{}}
    for name,rows in families.items():
        ranks=[audit.rank(rows+[{i:1}],PLAN['q']) for i in range(40)]
        assert all(x==40 for x in ranks)
        assert all(result['q_logs'][i]!=0 for i in range(40))
        output['families'][name]={'coordinates_checked':40,'ranks_after_anchor':ranks}
    (HERE/'anchor-audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print('PASS: 40 coordinate anchors in each of three completed matrices')


if __name__=='__main__':
    main()
