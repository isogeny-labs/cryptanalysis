"""Read-only terminal replay of identity, status, ranks, and sign certificates."""
import hashlib
import itertools
import json
from pathlib import Path

D = Path(__file__).resolve().parent
S = D.parent / 'n41_sixpair_shared_target_20261017' / 'join_input.tsv'
MOD = (1 << 41) | (1 << 3) | 1

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def mul(a, b):
    result = 0
    while b:
        if b & 1:
            result ^= a
        b >>= 1
        a <<= 1
        if a & (1 << 41):
            a ^= MOD
    return result

def determinant(points):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    assert len(set(x)) == 7
    pair = {(i, j): x[i] ^ x[j] for i in range(7) for j in range(i+1, 7)}
    def vdm(subset):
        z = 1
        for i, j in itertools.combinations(subset, 2):
            z = mul(z, pair[i, j])
        return z
    result = 0
    for sel in itertools.combinations(range(7), 3):
        rest = tuple(i for i in range(7) if i not in sel)
        result ^= mul(mul(mul(mul(y[sel[0]], y[sel[1]]), y[sel[2]]),
                          vdm(sel)), vdm(rest))
    return result

panel = json.loads((D/'panel.json').read_text())
protocol = json.loads((D/'protocol.json').read_text())
result = json.loads((D/'result.json').read_text())
first_result = json.loads((D/'result_v1.json').read_text())
audit = json.loads((D/'audit_result.json').read_text())
first_audit = json.loads((D/'audit_result_v1.json').read_text())
assert panel['source_sha256'] == protocol['source_sha256'] == sha(S)
assert protocol['panel_sha256'] == sha(D/'panel.json')
assert protocol['worker_sha256'] == sha(D/'run.py')
assert result['protocol_sha256'] == sha(D/'protocol.json')
assert result['status'] == first_result['status'] == 'COMPLETE'
fields = ('kind', 'trial', 'possible_assignments', 'evaluated',
          'difference_rank', 'zero_determinants_seen', 'exceptional_charts',
          'stop_reason', 'classification', 'first_determinant')
assert len(result['rows']) == len(first_result['rows']) == 97
for a, b in zip(result['rows'], first_result['rows']):
    assert all(a[f] == b[f] for f in fields)
assert audit['status'] == first_audit['status'] == 'PASS'
assert audit['boxes'] == 97 and audit['independent_determinants'] == 4896
assert audit['independent_group_checks'] == 4896 and audit['group_matches'] == 1
assert audit['producer_result_sha256'] == sha(D/'result.json')
assert audit['panel_sha256'] == sha(D/'panel.json')
assert audit['audit_source_sha256'] == sha(D/'audit.py')
assert result['peak_self_rss_bytes'] < protocol['rss_boundary_bytes']
assert result['elapsed_s'] < protocol['wall_cap_s']
assert len(audit['sign_certificates']) == 32
assert {c['box'] for c in audit['sign_certificates']} == set(range(32))
rows = {}
for line in S.read_text().splitlines()[1:]:
    v = line.split()
    rows[int(v[1]), int(v[2])] = (int(v[9]), int(v[10]))
qx, qy = panel['target']
negative_target = (qx, qx ^ qy)
replayed_values = 0
for certificate in audit['sign_certificates']:
    box = panel['panels'][certificate['box']]
    assert box['kind'] == 'sign' and certificate['checked_values'] == 64
    mask = certificate['functional_mask']
    assert 0 < mask < 1 << 41
    for ids in itertools.product(*box['slots']):
        value = determinant([rows[j, ids[j]] for j in range(6)] + [negative_target])
        assert (mask & value).bit_count() & 1
        replayed_values += 1
assert replayed_values == 2048
lean = (D/'lean_check.stdout').read_text()
assert 'AffineCertificate.affine_nonzero' in lean
assert 'AffineCertificate.full_span_obstruction' in lean
assert 'sorryAx' not in lean and not (D/'lean_check.stderr').read_text()
out = {'status': 'PASS', 'panel_sha256': sha(D/'panel.json'),
       'protocol_sha256': sha(D/'protocol.json'),
       'result_sha256': sha(D/'result.json'),
       'audit_result_sha256': sha(D/'audit_result.json'),
       'lean_stdout_sha256': sha(D/'lean_check.stdout'),
       'replayed_sign_certificate_values': replayed_values,
       'full_rank_boxes': sum(r['difference_rank'] == 41 for r in result['rows']),
       'independent_group_checks': audit['independent_group_checks']}
(D/'terminal.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
print(json.dumps(out))
