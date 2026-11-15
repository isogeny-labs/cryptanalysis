"""Read-only checks of the frozen adjacent-image base screen."""

import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def main():
    p = read('protocol.json')
    a = read('audit_protocol.json')
    c = read('census_result.json')
    s = read('audit_result.json')
    source = Path(p['source_receipt'])
    eigen_path = HERE.parent / 'n131_w18_linked_tenpair_public_20261017/lambda_sage_result.json'
    eigen = json.loads(eigen_path.read_text())
    assert p['status'] == 'FROZEN_BEFORE_CENSUS'
    assert a['status'] == 'FROZEN_BEFORE_AUDIT'
    assert a['runtime_info_sha256'] == p['runtime_info_sha256']
    assert sha(source) == p['source_receipt_sha256'] == a['source_receipt_sha256']
    assert sha(eigen_path) == p['eigen_receipt_sha256']
    assert eigen['status'] == 'PASS_ACTUAL_N131_FROBENIUS_EIGENVALUE'
    assert eigen['lambda'] == p['frobenius_eigenvalue']
    assert sha(HERE / 'census.py') == p['census_source_sha256']
    assert sha(HERE / 'audit_sage.py') == a['auditor_source_sha256']
    assert sha(HERE / 'sage_runtime_info.json') == p['runtime_info_sha256']
    assert sha(HERE / 'census_result.json') == a['census_result_sha256']
    assert c['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert s['protocol_sha256'] == sha(HERE / 'audit_protocol.json')
    assert c['status'] == 'PASS_EXACT_ORBIT_CENSUS'
    assert s['status'] == 'PASS_ALL_REPRESENTATIVES'
    assert s['representatives_checked'] == 4134 and s['subgroup_scalar_checks'] == 8
    assert s['image_x_digest'] == c['representative_image_x_sha256']
    assert c['original_x_count'] == c['image_x_count'] == 4134*131
    assert c['x_overlap_count'] == 0
    assert c['union_point_count'] == 2166216
    assert c['union_independent_log_unknowns_upper_bound'] == 4134
    assert c['endomorphism_scalar_mod_r'] == (
        1 + int(p['frobenius_eigenvalue'])) % int(p['subgroup_order'])
    assert c['wall_seconds'] < p['wall_cap_seconds']
    assert s['wall_seconds'] < a['wall_cap_seconds']
    assert c['peak_rss_bytes'] < p['rss_cap_bytes']
    assert s['peak_rss_bytes'] < a['rss_cap_bytes']
    assert (HERE / 'census.stderr.txt').read_text() == ''
    assert (HERE / 'audit.stderr.txt').read_text() == ''
    for name, digest in p['codegen_source_sha256'].items():
        assert sha(ROOT / 'ecc2k130/codegen' / name) == digest
    getcontext().prec = 35
    r = Decimal(int(p['subgroup_order']))
    assert Decimal('0.13583') < Decimal(16536)**9 / r < Decimal('0.13584')
    assert Decimal('2246.13') < Decimal(16536)**10 / r < Decimal('2246.14')
    assert Decimal('149946445') < Decimal(8268)**12 / r < Decimal('149946446')
    print('PASS_ADJACENT_EXPANDED_BASE_SCREEN', c['union_point_count'])


if __name__ == '__main__':
    main()
