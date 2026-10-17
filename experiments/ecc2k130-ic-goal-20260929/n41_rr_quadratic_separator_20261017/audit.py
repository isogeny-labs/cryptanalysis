"""Independent Gaussian determinant, group, and certificate replay."""
import hashlib
import importlib.util
import json
import resource
import time
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parent
PREV = ROOT / 'n41_rr_function_selector_20261017' / 'audit.py'
SPEC = importlib.util.spec_from_file_location('independent_n41_field', PREV)
field = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(field)
GEOMETRY = ROOT / 'n41_w8_fixed_sum_table_20261009' / 'geometry.json'
WITNESS = ROOT / 'n41_sixpair_shared_target_20261017' / 'join_audit_result.json'
N = 41
WIDTH = N + N * (N - 1) // 2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def determinant(points):
    matrix = []
    for x, y in points:
        x2 = field.mul(x, x)
        matrix.append([1, x, y, x2, field.mul(x, y),
                       field.mul(x2, x), field.mul(x2, y)])
    result = 1
    for column in range(7):
        pivot = next((row for row in range(column, 7)
                      if matrix[row][column]), None)
        if pivot is None:
            return 0
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        value = matrix[column][column]
        result = field.mul(result, value)
        inverse = field.inv(value)
        for row in range(column + 1, 7):
            if matrix[row][column] == 0:
                continue
            factor = field.mul(matrix[row][column], inverse)
            for c in range(column + 1, 7):
                matrix[row][c] ^= field.mul(factor, matrix[column][c])
            matrix[row][column] = 0
    return result


def roots(block, mask):
    rows = [row for row in block['states'] if row['a'] == mask]
    assert len(rows) == 4
    by_x = {}
    for row in rows:
        x, y = row['raw_sum']
        by_x.setdefault(x, set()).add(y)
    assert len(by_x) == 2 and all(len(ys) == 2 for ys in by_x.values())
    return [[(x, y) for y in sorted(by_x[x])] for x in sorted(by_x)]


def feature(word, degree):
    result = word
    if degree == 2:
        index = N
        for low in range(N):
            for high in range(low + 1, N):
                if word & (1 << low) and word & (1 << high):
                    result ^= 1 << index
                index += 1
        assert index == WIDTH
    return result


def consistent_add(basis, values, degree):
    width = N if degree == 1 else WIDTH
    trial = dict(basis)
    mask = (1 << width) - 1
    for value in values:
        row = feature(value, degree) | (1 << width)
        while row & mask:
            bit = (row & mask) & -(row & mask)
            pivot = bit.bit_length() - 1
            if pivot in trial:
                row ^= trial[pivot]
            else:
                trial[pivot] = row
                break
        else:
            if row >> width & 1:
                return None
    return trial


def chart_values(geometry, fixed, target, mask, root_index):
    first = roots(geometry['blocks'][0], mask)[root_index][0]
    base = [first] + fixed
    values = []
    group_hits = 0
    for sign_mask in range(64):
        points = [(x, y ^ x if sign_mask >> slot & 1 else y)
                  for slot, (x, y) in enumerate(base)]
        value = determinant(points + [(target[0], target[1] ^ target[0])])
        group = None
        for point in points:
            group = field.add(group, point)
        assert (value == 0) == (group == tuple(target))
        group_hits += group == tuple(target)
        values.append(value)
    return values, group_hits


def main():
    start = time.monotonic()
    protocol = json.loads((D / 'protocol.json').read_text())
    run_protocol = json.loads((D / 'run_protocol.json').read_text())
    receipt = json.loads((D / 'run_result.json').read_text())
    result = json.loads((D / 'result.json').read_text())
    assert all(sha(Path(path)) == digest for path, digest in protocol['sources'].items())
    assert run_protocol['base_protocol_sha256'] == sha(D / 'protocol.json')
    assert run_protocol['runner_sha256'] == sha(D / 'run.py')
    assert run_protocol['producer_sha256'] == sha(D / 'screen.py')
    assert receipt['protocol_sha256'] == sha(D / 'run_protocol.json')
    assert receipt['result_sha256'] == sha(D / 'result.json')
    assert receipt['stdout_sha256'] == sha(D / 'worker.stdout')
    assert receipt['stderr_sha256'] == sha(D / 'worker.stderr')
    assert receipt['status'] == 'COMPLETE' and receipt['exit_code'] == 0
    assert receipt['peak_child_rss_bytes'] < protocol['rss_cap_bytes']
    assert result['status'] == 'QUADRATIC_FAMILY_SCREEN_COMPLETE'
    assert result['protocol_sha256'] == sha(D / 'protocol.json')
    geometry = json.loads(GEOMETRY.read_text())
    witness = json.loads(WITNESS.read_text())
    target = witness['raw_target']
    assert target == protocol['target']
    fixed = []
    for slot in range(1, 6):
        row = witness['pair_rows'][slot]
        options = roots(geometry['blocks'][slot], row['masks'][0])
        matching = [root for root in options if tuple(row['raw_sum']) in root]
        assert len(matching) == 1
        fixed.append(matching[0][0])
    audited = {}
    group_checks = 0
    for mask in protocol['root0_masks']:
        values, hits = chart_values(geometry, fixed, target, mask, 0)
        assert values == result['root0_values'][str(mask)]
        assert hits == 0
        audited[mask] = values
        group_checks += 64
    positive, hits = chart_values(geometry, fixed, target,
                                  protocol['positive_mask'], 1)
    assert positive == result['positive_chart']['determinants']
    assert hits == len(result['positive_chart']['zero_signs']) == 1
    assert result['positive_chart']['zero_signs'] == [15]
    group_checks += 64

    summaries = {}
    for degree in (1, 2):
        for mode in ('sorted', 'greedy'):
            saved = result['panels'][str(degree)][mode]
            basis = {}
            accepted = []
            for row in saved['rows']:
                mask = row['mask']
                trial = consistent_add(basis, audited[mask], degree)
                assert (trial is not None) == row['accepted']
                if trial is not None:
                    basis = trial
                    accepted.append(mask)
                assert len(basis) == row['rank_after']
            assert accepted == saved['accepted_masks']
            cert = int(saved['certificate_hex'], 16)
            assert cert.bit_count() == saved['certificate_weight']
            assert all((cert & feature(value, degree)).bit_count() & 1
                       for mask in accepted for value in audited[mask])
            assert (cert & feature(0, degree)).bit_count() & 1 == 0
            summaries[f'{degree}_{mode}'] = {
                'accepted_charts': len(accepted), 'rank': len(basis),
                'certificate_weight': cert.bit_count(),
                'quadratic_terms': saved['quadratic_terms']}
    report = {'status': 'INDEPENDENT_QUADRATIC_CERTIFICATE_AUDIT_PASS',
              'protocol_sha256': sha(D / 'protocol.json'),
              'result_sha256': sha(D / 'result.json'),
              'independent_field_sha256': sha(PREV),
              'determinants_checked': group_checks,
              'group_sums_checked': group_checks,
              'root0_charts_checked': len(audited),
              'positive_group_hits': hits,
              'certificates': summaries,
              'wall_s': time.monotonic() - start,
              'peak_self_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (D / 'audit_result.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
