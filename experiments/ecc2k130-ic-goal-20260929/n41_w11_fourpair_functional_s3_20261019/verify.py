"""Read-only verification of the frozen functional-S3 experiment archive."""
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    build_protocol = load(HERE / 'build_protocol.json')
    query_protocol = load(HERE / 'query_protocol.json')
    build = load(HERE / 'build_result.json')
    query = load(HERE / 'query_result.json')
    chart = load(HERE / 'chart_result.json')
    all_witnesses = load(HERE / 'all_witnesses_result.json')
    assert build_protocol['status'] == 'FROZEN_BEFORE_FUNCTIONAL_S3_BUILD'
    assert query_protocol['status'] == 'FROZEN_BEFORE_FUNCTIONAL_S3_QUERY'
    assert build_protocol['worker_count'] == query_protocol['worker_count'] == 1
    assert build_protocol['rss_cap_bytes'] == query_protocol['rss_cap_bytes'] == 4294967296
    for protocol in [build_protocol, query_protocol]:
        for item in protocol['sources'].values():
            assert sha(item['path']) == item['sha256']
    assert sha(query_protocol['solver']) == query_protocol['solver_sha256']
    assert build['status'] == 'PASS_FUNCTIONAL_S3_FULL_ASSIGNMENT'
    assert build['protocol_sha256'] == sha(HERE / 'build_protocol.json')
    assert build['script_sha256'] == sha(HERE / 'build.py')
    assert build['formula_sha256'] == sha(HERE / 'functional_s3.xcnf')
    assert build['assignment_check']['clauses'] == build['counts']['clauses']
    assert build['assignment_check']['xor_rows'] == build['counts']['xor_rows']
    with (HERE / 'functional_s3.xcnf').open() as formula:
        header = formula.readline().split()
        assert header == ['p', 'cnf', str(build['counts']['variables']),
                          str(build['counts']['clauses'] + build['counts']['xor_rows'])]
        cnf = xor = 0
        for line in formula:
            if line.startswith('x '):
                xor += 1
            else:
                cnf += 1
        assert cnf == build['counts']['clauses']
        assert xor == build['counts']['xor_rows']
    assert chart['status'] == 'PASS_N41_W11_S3_CHART_AUDIT'
    assert chart['witness_count'] == 32
    assert chart['quadratic_charts'] + chart['linear_charts'] == 96
    assert chart['source_sha256'] == sha(ROOT / 'n41_w11_fourpair_public_20261019' / 'join4_input.tsv')
    assert chart['hits_sha256'] == sha(ROOT / 'n41_w11_fourpair_orbit_sat_20261019' / 'census' / 'census.stdout')
    assert all_witnesses['status'] == 'PASS_ALL_32_FUNCTIONAL_S3_ASSIGNMENTS'
    assert all_witnesses['chart_sha256'] == sha(HERE / 'chart_result.json')
    assert all_witnesses['source_sha256'] == chart['source_sha256']
    assert all_witnesses['script_sha256'] == sha(HERE / 'audit_all_witnesses.py')
    assert all_witnesses['formula_sha256'] == build['formula_sha256']
    assert len(all_witnesses['checks']) == 32
    assert all(row['assignment_check'] == build['assignment_check']
               for row in all_witnesses['checks'])
    prior = subprocess.run([sys.executable, str(ROOT / 'n41_w11_fourpair_orbit_sat_20261019' /
                                           'census' / 'archive_verify.py')],
                           capture_output=True, text=True, check=True)
    assert load_line(prior.stdout)['status'] == 'PASS_ARCHIVE_VERIFICATION'
    lean = (HERE / 'lean.stdout').read_text()
    assert not (HERE / 'lean.stderr').read_text()
    assert 'error:' not in lean and 'sorryAx' not in lean
    for theorem in ['quadratic_branch_sound', 'quadratic_branch_complete',
                    'linear_branch_sound', 'linear_branch_complete']:
        assert f"'FunctionalS3.{theorem}' depends on axioms: [propext, Classical.choice, Quot.sound]" in lean
    assert query['protocol_sha256'] == sha(HERE / 'query_protocol.json')
    assert query['runner_sha256'] == sha(HERE / 'run_solver.py')
    assert query['sampled_peak_combined_rss_bytes'] <= 4294967296
    assert query['wall_seconds'] <= 591
    stdout = HERE / 'solver.stdout'
    if not stdout.exists():
        stdout = HERE / 'solver.stdout.gz'
        with gzip.open(stdout, 'rb') as stream:
            assert hashlib.sha256(stream.read()).hexdigest() == query['stdout_sha256']
    else:
        assert sha(stdout) == query['stdout_sha256']
    assert sha(HERE / 'solver.stderr') == query['stderr_sha256']
    assert query['status'] == 'WALL_CAP'
    assert query['stop_reason'] == 'WALL_CAP'
    assert not query['terminal_sat_line'] and not query['terminal_unsat_line']
    print(json.dumps({'status': 'PASS_ARCHIVE_VERIFICATION', 'candidate_id': None,
                      'witness_count': 32, 'query': query['status']}, sort_keys=True))


def load_line(text):
    return json.loads(text.strip().splitlines()[-1])


if __name__ == '__main__':
    main()
