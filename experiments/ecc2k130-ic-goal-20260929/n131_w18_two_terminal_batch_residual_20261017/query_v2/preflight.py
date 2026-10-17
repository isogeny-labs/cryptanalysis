"""Check batch residual identity and full XCNF hash before solver allocation."""
import hashlib
import json
from pathlib import Path

import query

HERE = Path(__file__).resolve().parent
OLD = HERE.parent.parent/'n131_w18_two_terminal_bilinear_20261015'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    old = query.configure()
    protocol = old.check_protocol()
    prior = json.loads((OLD/'query_result.json').read_text())
    assert protocol['public_target'] == prior['public_target']
    target = old.base.target_record()
    raw_target = target['preimages'][0]['point']
    assert raw_target == prior['raw_target']
    states = old.pool()['joint_states']
    residuals = old.residuals(raw_target,states)
    assert residuals == prior['residuals']
    _,root,nodes=old.base.source_domain()
    circuit,_=old.build(residuals,root,nodes)
    path=HERE/'preflight.xcnf'
    circuit.write(path)
    actual=sha(path)
    expected=prior['formula']['xcnf_sha256']
    assert actual==expected
    receipt={'status':'PASS_IDENTICAL_N131_BATCH_PUBLIC_XCNF',
             'public_target':protocol['public_target'],
             'raw_target':raw_target,'residual_count':len(residuals),
             'xcnf_sha256':actual,'xcnf_bytes':path.stat().st_size,
             'old_query_result_sha256':sha(OLD/'query_result.json'),
             'protocol_sha256':sha(HERE/'protocol.json'),
             'preflight_source_sha256':sha(Path(__file__))}
    (HERE/'preflight_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],actual,flush=True)


if __name__=='__main__':
    main()
