"""Independent arithmetic and source-key audit of the corrected p887 census."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 887


def key(row):
    return (tuple(row['source_ainvs']), row['source_label'], tuple(row['pair']))


def evaluate(terms, x, y):
    value = 0
    for term in terms:
        coefficient = term['coefficient']
        numerator, denominator = (map(int, coefficient.split('/'))
                                  if '/' in coefficient else (int(coefficient), 1))
        value += (numerator * pow(denominator, -1, P) *
                  pow(x, term['x_power'], P) * pow(y, term['y_power'], P))
    return value % P


def rational_value(record, x, y):
    denominator = evaluate(record['denominator'], x, y)
    return None if denominator == 0 else (
        -evaluate(record['numerator'], x, y) * pow(denominator, -1, P) % P)


def curve_points(kind):
    squares = defaultdict(list)
    for y in range(P):
        squares[y*y % P].append(y)
    points = []
    for x in range(P):
        rhs = ((4*(x*x*x - 7) + 1) if kind == 'C' else x*x*x - 16) % P
        for value in squares[rhs]:
            y = ((value - 1) * pow(2, -1, P) % P) if kind == 'C' else value
            points.append((x, y))
    return points


def dual_image(point):
    x, y = point
    if x == 0:
        return None
    return ((pow(x, 3, P) - 64) * pow(x*x, -1, P) % P,
            y * (pow(x, 3, P) + 128) * pow(x, -3, P) % P)


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text()) if path.suffix == '.json' else path
    result = json.loads((HERE / 'result.json').read_text())
    assert result['status'] == 'COMPLETE_P887_AUTOMORPHISM_CORRECTION'
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256'] == sha256(
        (HERE / 'rebuild_sage.py').read_bytes()).hexdigest()
    rows = []
    for shard in result['corrected_shards']:
        path = HERE / shard['file']
        assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
        block = json.loads(path.read_text())
        assert len(block) == shard['rows']
        rows.extend(block)
    assert len(rows) == len({key(row) for row in rows}) == 872
    assert inputs['census']['X0_point_count_from_Hecke'] - 8 == len(rows)
    previous = inputs['previous_image']['rows']
    old = {key(row): (index, row) for index, row in enumerate(previous)}
    assert len(old) == 872
    removed = {tuple(row['pair']) for row in result['removed_duplicate_base_rows']}
    assert len(removed) == 4
    retained = [row for row in rows if row['previous_row'] is not None]
    added = [row for row in rows if row['previous_row'] is None]
    assert len(retained) == 868 and len(added) == 4
    retained_keys = {key(row) for row in retained}
    for row in retained:
        index, original = old[key(row)]
        assert row['previous_row'] == index
        assert row['B_point'] == original['B_candidates'][0]
    for row in previous:
        if key(row) not in retained_keys:
            assert row['source_label'] == 'j1728_base'
            assert tuple(row['pair']) in removed
    assert {tuple(row['pair']) for row in added} == {
        tuple(orbit['pair']) for orbit in result['added_twist_orbits']}
    assert all(row['source_label'] == 'j1728_twist' for row in added)
    assert all(row['B_point'] == next(item['B_point'] for item in
               result['added_twist_orbits'] if item['pair'] == row['pair'])
               for row in added)
    assert all((y*y - x*x*x + 16) % P == 0 for x, y in
               (row['B_point'] for row in rows))
    b_points = curve_points('B')
    assert len(b_points) + 1 == 888
    b_fibers = Counter(tuple(row['B_point']) for row in rows)
    assert len(b_fibers) == 109
    assert Counter(b_fibers.values()) == {8: 109}
    assert (0, 4) not in b_fibers and (0, P-4) not in b_fibers
    assert all(dual_image(row['B_point']) is not None for row in rows)
    assert all((ye*ye - xe*xe*xe - 432) % P == 0 for xe, ye in
               (dual_image(row['B_point']) for row in rows))

    coordinate = inputs['coordinate_map']
    intermediate = inputs['intermediate_j']
    points_by_js = defaultdict(list)
    for x, y in curve_points('C'):
        js = tuple(rational_value(map_data, x, y) for map_data in
                   (coordinate['source_j'], intermediate['j3'],
                    intermediate['j9'], coordinate['target_j']))
        points_by_js[js].append((x, y))
    models = {(tuple(model['curve_ainvs']), model['label']): model
              for model in inputs['census']['rows']}
    pairs = defaultdict(list)
    for row in rows:
        model = models[(tuple(row['source_ainvs']), row['source_label'])]
        i, j = row['pair']
        assert 0 <= i < len(model['two_paths']) and 0 <= j < len(model['three_paths'])
        js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][j]))
        assert len(points_by_js[js]) == 1
        pairs[(points_by_js[js][0], dual_image(row['B_point']))].append(key(row))
    pair_hist = dict(sorted(Counter(map(len, pairs.values())).items()))
    assert pair_hist == {1: 856, 2: 8}
    c_count = len({pair[0] for pair in pairs})
    assert c_count == 218 and len(pairs) == 864
    out = {'status': 'PASS_INDEPENDENT_P887_CORRECTION_AUDIT',
           'source_records': len(rows), 'B_group_order': len(b_points)+1,
           'B_image_points_affine': len(b_fibers),
           'B_fiber_size_histogram': dict(Counter(b_fibers.values())),
           'C_point_count': c_count, 'distinct_C_E_pairs': len(pairs),
           'C_E_pair_fiber_histogram': pair_hist,
           'twist_rows_added': len(added), 'base_rows_removed': len(removed)}
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
