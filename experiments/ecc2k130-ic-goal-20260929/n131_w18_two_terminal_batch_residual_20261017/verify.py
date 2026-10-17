"""Audit frozen batch residual measurement against prior checked Sage replay."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD = ROOT/'n131_w18_two_terminal_bilinear_20261015'
ARITH = ROOT/'n131_fixed_seed_halftrace_cubic_20261011/verify.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    protocol_path=HERE/'protocol.json';result_path=HERE/'result.json'
    protocol=json.loads(protocol_path.read_text())
    result=json.loads(result_path.read_text())
    paths={'batch.py':HERE/'batch.py','run.py':HERE/'run.py',
           'freeze.py':HERE/'freeze.py','arithmetic.py':ARITH,
           'pool.json':OLD/'pool.json','query_result.json':OLD/'query_result.json',
           'control_result.json':OLD/'control_result.json',
           'old_terminal.py':OLD/'terminal.py','old_protocol.json':OLD/'protocol.json'}
    assert protocol['input_sha256']=={name:sha(path) for name,path in paths.items()}
    assert result['protocol_sha256']==sha(protocol_path)
    assert result['status']=='PASS_N131_BATCH_RESIDUAL_EXACT_REPLAY'
    assert result['peak_self_rss_raw']<protocol['resource_envelope']['rss_cap_bytes']
    sage_audit_path=OLD/'sage_audit_result.json'
    sage_audit=json.loads(sage_audit_path.read_text())
    assert sage_audit['status']=='PASS_INDEPENDENT_SAGE_BILINEAR_TWO_TERMINAL_FIBERS'
    assert sage_audit['replayed_control_and_public_residuals']==4160
    assert sage_audit['sha256']['pool']==sha(paths['pool.json'])
    assert sage_audit['sha256']['query']==sha(paths['query_result.json'])
    assert sage_audit['sha256']['control']==sha(paths['control_result.json'])
    arith=load_module('independent_n131_arithmetic',ARITH)
    batch=load_module('measured_batch',HERE/'batch.py')
    inputs=[1,2,3,5,7,11,13,17]
    got,count=batch.batch_invert(inputs,arith.mul,arith.inverse)
    assert count==1
    assert got==[arith.inverse(value) for value in inputs]
    states=json.loads(paths['pool.json'].read_text())['joint_states']
    checks=[]
    for row,source_name,target_name in zip(result['rows'],
                                            ('query_result.json','control_result.json'),
                                            ('raw_target','control_raw_target')):
        previous=json.loads(paths[source_name].read_text())
        assert row['raw_target']==previous[target_name]
        assert row['residual_count']==2080
        assert row['archived_residuals_sha256']==sha(paths[source_name])
        phase=row['batch_phase_ns']
        assert phase['batch_inversions']==2 and phase['fallback_point_additions']==0
        assert phase['nonexceptional_residuals']==2080 and phase['exceptional_residuals']==0
        assert sum(value for key,value in phase.items() if key.endswith('_ns'))<=row['batch_ns']
        replay,_=batch.residuals(row['raw_target'],states,arith)
        assert replay==previous['residuals']
        digest=hashlib.sha256(json.dumps(replay,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert digest==row['ordered_residuals_sha256']
        checks.append({'label':row['label'],'residuals':len(replay),
                       'batch_inversions':phase['batch_inversions'],'residual_sha256':digest})
    assert result['rows'][0]['matched_scalar_ns']>0
    receipt={'status':'PASS_INDEPENDENT_N131_BATCH_RESIDUAL_REPLAY',
             'protocol_sha256':sha(protocol_path),'result_sha256':sha(result_path),
             'prior_sage_audit_sha256':sha(sage_audit_path),
             'verifier_sha256':sha(Path(__file__)),'checks':checks}
    (HERE/'verification.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],flush=True)


if __name__=='__main__':
    main()
