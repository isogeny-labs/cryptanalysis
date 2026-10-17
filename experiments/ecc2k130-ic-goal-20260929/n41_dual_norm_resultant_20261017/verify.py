"""Read-only integrity and outcome checks for the resultant experiment."""
import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
BASE=D.parent/'n41_dual_three_norm_public_20261017'


def read(name):
    return json.loads((D/name).read_text())


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def bound(name,digest):
    assert sha(D/name)==digest,(name,digest)


def main():
    p=read('protocol.json');b=read('build_result.json');br=read('build_receipt.json')
    qp=read('query_protocol.json');q=read('query_result.json')
    field=read('field_audit.json')
    archive=D.parent/'n41_sixpair_shared_target_20261017'/'join_audit_result.json'
    assert p['public_raw_target']==json.loads(archive.read_text())['raw_target']
    for name,key in [('build.py','producer_sha256'),('run_build.py','runner_sha256')]:
        bound(name,p[key])
    for path,digest in p['sources'].items():assert sha(Path(path))==digest,path
    bound('protocol.json',b['protocol_sha256'])
    bound('protocol.json',br['protocol_sha256'])
    bound('run_build.py',br['runner_sha256'])
    bound('sage_runtime_info.json',br['runtime_info_sha256'])
    bound('build_result.json',br['build_result_sha256'])
    for ext in ('stdout','stderr'):bound('build.'+ext,br[ext+'_sha256'])
    assert br['status']=='COMPLETE' and br['exit_code']==0
    assert br['monitor_degraded'] is True
    assert br['sampled_peak_combined_rss_bytes']==0
    assert b['status']=='N41_DUAL_NORM_RESULTANT_CONTROL_PASS'
    assert b['witness_assignment_check']=={'clauses':b['clauses'],
                                             'native_xor_rows':b['xor_rows']}
    bound('public.xcnf',b['formula_sha256'])
    assert (D/'public.xcnf').stat().st_size==b['formula_bytes']
    with (D/'public.xcnf').open() as f:header=f.readline().strip()
    assert header==f"p cnf {b['variables']} {b['clauses']+b['xor_rows']}"
    bound('public.xcnf',qp['formula_sha256'])
    bound('build_result.json',qp['build_result_sha256'])
    bound('build_receipt.json',qp['build_receipt_sha256'])
    bound('run_query.py',qp['producer_sha256'])
    assert sha(Path(qp['solver_path']))==qp['solver_sha256']
    bound('query_protocol.json',q['protocol_sha256'])
    for ext in ('stdout','stderr'):bound('solver.'+ext,q[ext+'_sha256'])
    output=(D/'solver.stdout').read_text()
    assert 'Reading file' in output and 'c Parsing time:' in output
    assert q['restart_lines']==sum(x.startswith('c rst ') for x in output.splitlines())>0
    assert q['terminal_lines']==[x for x in output.splitlines() if x.startswith('s ')]==[]
    assert q['status']=='BOUNDED_UNKNOWN' and q['stop_reason']=='PARENT_WALL_CAP'
    assert q['exit_code']==-15 and q['monitor_degraded'] is False
    assert q['sampled_peak_combined_rss_bytes']<qp['rss_cap_bytes']
    assert q['wall_s']>=qp['parent_cap_s']
    assert field['status']=='PASS' and field['archive_sha256']==sha(archive)
    assert field['s3_quadratic_lead_root']!=0 and field['resultant_value']==0
    assert field['right_norm_values'][0]==0
    assert (D/'lean_build.exit').read_text().strip()=='0'
    stdout=(D/'lean_build.stdout').read_text()
    for theorem in ('s3AsQuadratic','normalizeQuadratic','commonRootImpliesNormZero'):
        assert "QuadraticNorm."+theorem in stdout
    old=json.loads((BASE/'build_result.json').read_text())
    assert old['status']=='N41_DUAL_NORM_PUBLIC_CIRCUIT_CONTROL_PASS'
    summary={'status':'PASS','query_status':q['status'],
             'and_gate_ratio':b['and_gates']/old['and_gates'],
             'formula_byte_ratio':b['formula_bytes']/old['formula_bytes'],
             'resultant_and_gates':b['and_gates'],
             'baseline_and_gates':old['and_gates'],
             'query_wall_s':q['wall_s'],
             'query_restart_lines':q['restart_lines'],
             'build_monitor_degraded':br['monitor_degraded']}
    (D/'verification.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary,sort_keys=True))


if __name__=='__main__':main()
