"""Replay archived N131 W23 pair samples through the implicit source law."""
import hashlib
import json
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
sys.path.insert(0, str(ROOT.parent / 'koblitz-polynomial-w-pair-20260925'))
from pair_oracle import Curve, Field, half_trace, trace

SAGE_AUDIT = ROOT / 'n131_w23_sixpair_density_20261016' / 'sage_audit_result.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = json.loads((D / 'n131_transfer_protocol.json').read_text())
    assert protocol['producer_sha256'] == sha(Path(__file__))
    assert protocol['archived_sage_audit_sha256'] == sha(SAGE_AUDIT)
    archived = json.loads(SAGE_AUDIT.read_text())
    assert archived['status'] == 'PASS_SAGE_W23_FIXED_SEED_EDGE_AND_PAIR_AUDIT'
    assert archived['curve_id'] == protocol['curve_id']
    assert archived['seed_mask'] == protocol['seed_mask'] == 898618
    assert len(archived['audited_edges']) == 8
    field = Field(131, [0, 1, 2, 13])
    curve = Curve(field, 0)
    def endpoint_options(mask):
        w = mask << 1
        assert trace(field, w) == 0
        assert trace(field, field.inv(w)) == 0
        u = half_trace(field, w)
        assert field.mul(u, u) ^ u == w
        x = 1 ^ field.inv(u)
        x2 = field.mul(x, x)
        rhs = x ^ field.inv(x2)
        z = half_trace(field, rhs)
        assert field.mul(z, z) ^ z == rhs
        y = field.mul(x, z)
        points = ((x, y), (x, y ^ x))
        assert all(curve.on_curve(point) for point in points)
        return points
    checks = []
    for entry in archived['audited_edges']:
        a, b = entry['masks']
        assert a ^ b == 898618
        assert field.mul(a << 1, b << 1) == entry['product']
        pa, pb = endpoint_options(a), endpoint_options(b)
        sums = [curve.add(left, right) for left in pa for right in pb]
        assert all(point is not None for point in sums)
        x_roots = sorted({point[0] for point in sums})
        assert x_roots == entry['pair_x_roots']
        checks.append({'masks': [a, b], 'pair_x_roots': x_roots,
                       'signed_pair_outputs': len(set(sums))})
    result = {'status': 'N131_IMPLICIT_SOURCE_SAMPLE_PASS',
              'protocol_sha256': sha(D / 'n131_transfer_protocol.json'),
              'archived_sage_audit_sha256': sha(SAGE_AUDIT),
              'curve_id': archived['curve_id'],
              'sample_edges_checked': len(checks),
              'signed_pair_outputs_checked': sum(row['signed_pair_outputs'] for row in checks),
              'rows': checks}
    (D / 'n131_transfer_result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'sample_edges_checked',
                                            'signed_pair_outputs_checked')}))


if __name__ == '__main__':
    main()
