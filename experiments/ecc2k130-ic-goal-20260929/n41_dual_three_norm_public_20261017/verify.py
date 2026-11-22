"""Read-only hash and outcome audit of the frozen dual-norm experiment."""
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent


def read(name):
    return json.loads((D / name).read_text())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def bound(name, expected):
    actual = digest(D / name)
    assert actual == expected, (name, actual, expected)


def main():
    protocol = read('protocol.json')
    build = read('build_result.json')
    first = read('build_receipt.json')
    retry = read('build_retry_receipt.json')
    query_protocol = read('query_protocol.json')
    query = read('query_result.json')

    bound('build.py', protocol['producer_sha256'])
    for source, expected in protocol['sources'].items():
        assert digest(Path(source)) == expected, source
    bound('protocol.json', build['protocol_sha256'])
    bound('protocol.json', first['protocol_sha256'])
    bound('protocol.json', retry['protocol_sha256'])
    for receipt in (first, retry):
        for stream in ('stdout', 'stderr'):
            name = 'build' + ('_retry' if receipt is retry else '') + '.' + stream
            bound(name, receipt[stream + '_sha256'])
    assert first['status'] == 'PRODUCER_FAILURE' and first['exit_code'] == 1
    assert retry['status'] == 'COMPLETE' and retry['exit_code'] == 0
    bound('run_build.py', retry['runner_sha256'])
    bound('sage_runtime_info.json', retry['runtime_info_sha256'])
    bound('build_result.json', retry['build_result_sha256'])

    assert build['status'] == 'N41_DUAL_NORM_PUBLIC_CIRCUIT_CONTROL_PASS'
    assert build['witness_assignment_check'] == {
        'clauses': build['clauses'], 'native_xor_rows': build['xor_rows']}
    bound('public.xcnf', build['formula_sha256'])
    assert (D / 'public.xcnf').stat().st_size == build['formula_bytes']
    with (D / 'public.xcnf').open() as f:
        header = f.readline().strip()
    assert header == f"p cnf {build['variables']} {build['clauses'] + build['xor_rows']}"

    bound('run_query.py', query_protocol['producer_sha256'])
    bound('public.xcnf', query_protocol['formula_sha256'])
    bound('build_result.json', query_protocol['build_result_sha256'])
    bound('build_retry_receipt.json', query_protocol['build_receipt_sha256'])
    assert digest(Path(query_protocol['solver_path'])) == query_protocol['solver_sha256']
    assert query_protocol['public_raw_target'] == protocol['public_raw_target']
    assert query_protocol['candidate_id'] is None
    bound('query_protocol.json', query['protocol_sha256'])
    bound('solver.stdout', query['stdout_sha256'])
    bound('solver.stderr', query['stderr_sha256'])
    output = (D / 'solver.stdout').read_text()
    assert 'Reading file' in output and 'Using 0 matrices recovered' in output
    assert query['restart_lines'] == sum(line.startswith('c rst ') for line in output.splitlines())
    assert query['restart_lines'] > 0
    assert query['terminal_lines'] == [line.strip() for line in output.splitlines()
                                       if line.startswith('s ')] == []
    assert query['status'] == 'BOUNDED_UNKNOWN'
    assert query['stop_reason'] == 'PARENT_WALL_CAP'
    assert query['exit_code'] == -15 and not query['monitor_degraded']
    assert query['sampled_peak_combined_rss_bytes'] < query_protocol['rss_cap_bytes']
    assert query['wall_s'] >= query_protocol['parent_cap_s']
    archive = json.loads((D.parent / 'n41_sixpair_shared_target_20261017' /
                          'join_audit_result.json').read_text())
    assert archive['raw_target'] == protocol['public_raw_target']
    result = {
        'status': 'PASS', 'query_status': query['status'],
        'parsed_and_searched': True, 'restart_lines': query['restart_lines'],
        'wall_s': query['wall_s'],
        'sampled_peak_combined_rss_bytes': query['sampled_peak_combined_rss_bytes'],
        'checks': ['frozen_sources', 'first_failure_retained', 'checked_retry',
                   'formula_header_and_control', 'public_target',
                   'solver_binary_and_raw_logs', 'search_and_cap']}
    (D / 'verification.json').write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
