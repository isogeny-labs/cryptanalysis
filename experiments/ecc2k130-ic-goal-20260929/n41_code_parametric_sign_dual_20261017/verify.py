#!/usr/bin/env python3
"""Read-only terminal check of the frozen degree screen and replay."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
UPSTREAM = HERE.parent / 'n41_rr_pairwise_certificate_20261017'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((HERE / name).read_text())


def rank(values):
    basis = {}
    for value in values:
        while value:
            pivot = value.bit_length() - 1
            if pivot in basis:
                value ^= basis[pivot]
            else:
                basis[pivot] = value
                break
    return len(basis)


def verify():
    protocol, result = load('protocol.json'), load('result.json')
    audit_protocol, audit = load('audit_protocol.json'), load('audit_result.json')
    assert protocol['source_sha256'] == sha(UPSTREAM / 'result.json')
    assert protocol['script_sha256'] == sha(HERE / 'run.py')
    assert result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert result['source_sha256'] == protocol['source_sha256']
    assert result['status'] == 'PASS_CODE_PARAMETRIC_SIGN_DUAL_SCREEN'
    assert audit['status'] == 'PASS_PARAMETRIC_SIGN_DUAL_REPLAY'
    assert audit['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert audit['source_sha256'] == audit_protocol['source_sha256']
    assert audit_protocol['source_sha256']['script'] == sha(HERE / 'audit.py')
    assert audit_protocol['source_sha256']['producer_result'] == sha(HERE / 'result.json')
    assert audit_protocol['source_sha256']['upstream_sage_audit'] == sha(UPSTREAM / 'audit_result.json')
    assert audit_protocol['source_sha256']['upstream_terminal'] == sha(UPSTREAM / 'terminal.json')
    assert json.loads((UPSTREAM / 'audit_result.json').read_text())['status'] == \
        'PASS_INDEPENDENT_N41_PAIRWISE_DETERMINANT_RANK_AUDIT'
    assert json.loads((UPSTREAM / 'terminal.json').read_text())['status'] == \
        'PASS_N41_RR_CERTIFICATE_COVERAGE_TERMINAL_AUDIT'
    fullroot = json.loads((UPSTREAM / 'fullroot_result.json').read_text())
    assert fullroot['status'] == 'COMPLETE_N41_BOTH_ROOTS_CERTIFICATE_CENSUS'
    assert [(row['mask'], row.get('root1_zero_signs', [])) for row in fullroot['rows']
            if row.get('root1_zero_signs')] == [(6, [15])]
    charts = json.loads((UPSTREAM / 'result.json').read_text())['charts']
    codes = [chart['mask'] for chart in charts]
    assert len(codes) == len(set(codes)) == 35
    ranks = []
    for degree, row in enumerate(result['results']):
        assert row['degree'] == degree
        monoms = row['monomials']
        ranks.append(rank([sum((code & mask == mask) << i
                               for i, mask in enumerate(monoms)) for code in codes]))
    assert ranks == [1, 8, 29, 35]
    assert [r['status'] for r in result['results']] == ['INCONSISTENT']*3 + ['SAT']
    assert [len(r['conflict_labels']) for r in result['results'][:3]] == [18, 54, 235]
    assert result['results'][3]['rank'] == 1225
    assert len(result['results'][3]['solution_blocks']) == 93
    assert audit['rows'][3]['coefficient_checks'] == 2240
    assert audit['rows'][3]['sign_value_checks'] == 2240
    for stderr in ('run.stderr', 'audit.stderr', 'lean.stderr'):
        assert not (HERE / stderr).read_bytes()
    lean = (HERE / 'lean.stdout').read_text()
    for theorem in ('map_xorRows', 'odd_dependency_excludes_dual'):
        assert f"'ParametricDual.{theorem}' depends on axioms:" in lean
    for banned in ('sorry', 'admit', 'sorryAx'):
        assert banned not in (HERE / 'ParametricDual.lean').read_text()
    print('PASS_FROZEN_CODE_PARAMETRIC_SIGN_DUAL', 'code_monomial_ranks', ranks)


if __name__ == '__main__':
    verify()
