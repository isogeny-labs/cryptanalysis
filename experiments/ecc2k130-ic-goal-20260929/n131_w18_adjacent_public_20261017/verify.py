"""Read-only terminal verification from the exact archived XCNF streams."""
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
    assert archive['status'] == 'PASS_ADJACENT_N131_ARCHIVE_REPLAY'
    assert archive['protocol_sha256'] == sha(HERE / 'archive_protocol.json')
    for name in ('control', 'ordinary'):
        assert sha(HERE / f'{name}.xcnf.gz') == archive['formulas'][name]['archive_sha256']
        assert inspect_archive(HERE / f'{name}.xcnf.gz') == {
            key: value for key, value in archive['formulas'][name].items()
            if key != 'archive_sha256'}
    protocol, control, query = load('protocol.json'), load('control_result.json'), load('query_result.json')
    source_control, census = load('control_sage_audit.json'), load('source_census.json')
    audit_protocol, audit = load('audit_protocol.json'), load('audit_result.json')
    assert protocol['status'] == 'FROZEN_N131_ADJACENT_TENPAIR_BEFORE_CONTROL_AND_QUERY'
    assert protocol['source_sha256']['runner'] == sha(HERE / 'adjacent.py')
    assert control['status'] == 'PASS_ADJACENT_TENPAIR_CONSTRUCTED_XCNF'
    assert source_control['status'] == 'PASS_ADJACENT_TENPAIR_SAGE_CONTROL'
    assert census['status'] == 'PASS_ADJACENT_SOURCE_DISTINCT_CENSUS'
    assert census['union_unique'] == 132764 and census['cross_intersection'] == 0
    assert census['script_sha256'] == sha(HERE / 'source_census.py')
    assert audit_protocol['status'] == 'FROZEN_ADJACENT_N131_TERMINAL_AUDIT'
    assert audit['status'] == 'PASS_ADJACENT_N131_QUERY_AUDIT'
    assert audit['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert query['status'] == archive['query_status'] == 'BOUNDED_UNKNOWN'
    assert query['stop_reason'] == 'TOTAL_QUERY_TIMEOUT' and not query['decoded_model_saved']
    assert sum(query['phase_ns'].values()) == query['target_dependent_attempt_ns']
    assert 600_000_000_000 <= query['target_dependent_attempt_ns'] < 600_300_000_000
    assert query['worker_count'] == protocol['worker_count'] == 1
    assert query['peak_combined_rss_bytes_sampled'] < protocol['combined_rss_cap_bytes']
    assert sha(HERE / 'solver.stdout.txt') == query['stdout_sha256']
    assert sha(HERE / 'solver.stderr.txt') == query['stderr_sha256']
    assert not (HERE / 'solver.stderr.txt').read_bytes()
    assert not query['status_lines']
    for filename in ('prepare_v2.stderr', 'control_sage.stderr', 'freeze.stderr',
                     'control.stderr', 'query.stderr', 'audit.stderr',
                     'archive_audit.stderr', 'lean.stderr', 'source_census.stderr'):
        assert not (HERE / filename).read_bytes(), filename
    lean = (HERE / 'lean.stdout').read_text()
    for declaration in ('plus_branch', 'minus_branch', 'composed_denominator_mod_two'):
        assert f"'AdjacentLeaf.{declaration}' depends on axioms:" in lean
    for marker in ('sorry', 'admit', 'sorryAx'):
        assert marker not in (HERE / 'AdjacentLeaf.lean').read_text()
    print('PASS_ADJACENT_N131_TERMINAL_REPLAY',
          query['target_dependent_attempt_ns'], census['union_unique'])


if __name__ == '__main__':
    verify()
