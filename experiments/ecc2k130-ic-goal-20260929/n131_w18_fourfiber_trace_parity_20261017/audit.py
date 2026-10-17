"""Read-only custody, formula, parity, and full-cost audit of public attempt."""
import gzip
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
PRIOR=HERE.parent/'n131_w18_two_terminal_fourfiber_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archived(path):
    digest=hashlib.sha256();size=0
    with gzip.open(path,'rb') as stream:
        while chunk:=stream.read(1024*1024):
            digest.update(chunk);size+=len(chunk)
    return digest.hexdigest(),size


def main():
    ppath=HERE/'protocol.json';qpath=HERE/'query_result.json'
    protocol=json.loads(ppath.read_text())
    query=json.loads(qpath.read_text())
    control=json.loads((HERE/'control_result.json').read_text())
    preflight=json.loads((HERE/'trace_audit_result.json').read_text())
    table=json.loads((HERE/'trace_table_audit_result.json').read_text())
    previous=json.loads((PRIOR/'query_result.json').read_text())
    assert protocol['status']=='FROZEN_FOURFIBER_TRACE_PARITY_BEFORE_QUERY'
    assert protocol['candidate_id'] is None
    import sys
    sys.path.insert(0,str(HERE))
    import terminal
    assert protocol['source_sha256']=={name:sha(path) for name,path in terminal.sources().items()}
    assert preflight['status']=='PASS_FOURFIBER_TRACE_PARITY_PREFLIGHT'
    assert preflight['public_rows_checked']==preflight['constructed_rows_checked']==8320
    assert preflight['source_sha256']['public']==sha(PRIOR/'query_result.json')
    assert table['status']=='PASS_INDEPENDENT_N131_TERMINAL_TRACE_TABLE'
    assert table['joint_states_checked']==2080
    assert table['sha256']['protocol']==sha(ppath)
    assert control['status']=='PASS_EXACT_N131_FOURFIBER_TRACE_PARITY_CONTROL'
    assert control['protocol_sha256']==query['protocol_sha256']==sha(ppath)
    assert control['assignment_check']=={'clauses':control['formula']['clauses'],
                                         'native_xor_rows':control['formula']['native_xor_rows']}
    assert query['curve_id']==protocol['curve_id']==previous['curve_id']
    assert query['workload_id']==protocol['workload_id']==previous['workload_id']
    assert query['public_target']==protocol['public_target']==previous['public_target']
    assert query['raw_targets']==protocol['raw_preimages']==previous['raw_targets']
    assert query['raw_target_trace_bits']==preflight['panels'][0]['raw_target_trace_bits']
    assert query['raw_target_trace_bits']==table['public_raw_target_trace_bits']
    assert query['trace_parity_literals']==control['trace_parity_literals']==40
    assert len(query['residuals'])==len(control['residuals'])==8320
    assert query['residuals']==previous['residuals']
    assert query['active_joint_pair_terms']==control['active_joint_pair_terms']==8320
    assert query['forbidden_joint_choices']==control['forbidden_joint_choices']==224
    assert query['exceptional_raw_joint_choices']==control['exceptional_raw_joint_choices']==0
    for row,name in ((query,'ordinary'),(control,'control')):
        assert archived(HERE/f'{name}.xcnf.gz')==(row['formula']['xcnf_sha256'],
                                                  row['formula']['xcnf_bytes'])
    for key in ('variables','clauses','native_xor_rows'):
        assert query['formula'][key]==control['formula'][key]
        assert query['formula'][key]==previous['formula'][key]+1
    assert query['formula']['and_gates']==control['formula']['and_gates']==previous['formula']['and_gates']
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
    stdout=HERE/'solver.stdout.txt';stderr=HERE/'solver.stderr.txt'
    assert query['stdout_sha256']==sha(stdout)
    assert query['stderr_sha256']==sha(stderr)
    lines=stdout.read_text(errors='replace').splitlines()
    assert query['restart_rows']==sum(line.startswith('c rst') for line in lines)
    assert query['status_lines']==[line for line in lines if line.startswith('s ')]
    if query['status']=='BOUNDED_UNKNOWN':
        assert not query['decoded_model_saved'] and not query['status_lines']
    elif query['status']=='SAT_PENDING_GROUP_REPLAY':
        assert query['decoded_model_saved'] and (HERE/'decoded_model.json').exists()
    elif query['status']=='UNSAT':
        assert any(line.startswith('s UNSATISFIABLE') for line in lines)
    else:
        raise AssertionError(query['status'])
    first=HERE/'attempt1'
    assert sha(first/'terminal.py')=='7ffb31ec5a6730b764b498b7bdb6aec2b7f0ffa894f99e7b4a34ab466f311c10'
    assert sha(first/'protocol.json')=='1b075ab647d8ab32173ec2e523895df4ac33be3870c08f3b29ba4d397de0c9be'
    assert archived(first/'control.xcnf.gz')[0]=='b2c05d25351b0d6c5b5bcc718434a97f8d684046dbc958cc7b72c1f53514c38e'
    receipt={'status':'PASS_FOURFIBER_TRACE_PARITY_PUBLIC_AUDIT',
             'solver_status':query['status'],'curve_id':query['curve_id'],
             'workload_id':query['workload_id'],
             'target_dependent_attempt_ns':query['target_dependent_attempt_ns'],
             'phase_ns':phase,'peak_combined_rss_bytes_sampled':query['peak_combined_rss_bytes_sampled'],
             'wall_cap_compliant':query['target_dependent_attempt_ns']<=600*10**9,
             'rss_cap_compliant':query['peak_combined_rss_bytes_sampled']<=4294967296,
             'formula_sha256':query['formula']['xcnf_sha256'],
             'archive_sha256':{'ordinary':sha(HERE/'ordinary.xcnf.gz'),
                               'control':sha(HERE/'control.xcnf.gz')},
             'sha256':{'script':sha(Path(__file__)),'protocol':sha(ppath),
                       'query':sha(qpath),'control':sha(HERE/'control_result.json'),
                       'preflight':sha(HERE/'trace_audit_result.json'),
                       'trace_table':sha(HERE/'trace_table_audit_result.json')}}
    (HERE/'audit_result.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(receipt['status'],query['status'],flush=True)


if __name__=='__main__':
    main()
