"""Read-only audit of the bounded same-formula N131 public-point query."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PARENT=HERE.parent
ROOT=PARENT.parent
OLD=ROOT/'n131_w18_two_terminal_bilinear_20261015'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol_path=HERE/'protocol.json'
    protocol=json.loads(protocol_path.read_text())
    old_protocol=json.loads((OLD/'protocol.json').read_text())
    old_result=json.loads((OLD/'query_result.json').read_text())
    preflight_path=HERE/'preflight_result.json'
    preflight=json.loads(preflight_path.read_text())
    query_path=HERE/'query_result.json'
    query=json.loads(query_path.read_text())
    sources={'query.py':HERE/'query.py','preflight.py':HERE/'preflight.py',
             'freeze_query.py':HERE/'freeze_query.py','batch.py':PARENT/'batch.py',
             'batch_verification.json':PARENT/'verification.json',
             'prior_query_result.json':OLD/'query_result.json',
             'prior_sage_audit_result.json':OLD/'sage_audit_result.json',
             'sage_runtime_info.json':HERE/'sage_runtime_info.json'}
    assert protocol['status']=='FROZEN_BILINEAR_TWO_TERMINAL_BEFORE_QUERY'
    assert protocol['batch_route']['status']=='FROZEN_EXACT_BATCH_RESIDUAL_ROUTE'
    assert protocol['batch_route']['source_sha256']=={name:sha(path) for name,path in sources.items()}
    assert protocol['source_sha256']==old_protocol['source_sha256']
    assert protocol['solver_cap_seconds']==590
    assert protocol['target_dependent_cap_seconds']==600
    assert protocol['worker_count']==1
    assert protocol['solver_flags']==['--threads=1','--maxtime=590',
                                      '--zero-exit-status','--verb=1','--printsol=1']
    for name in ('pool.json','control_fixture.json','control_result.json','prepare.py'):
        assert sha(HERE/name)==sha(OLD/name)
    assert protocol['source_sha256']['pool']==sha(HERE/'pool.json')
    assert protocol['source_sha256']['control_fixture']==sha(HERE/'control_fixture.json')
    assert protocol['source_sha256']['preparer']==sha(HERE/'prepare.py')
    assert preflight['status']=='PASS_IDENTICAL_N131_BATCH_PUBLIC_XCNF'
    assert preflight['protocol_sha256']==sha(protocol_path)
    assert preflight['xcnf_sha256']==sha(HERE/'preflight.xcnf')
    expected=old_result['formula']['xcnf_sha256']
    assert protocol['batch_route']['prior_formula_sha256']==preflight['xcnf_sha256']==expected
    assert query['protocol_sha256']==sha(protocol_path)
    assert query['curve_id']==protocol['curve_id']==old_result['curve_id']
    assert query['workload_id']==protocol['workload_id']==old_result['workload_id']
    assert query['public_target']==protocol['public_target']==old_result['public_target']
    assert query['raw_target']==old_result['raw_target']
    assert query['residuals']==old_result['residuals']
    assert len(query['residuals'])==2080
    assert query['formula']['xcnf_sha256']==sha(HERE/'ordinary.xcnf')==expected
    assert query['formula']['xcnf_bytes']==(HERE/'ordinary.xcnf').stat().st_size
    for key in ('variables','and_gates','clauses','native_xor_rows'):
        assert query['formula'][key]==old_result['formula'][key]
    phase=query['phase_ns']
    assert set(phase)=={'target_residual_generation_ns','formula_construction_ns',
                        'formula_serialization_ns','solver_search_ns',
                        'terminal_parse_and_model_decode_ns'}
    assert all(value>=0 for value in phase.values())
    assert sum(phase.values())==query['target_dependent_attempt_ns']
    assert query['target_dependent_attempt_ns']<=600*10**9
    assert query['worker_count']==1
    assert query['solver_budget_seconds']<=590
    assert query['peak_combined_rss_bytes_sampled']<=protocol['combined_rss_cap_bytes']
    stdout_path=HERE/'solver.stdout.txt';stderr_path=HERE/'solver.stderr.txt'
    assert query['stdout_sha256']==sha(stdout_path)
    assert query['stderr_sha256']==sha(stderr_path)
    output=stdout_path.read_text(errors='replace')
    assert query['restart_rows']==sum(line.startswith('c rst') for line in output.splitlines())
    assert query['status_lines']==[line for line in output.splitlines() if line.startswith('s ')]
    if query['status']=='BOUNDED_UNKNOWN':
        assert query['stop_reason'] in ('TARGET_DEPENDENT_TIMEOUT',None)
        assert not query['decoded_model_saved']
        assert not any(line.startswith(('s SATISFIABLE','s UNSATISFIABLE'))
                       for line in output.splitlines())
    elif query['status']=='SAT_PENDING_GROUP_REPLAY':
        assert query['decoded_model_saved']
        assert (HERE/'decoded_model.json').exists()
    elif query['status']=='UNSAT':
        assert any(line.startswith('s UNSATISFIABLE') for line in output.splitlines())
    else:
        raise AssertionError(query['status'])
    receipt={'status':'PASS_N131_SAME_FORMULA_BATCH_QUERY_AUDIT',
             'solver_status':query['status'],'target_dependent_attempt_ns':query['target_dependent_attempt_ns'],
             'phase_sum_ns':sum(phase.values()),'formula_sha256':expected,
             'residual_count':len(query['residuals']),
             'restart_rows':query['restart_rows'],
             'peak_combined_rss_bytes_sampled':query['peak_combined_rss_bytes_sampled'],
             'protocol_sha256':sha(protocol_path),'preflight_sha256':sha(preflight_path),
             'query_sha256':sha(query_path),'source_sha256':sha(Path(__file__))}
    (HERE/'audit_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],query['status'],flush=True)


if __name__=='__main__':
    main()
