"""Independent seven-row Gaussian replay of split-minor classifications."""
import hashlib
import itertools
import json
import resource
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PRIOR = ROOT / 'n41_rr_joint_box_rank_20261017'
SOURCE = ROOT / 'n41_sixpair_shared_target_20261017/join_input.tsv'
MOD = (1 << 41) | (1 << 3) | 1


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reduce(value):
    while value.bit_length() > 41:
        value ^= MOD << (value.bit_length()-42)
    return value


def mul(a, b):
    raw = 0
    while b:
        low = b & -b
        raw ^= a << (low.bit_length()-1)
        b ^= low
    return reduce(raw)


def inv(a):
    assert a
    u, v, g, h = a, MOD, 1, 0
    while u != 1:
        shift = u.bit_length()-v.bit_length()
        if shift < 0:
            u, v, g, h = v, u, h, g
            shift = -shift
        u ^= v << shift
        g ^= h << shift
    return reduce(g)


def determinant(points):
    matrix = []
    for x, y in points:
        x2 = mul(x, x)
        matrix.append([1, x, y, x2, mul(x, y), mul(x2, x), mul(x2, y)])
    result = 1
    for col in range(7):
        pivot = next((j for j in range(col, 7) if matrix[j][col]), None)
        if pivot is None:
            return 0
        matrix[col], matrix[pivot] = matrix[pivot], matrix[col]
        value = matrix[col][col]
        result = mul(result, value)
        inverse = inv(value)
        for j in range(col+1, 7):
            if matrix[j][col]:
                factor = mul(matrix[j][col], inverse)
                for k in range(col+1, 7):
                    matrix[j][k] ^= mul(factor, matrix[col][k])
                matrix[j][col] = 0
    return result


def rank_insert(basis, value):
    while value:
        pivot = value & -value
        key = pivot.bit_length()-1
        if key not in basis:
            basis[key] = value
            return True
        value ^= basis[key]
    return False


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    result = json.loads((HERE / 'result.json').read_text())
    panel = json.loads((PRIOR / 'panel.json').read_text())
    prior_audit = json.loads((PRIOR / 'audit_result.json').read_text())
    assert protocol['source_sha256']['source'] == sha(SOURCE)
    assert protocol['source_sha256']['panel'] == sha(PRIOR / 'panel.json')
    assert result['status'] == 'COMPLETE' and result['protocol_sha256'] == sha(HERE / 'protocol.json')
    assert prior_audit['status'] == 'PASS' and prior_audit['group_matches'] == 1
    masks = {row['box']: row['functional_mask'] for row in prior_audit['sign_certificates']}
    assert len(masks) == 32
    lines = SOURCE.read_text().splitlines()
    rows = {}
    for line in lines[1:]:
        values = line.split()
        slot, state = map(int, values[1:3])
        rows[slot, state] = (int(values[9]), int(values[10]))
    target = tuple(panel['target'])
    minus_target = (target[0], target[0] ^ target[1])
    started = time.monotonic()
    checks = 0
    masked = 0
    zero_count = 0
    for recorded in result['rows']:
        index = recorded['panel_index']
        box = panel['panels'][index]
        basis = {}
        first = None
        count = 0
        for ids in itertools.product(*box['slots']):
            points = [rows[j, ids[j]] for j in range(6)] + [minus_target]
            assert len({p[0] for p in points}) == 7
            value = determinant(points)
            if first is None:
                first = value
            else:
                rank_insert(basis, value ^ first)
            if box['kind'] == 'sign':
                assert (masks[index] & value).bit_count() & 1
                masked += 1
            zero_count += value == 0
            count += 1
            if len(basis) == 41:
                break
        checks += count
        assert first == recorded['first_determinant']
        assert len(basis) == recorded['field_difference_rank']
        if box['kind'] == 'sign':
            assert count == 64 and recorded['status'] == 'CERTIFIED_NO_ZERO'
        else:
            assert len(basis) == 41 and recorded['status'] == 'NO_AFFINE_LINEAR_SEPARATOR'
    assert masked == 32*64 and zero_count == 1
    record = {'status': 'PASS_INDEPENDENT_SPLIT_MINOR_AUDIT',
              'candidate_id': None, 'boxes_checked': len(result['rows']),
              'independent_determinants': checks, 'certified_sign_values': masked,
              'zero_determinants_seen': zero_count,
              'elapsed_seconds': time.monotonic()-started,
              'peak_self_rss_raw': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'protocol_sha256': sha(HERE / 'protocol.json'),
              'result_sha256': sha(HERE / 'result.json'),
              'prior_audit_sha256': sha(PRIOR / 'audit_result.json'),
              'script_sha256': sha(Path(__file__))}
    with (HERE / 'audit_result.json').open('x') as file:
        json.dump(record, file, indent=2, sort_keys=True)
        file.write('\n')
    print(record['status'], checks, masked)


if __name__ == '__main__':
    main()
