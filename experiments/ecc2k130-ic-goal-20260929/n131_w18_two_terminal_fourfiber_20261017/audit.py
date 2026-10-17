"""Read-only full-cost and source audit of four-fiber public query."""
import hashlib
import json
import gzip
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
PRIOR=ROOT/'n131_w18_two_terminal_batch_residual_20261017/query_v2'
COVERAGE=ROOT/'n131_w18_two_terminal_coverage_20261015/count_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archived_xcnf(path):
    digest=hashlib.sha256(); size=0
    with gzip.open(path,'rb') as stream:
        while chunk:=stream.read(1024*1024):
            digest.update(chunk); size+=len(chunk)
    return digest.hexdigest(),size


def main():
    protocol_path=HERE/'protocol.json';query_path=HERE/'query_result.json'
    protocol=json.loads(protocol_path.read_text())
    query=json.loads(query_path.read_text())
    control=json.loads((HERE/'control_result.json').read_text())
    n41=json.loads((HERE/'n41_control_result.json').read_text())
    sage_control=json.loads((HERE/'control_sage_audit_result.json').read_text())
    sage_public=json.loads((HERE/'public_sage_audit_result.json').read_text())
    coverage=json.loads(COVERAGE.read_text())
    prior=json.loads((PRIOR/'query_result.json').read_text())
    assert protocol['status']=='FROZEN_FOURFIBER_TWO_TERMINAL_BEFORE_QUERY'
    assert protocol['candidate_id'] is None
    for name,path in {'terminal':HERE/'terminal.py','preparer':HERE/'prepare.py',
                      'batch':HERE/'batch.py','pool':HERE/'pool.json',
                      'control_fixture':HERE/'control_fixture.json',
                      'n41_control':HERE/'n41_control.py',
                      'n41_control_result':HERE/'n41_control_result.json',
                      'sage_runtime':HERE/'sage_runtime_info.json',
                      'prior_batch_verification':ROOT/'n131_w18_two_terminal_batch_residual_20261017/verification.json'}.items():
        assert protocol['source_sha256'][name]==sha(path)
    assert n41['status']=='PASS_UNPINNED_N41_FOURFIBER_SELECTOR_CONTROL'
    assert [row['matches_unpinned_free_five'] for row in n41['raw_fibers']]==[True,False,False,False]
    assert sage_control['status']=='PASS_INDEPENDENT_SAGE_N131_FOURFIBER_CONTROL'
    assert sage_control['residual_rows_checked']==8320
    assert sage_public['status']=='PASS_INDEPENDENT_SAGE_N131_FOURFIBER_PUBLIC_RESIDUALS'
    assert sage_public['residual_rows_checked']==8320
    assert sage_public['source_sha256']['query']==sha(query_path)
    assert control['protocol_sha256']==query['protocol_sha256']==sha(protocol_path)
    assert control['assignment_check']=={'clauses':control['formula']['clauses'],
                                         'native_xor_rows':control['formula']['native_xor_rows']}
    assert query['curve_id']==protocol['curve_id']==prior['curve_id']
    assert query['workload_id']==protocol['workload_id']==prior['workload_id']
    assert query['public_target']==protocol['public_target']==prior['public_target']
    assert query['raw_preimage_indices']==protocol['raw_preimage_indices']==[0,1,2,3]
    assert query['raw_targets']==protocol['raw_preimages']
    assert query['raw_targets'][0]==prior['raw_target']
    assert len(query['residuals'])==len(control['residuals'])==8320
    assert query['active_joint_pair_terms']==control['active_joint_pair_terms']==8320
    assert query['forbidden_joint_choices']==control['forbidden_joint_choices']==224
    assert query['exceptional_raw_joint_choices']==control['exceptional_raw_joint_choices']==0
    for row,name in ((query,'ordinary'),(control,'control')):
        archive=HERE/f'{name}.xcnf.gz'
        assert archived_xcnf(archive)==(row['formula']['xcnf_sha256'],row['formula']['xcnf_bytes'])
    for key in ('variables','and_gates','clauses','native_xor_rows'):
        assert query['formula'][key]==control['formula'][key]
    phase=query['phase_ns']
    assert set(phase)=={'target_residual_generation_ns','formula_construction_ns',
                        'formula_serialization_ns','solver_search_ns',
                        'terminal_parse_and_model_decode_ns'}
    assert all(value>=0 for value in phase.values())
    assert sum(phase.values())==query['target_dependent_attempt_ns']
    assert query['target_dependent_cap_seconds']==protocol['target_dependent_cap_seconds']==600
    assert query['worker_count']==protocol['worker_count']==1
    assert query['solver_budget_seconds']<=protocol['solver_cap_seconds']==590
    assert protocol['combined_rss_cap_bytes']==4294967296
    stdout_path=HERE/'solver.stdout.txt';stderr_path=HERE/'solver.stderr.txt'
    assert query['stdout_sha256']==sha(stdout_path)
    assert query['stderr_sha256']==sha(stderr_path)
    output=stdout_path.read_text(errors='replace')
    assert query['restart_rows']==sum(line.startswith('c rst') for line in output.splitlines())
    assert query['status_lines']==[line for line in output.splitlines() if line.startswith('s ')]
    if query['status']=='BOUNDED_UNKNOWN':
        assert query['stop_reason'] in ('TARGET_DEPENDENT_TIMEOUT',None)
        assert not query['decoded_model_saved']
        assert not query['status_lines']
    elif query['status']=='SAT_PENDING_GROUP_REPLAY':
        assert query['decoded_model_saved'] and (HERE/'decoded_model.json').exists()
    elif query['status']=='UNSAT':
        assert any(line.startswith('s UNSATISFIABLE') for line in output.splitlines())
    else:
        raise AssertionError(query['status'])
    prefix=next(row for row in coverage['prefixes'] if row['pool_edges_per_terminal']==12)
    assert prefix['uniform_raw_point_mean_upper_decimal']=='0.554579433463'
    receipt={'status':'PASS_FOURFIBER_N131_PUBLIC_QUERY_AUDIT',
             'solver_status':query['status'],'workload_id':query['workload_id'],
             'raw_preimages':4,'residuals':len(query['residuals']),
             'formula_sha256':query['formula']['xcnf_sha256'],
             'phase_ns':phase,'target_dependent_attempt_ns':query['target_dependent_attempt_ns'],
             'wall_cap_compliant':query['target_dependent_attempt_ns']<=600*10**9,
             'restart_rows':query['restart_rows'],
             'peak_combined_rss_bytes_sampled':query['peak_combined_rss_bytes_sampled'],
             'rss_cap_compliant':query['peak_combined_rss_bytes_sampled']<=4294967296,
             'source_mean_upper_one_raw':prefix['uniform_raw_point_mean_upper_decimal'],
             'source_mean_upper_four_raw':'2.218317733852',
             'archive_sha256':{'ordinary':sha(HERE/'ordinary.xcnf.gz'),
                               'control':sha(HERE/'control.xcnf.gz')},
             'sha256':{'script':sha(Path(__file__)),'protocol':sha(protocol_path),
                       'query':sha(query_path),'control':sha(HERE/'control_result.json'),
                       'sage_control':sha(HERE/'control_sage_audit_result.json'),
                       'sage_public':sha(HERE/'public_sage_audit_result.json')}}
    (HERE/'audit_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],query['status'],flush=True)


if __name__=='__main__':
    main()
