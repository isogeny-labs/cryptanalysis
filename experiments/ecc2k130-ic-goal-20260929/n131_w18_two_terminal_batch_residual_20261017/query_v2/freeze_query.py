"""Freeze same-target batch query inputs and 590-second solver allowance."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
ROOT=PARENT.parent
OLD=ROOT/'n131_w18_two_terminal_bilinear_20261015'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_exact(name):
    data=(OLD/name).read_bytes()
    with (HERE/name).open('xb') as stream:
        stream.write(data)
    assert sha(HERE/name)==sha(OLD/name)


def main():
    for name in ('pool.json','control_fixture.json','control_result.json','prepare.py'):
        copy_exact(name)
    old=json.loads((OLD/'protocol.json').read_text())
    assert old['status']=='FROZEN_BILINEAR_TWO_TERMINAL_BEFORE_QUERY'
    assert old['target_dependent_cap_seconds']==600
    assert json.loads((PARENT/'verification.json').read_text())['status']==\
        'PASS_INDEPENDENT_N131_BATCH_RESIDUAL_REPLAY'
    sources={'query.py':HERE/'query.py','preflight.py':HERE/'preflight.py',
             'freeze_query.py':HERE/'freeze_query.py',
             'batch.py':PARENT/'batch.py',
             'batch_verification.json':PARENT/'verification.json',
             'prior_query_result.json':OLD/'query_result.json',
             'prior_sage_audit_result.json':OLD/'sage_audit_result.json',
             'sage_runtime_info.json':HERE/'sage_runtime_info.json'}
    old['solver_cap_seconds']=590
    old['solver_flags']=['--threads=1','--maxtime=590','--zero-exit-status',
                         '--verb=1','--printsol=1']
    old['batch_route']={'status':'FROZEN_EXACT_BATCH_RESIDUAL_ROUTE',
                        'source_sha256':{name:sha(path) for name,path in sources.items()},
                        'prior_formula_sha256':json.loads(
                            sources['prior_query_result.json'].read_text())['formula']['xcnf_sha256']}
    with (HERE/'protocol.json').open('x') as stream:
        json.dump(old,stream,sort_keys=True,indent=2);stream.write('\n')
    print('FROZEN_N131_SAME_TARGET_BATCH_QUERY',flush=True)


if __name__=='__main__':
    main()
