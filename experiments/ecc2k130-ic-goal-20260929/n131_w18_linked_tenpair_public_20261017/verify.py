#!/usr/bin/env python3
"""Read-only final verifier for the linked N131 bounded attempt."""
import hashlib
import json
from pathlib import Path

from audit_archive import inspect_archive, paths

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def verify():
    archive_protocol, archive = load('archive_protocol.json'), load('archive_result.json')
    assert archive_protocol['source_sha256'] == {name: sha(path) for name, path in paths().items()}
    assert archive['status'] == 'PASS_LINKED_N131_ARCHIVE_REPLAY'
    assert archive['protocol_sha256'] == sha(HERE / 'archive_protocol.json')
    for name in ('control', 'ordinary'):
        assert inspect_archive(HERE / f'{name}.xcnf.gz') == {
            key: value for key, value in archive['formulas'][name].items()
            if key != 'archive_sha256'}
    protocol, control, query = load('protocol.json'), load('control_result.json'), load('query_result.json')
    source_control, lambda_control = load('control_sage_audit.json'), load('lambda_sage_result.json')
    assert protocol['status'] == 'FROZEN_N131_LINKED_TENPAIR_BEFORE_CONTROL_AND_QUERY'
    assert control['status'] == 'PASS_LINKED_TENPAIR_CONSTRUCTED_XCNF'
    assert source_control['status'] == 'PASS_LINKED_TENPAIR_SAGE_CONTROL'
    assert lambda_control['status'] == 'PASS_ACTUAL_N131_FROBENIUS_EIGENVALUE'
    assert query['status'] == archive['query_status'] == 'BOUNDED_UNKNOWN'
    assert query['stop_reason'] == 'TOTAL_QUERY_TIMEOUT' and not query['decoded_model_saved']
    assert sum(query['phase_ns'].values()) == query['target_dependent_attempt_ns']
    assert query['peak_combined_rss_bytes_sampled'] < protocol['combined_rss_cap_bytes']
    assert sha(HERE / 'solver.stdout.txt') == query['stdout_sha256']
    assert sha(HERE / 'solver.stderr.txt') == query['stderr_sha256']
    assert not (HERE / 'solver.stderr.txt').read_bytes()
    assert not query['status_lines']
    for stderr in ('control.stderr', 'query.stderr', 'sage_audit.stderr',
                   'lambda_sage.stderr', 'link_coefficients.stderr',
                   'archive_audit.stderr', 'audit.stderr', 'lean.stderr'):
        assert not (HERE / stderr).read_bytes()
    lean = (HERE / 'lean.stdout').read_text()
    for declaration in ('coefficient_factor', 'same_sign', 'opposite_sign'):
        assert f"'LinkedSign.{declaration}' depends on axioms: [propext]" in lean
    for marker in ('sorry', 'admit', 'sorryAx'):
        assert marker not in (HERE / 'LinkedSign.lean').read_text()
    print('PASS_LINKED_N131_FROZEN_TERMINAL_REPLAY')


if __name__ == '__main__':
    verify()
