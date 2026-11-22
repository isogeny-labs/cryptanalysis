"""Check complete frozen quartic-block result against prior exact scan."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
cfg = json.loads((HERE / 'full600_protocol.json').read_text())
result = json.loads((HERE / 'full600_result.json').read_text())
prior = json.loads((ROOT / cfg['target_rows']).read_text())
assert result['protocol_sha256'] == hashlib.sha256((HERE / 'full600_protocol.json').read_bytes()).hexdigest()
for name, digest in cfg['sources'].items():
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
assert result['candidate_id'] is None and result['curve_id'] == cfg['curve_id']
assert result['source_codes'] == 281
assert result['source_product_space_dimension'] == 10
assert result['source_product_vanishing_degree'] == 1024
assert result['source_product_vanishing_terms'] <= 11
assert result['block_free_code_bits'] == 3
assert len(result['rows']) == cfg['target_count'] == 25
for row, old in zip(result['rows'], prior['rows']):
    assert row['name'] == old['name'] and row['target_point'] == old['target_point']
    assert row['prior_exact_product_hits'] == old['exact_product_subspace_hits']
    assert row['quartic_count'] == 281 and row['block_count'] == 109
    assert sum(row['gcd_degree_histogram'].values()) == 109
    assert row['rejected_blocks'] == row['gcd_degree_histogram'].get('0', 0)
    assert 109-row['rejected_blocks'] == len(row['retained_prefixes'])
    assert row['quartic_seconds'] > 0 and row['block_product_and_gcd_seconds'] > 0
    assert row['query_seconds_including_audit'] >= row['quartic_seconds'] + row['block_product_and_gcd_seconds']
    assert len(set(row['direct_root_audit_products'])) == 4
    if row['name'] == 'positive_residual':
        assert 253 >> 3 in row['retained_prefixes']
        assert row['rejected_blocks'] == 108
    else:
        assert old['exact_product_subspace_hits'] == 0
        assert row['rejected_blocks'] == 109
assert 'sorryAx' not in (HERE / 'lean_check.log').read_text()
receipt = {'status': 'PASS_N41_W11_QUARTIC_BLOCK_GCD_PANEL',
           'candidate_id': None, 'query_count': len(result['rows']),
           'positive_retained': True, 'ordinary_all_blocks_rejected': 24,
           'source_hashes': cfg['sources'],
           'result_sha256': hashlib.sha256((HERE / 'full600_result.json').read_bytes()).hexdigest(),
           'protocol_sha256': result['protocol_sha256'],
           'scope': 'hashes, row accounting, exact-scan agreement; direct roots and arithmetic are checked in Sage producer'}
(HERE / 'verification_result.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
print(json.dumps({'status': receipt['status'], 'query_count': len(result['rows'])}, sort_keys=True))
