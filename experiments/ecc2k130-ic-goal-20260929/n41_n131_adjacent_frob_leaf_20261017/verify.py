"""Read-only terminal check of this experiment's frozen receipts."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
N131_SOURCE = ROOT / 'n131_projected_root_lookup_screen_20261015'


def read(name):
    return json.loads((HERE / name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hashes(expected, paths):
    assert set(expected) == set(paths)
    for key, path in paths.items():
        assert sha(path) == expected[key], (key, path)


def main():
    prepared = read('prepare_result.json')
    assert prepared['status'] == 'FROZEN_ADJACENT_SOURCE_DERIVATION'
    check_hashes(prepared['output_sha256'], {
        name: HERE / name for name in prepared['output_sha256']})
    protocol = read('protocol.json')
    assert protocol['status'] == 'FROZEN_N41_ADJACENT_PUBLIC_JOIN'
    assert protocol['worker_count'] == 1 and protocol['wall_cap_seconds'] == 180
    assert protocol['independent_edges'] == 9 and protocol['source_pair_slots'] == 10
    for key, filename in [('input', 'adjacent_input.tsv'),
                          ('native_binary', 'adjacent_join'),
                          ('native_source', 'adjacent_join.cpp'),
                          ('runner', 'run.py'),
                          ('prepare_receipt', 'prepare_result.json'),
                          ('sage_runtime', 'sage_runtime_info.json')]:
        assert sha(HERE / filename) == protocol['source_sha256'][key]
    receipt = read('receipt.json')
    assert receipt['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert receipt['status'] == 'HIT_PENDING_INDEPENDENT_REPLAY'
    assert receipt['exit_code'] == 0 and receipt['worker_count'] == 1
    assert receipt['peak_combined_rss_bytes_sampled'] < protocol['rss_cap_bytes']
    assert receipt['runner_wall_ns'] < protocol['wall_cap_seconds']*10**9
    assert sha(HERE / 'stdout.log') == receipt['stdout_sha256']
    assert sha(HERE / 'stderr.log') == receipt['stderr_sha256']
    assert receipt['hit_line'] in (HERE / 'stdout.log').read_text().splitlines()
    audit_protocol = read('audit_protocol.json')
    assert audit_protocol['status'] == 'FROZEN_N41_ADJACENT_SAGE_REPLAY'
    for key, filename in [('audit_source', 'audit_sage.py'),
                          ('input', 'adjacent_input.tsv'),
                          ('native_receipt', 'receipt.json'),
                          ('sage_runtime', 'sage_runtime_info.json'),
                          ('stdout', 'stdout.log')]:
        assert sha(HERE / filename) == audit_protocol['sha256'][key]
    audit = read('audit_result.json')
    assert audit['status'] == 'PASS_INDEPENDENT_N41_LINKED_FROBENIUS_PUBLIC_RELATION'
    assert audit['linked_frobenius_exponent'] == 1
    assert audit['source_edges_distinct'] == audit['source_pairs_free'] == 9
    assert audit['rank_before_with_prior_six_nine_ten'] == 3
    assert audit['rank_after_with_linked_row'] == 4
    assert audit['folded_columns_nonzero'] == len(audit['relation_row']) == 18
    assert audit['term_count'] == len(audit['source_terms']) == 20
    n131_protocol = read('n131_protocol.json')
    n131_result = read('n131_result.json')
    assert n131_protocol['status'] == 'FROZEN_ADJACENT_W18_ROOT_SOURCE'
    check_hashes(n131_protocol['source_sha256'], {
        'script': HERE / 'n131_source_sage.py',
        'raw_root_table': N131_SOURCE / 'canonical_table.bin',
        'raw_root_receipt': N131_SOURCE / 'prepare_result.json',
        'n41_sage_audit': HERE / 'audit_result.json',
        'runtime': HERE / 'n131_sage_runtime_info.json'})
    assert n131_result['protocol_sha256'] == sha(HERE / 'n131_protocol.json')
    assert n131_result['status'] == 'PASS_N131_ADJACENT_ROOT_MAP'
    assert n131_result['source_sha256'] == n131_protocol['source_sha256']
    assert n131_result['raw_roots'] == 66382
    assert n131_result['independent_group_checks'] == 512
    assert sum(n131_result['phase_ns'].values()) == n131_result['total_ns']
    assert sha(HERE / 'adjacent_roots.bin') == n131_result['output_sha256']
    assert (HERE / 'adjacent_roots.bin').stat().st_size == n131_result['output_bytes']
    field = read('n131_verify_result.json')
    assert field['status'] == 'PASS_INDEPENDENT_FULL_ADJACENT_ROOT_TABLE'
    assert field['root_count'] == 66382 and field['field_equations_checked'] == 132764
    assert field['source_sha256'] == n131_protocol['source_sha256']['raw_root_table']
    assert field['mapped_sha256'] == n131_result['output_sha256']
    assert field['verifier_sha256'] == sha(HERE / 'verify_n131.py')
    for filename in ['audit.stderr', 'run.stderr', 'n131_run.stderr',
                     'n131_verify.stderr', 'lean.stderr']:
        assert (HERE / filename).stat().st_size == 0, filename
    lean = (HERE / 'lean.stdout').read_text()
    assert "'Adjacent.adjacent_polynomial_identity' depends on axioms:" in lean
    assert "'Adjacent.adjacent_parity' depends on axioms:" in lean
    assert 'sorryAx' not in lean and 'sorry' not in (HERE / 'Adjacent.lean').read_text()
    print('PASS_ADJACENT_TERMINAL_VERIFY', audit['folded_columns_nonzero'],
          n131_result['raw_roots'], field['field_equations_checked'])


if __name__ == '__main__':
    main()
