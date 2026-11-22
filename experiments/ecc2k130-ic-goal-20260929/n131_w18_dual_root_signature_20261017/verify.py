"""Check immutable W18 dual-signature receipts and proof output."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / 'n131_w18_linked_signature_prefix_20261012'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((BASE / name).read_text())


def check():
    census_protocol, census = read('protocol.json'), read('result.json')
    inter_protocol, inter = read('intersection_protocol.json'), read('intersection_result.json')
    audit_protocol, audit = read('audit_protocol.json'), read('audit_result.json')
    d6_protocol, d6 = read('degree6_protocol.json'), read('degree6_result.json')
    d6low_protocol, d6low = read('degree6_low_protocol.json'), read('degree6_low_result.json')
    assert census_protocol['source_sha256'] == {
        'script': digest(BASE / 'census.py'), 'table': digest(SOURCE / 'rows.tsv.gz'),
        'prior_audit': digest(SOURCE / 'table_audit_result.json')}
    assert census['protocol_sha256'] == digest(BASE / 'protocol.json')
    assert census['source_sha256'] == census_protocol['source_sha256']
    assert census['status'] == 'PASS_W18_DUAL_ROOT_SIGNATURE_CENSUS'
    assert (census['source_code_count'], census['delta_rank'], census['dual_dimension'],
            census['unique_full_signatures'], census['signature_collision_count']) == (
            33191, 17, 114, 33191, 0)
    assert len(census['dual_masks']) == 114
    assert inter_protocol['source_sha256'] == {
        'script': digest(BASE / 'intersect.py'), 'census': digest(BASE / 'census.py'),
        'census_result': digest(BASE / 'result.json'),
        'table': digest(SOURCE / 'rows.tsv.gz')}
    assert inter['protocol_sha256'] == digest(BASE / 'intersection_protocol.json')
    assert inter['source_sha256'] == inter_protocol['source_sha256']
    assert inter['status'] == 'PASS_W18_DUAL_ANF_INTERSECTION'
    assert inter['signature_rank'] == 113
    assert [(s['degree'], s['feature_rank'], s['intersection_dimension'])
            for s in inter['screens']] == [
                (0, 1, 0), (1, 18, 0), (2, 154, 0), (3, 834, 0),
                (4, 3214, 0), (5, 9402, 0)]
    assert audit_protocol['table_sha256'] == digest(SOURCE / 'rows.tsv.gz')
    assert audit_protocol['script_sha256'] == digest(BASE / 'audit.py')
    assert audit_protocol['census_sha256'] == digest(BASE / 'result.json')
    assert audit_protocol['intersection_sha256'] == digest(BASE / 'intersection_result.json')
    assert audit['protocol_sha256'] == digest(BASE / 'audit_protocol.json')
    assert audit['status'] == 'PASS_INDEPENDENT_LOW_PIVOT_REPLAY'
    assert (audit['source_rows'], audit['root_difference_rank'], audit['dual_rank'],
            audit['output_span_rank'], audit['signature_rank']) == (33191, 17, 114, 130, 113)
    assert audit['global_zero_mask_hex'] == '0x5f90004b7c0f8784ac98a13264581e5b9'
    assert audit['global_zero_mask_weight'] == 57
    assert audit['screens'] == [{
        'degree': s['degree'], 'feature_count': s['feature_count'],
        'feature_rank': s['feature_rank'],
        'quotient_signature_rank': s['quotient_signature_rank'],
        'intersection_dimension': s['intersection_dimension']}
        for s in inter['screens']]
    assert d6_protocol['source_sha256'] == {
        'script': digest(BASE / 'degree6.py'), 'table': digest(SOURCE / 'rows.tsv.gz'),
        'census_result': digest(BASE / 'result.json'),
        'intersection_result': digest(BASE / 'intersection_result.json'),
        'independent_audit': digest(BASE / 'audit_result.json')}
    assert d6['protocol_sha256'] == digest(BASE / 'degree6_protocol.json')
    assert (d6['status'], d6['source_rows'], d6['feature_count'], d6['feature_rank'],
            d6['signature_rank'], d6['quotient_signature_rank'],
            d6['intersection_dimension']) == (
            'PASS_DEGREE6_EXTENSION', 33191, 21778, 21778, 113, 113, 0)
    assert d6low_protocol['source_sha256'] == {
        'script': digest(BASE / 'degree6_low.py'),
        'audit_script': digest(BASE / 'audit.py'),
        'table': digest(SOURCE / 'rows.tsv.gz'),
        'degree6_result': digest(BASE / 'degree6_result.json')}
    assert d6low['protocol_sha256'] == digest(BASE / 'degree6_low_protocol.json')
    assert d6low['status'] == 'PASS_INDEPENDENT_DEGREE6_LOW_PIVOT'
    for key in ('source_rows', 'feature_count', 'feature_rank', 'signature_rank',
                'quotient_signature_rank', 'intersection_dimension'):
        assert d6low[key] == d6[key]
    assert read('attempt1/protocol.json')['status'].startswith('FROZEN_')
    assert read('attempt2/protocol.json')['status'].startswith('FROZEN_')
    for attempt in ('attempt1', 'attempt2'):
        assert (BASE / attempt / 'FAILURE.md').exists()
        assert (BASE / attempt / 'run.stderr').stat().st_size > 0
    assert (SOURCE / 'fast_audit_result.json').exists()
    source_audit = json.loads((SOURCE / 'fast_audit_result.json').read_text())
    assert source_audit['status'] == 'PASS_INDEPENDENT_SAGE_ALL_W18_LINKED_ADDITION_FORMULAS'
    assert (source_audit['source_codes'], source_audit['pair_output_roots'],
            source_audit['signed_additions_replayed']) == (33191, 66382, 265528)
    assert 'leanprover/lean4:v4.34.1' in (BASE / 'lean-toolchain').read_text()
    assert (BASE / 'lean.stderr').stat().st_size == 0
    lean = (BASE / 'lean.stdout').read_text()
    assert 'paired_roots_agree' in lean and 'zero_functional_on_pair' in lean
    assert lean.count('depends on axioms: [propext]') == 2
    for name in ('run', 'intersection', 'audit', 'degree6', 'degree6_low'):
        assert (BASE / f'{name}.stderr').stat().st_size == 0
        assert (BASE / f'{name}.stdout').stat().st_size > 0
    print('PASS_W18_DUAL_SIGNATURE_RECEIPT_AUDIT')
    print('all_root_sage_audit_sha256', digest(SOURCE / 'fast_audit_result.json'))


if __name__ == '__main__':
    check()
