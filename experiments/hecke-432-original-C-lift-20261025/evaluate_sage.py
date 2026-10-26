"""Recover original X0(27) points for the full p=997 level-432 source census."""
import json
import sys
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

import sage.misc.lazy_import_cache as lazy_cache
lazy_cache.DOT_SAGE = '/Volumes/SSD990/llm/tmp/hecke432sage'

from sage.all import EllipticCurve, GF, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'hecke-27-coordinate-bridge-20261025'))
from evaluate_sage import roots_for_pair  # noqa: E402


def value_at(map_data, point, field):
    def polynomial(terms):
        return sum((field(QQ(term['coefficient'])) *
                    point[0]**term['x_power'] * point[1]**term['y_power']
                    for term in terms), field(0))
    denominator = polynomial(map_data['denominator'])
    assert denominator != 0
    return -polynomial(map_data['numerator']) / denominator


def source_key(ainvs, label):
    return (tuple(ainvs), label)


def c_point_for_path(curve, maps, intermediate, source_j, path, field):
    assert len(path) == 3
    terminal_j = path[-1]['target_j']
    _, candidates = roots_for_pair(curve, maps, field(source_j), field(terminal_j))
    filtered = [point for point in candidates
                if value_at(intermediate['j3'], point, field) == field(path[0]['target_j'])
                and value_at(intermediate['j9'], point, field) == field(path[1]['target_j'])]
    assert len(filtered) == 1, (source_j, terminal_j, len(candidates), len(filtered))
    point = filtered[0]
    assert point[0]**997 == point[0] and point[1]**997 == point[1]
    return [int(point[0]), int(point[1])], len(candidates)


def hist_and_max(groups):
    hist = Counter(map(len, groups.values()))
    maximum = max(hist)
    witnesses = [list(key) for key, rows in groups.items() if len(rows) == maximum]
    return ({str(k): hist[k] for k in sorted(hist)}, maximum, witnesses[:10])


def main():
    protocol = json.loads((HERE / 'protocol.json').read_text())
    assert protocol['status'] == 'FROZEN_BEFORE_ORIGINAL_C_EVALUATION'
    p = protocol['prime']
    field = GF(p)
    curve = EllipticCurve(field, [0, 0, 1, 0, -7])
    census_path = ROOT / 'hecke-432-prime997-20261025' / 'census.json'
    image_path = ROOT / 'hecke-432-prime997-20261025' / 'image.json'
    map_path = ROOT / 'hecke-27-coordinate-bridge-20261025' / 'coordinate_map.json'
    intermediate_path = ROOT / 'hecke-432-prime997-20261025' / 'intermediate_j.json'
    census = json.loads(census_path.read_text())
    image = json.loads(image_path.read_text())
    maps = json.loads(map_path.read_text())
    intermediate = json.loads(intermediate_path.read_text())
    source_records = {}
    for record in census['rows']:
        key = source_key(record['curve_ainvs'], record['label'])
        assert key not in source_records
        source_records[key] = record
    c_by_path = {}
    candidate_counts = Counter()
    for key, record in source_records.items():
        for j, path in enumerate(record['three_paths']):
            point, count = c_point_for_path(curve, maps, intermediate,
                                            record['j'], path, field)
            c_by_path[(key, j)] = point
            candidate_counts[count] += 1
    rows = []
    seen = set()
    for row in image['rows']:
        key = source_key(row['source_ainvs'], row['source_label'])
        i, j = row['pair']
        source = source_records[key]
        assert row['source_j'] == source['j']
        row_key = (key, i, j)
        assert row_key not in seen
        seen.add(row_key)
        assert len(row['projections']) == 1
        rows.append({'source_ainvs':row['source_ainvs'],
                     'source_label':row['source_label'],
                     'source_j':row['source_j'], 'pair':[i,j],
                     'C_point':c_by_path[(key,j)],
                     'E_point':row['projections'][0]['E_point'],
                     'terminal16_j':source['two_paths'][i][-1]['target_j'],
                     'terminal27_j':source['three_paths'][j][-1]['target_j']})
    assert len(rows) == len(seen) == image['row_count'] == 1800
    groups_ce = defaultdict(list)
    groups_cej16 = defaultdict(list)
    groups_c = defaultdict(list)
    for row in rows:
        ce = (tuple(row['C_point']), tuple(row['E_point']) if row['E_point'] else None)
        groups_c[tuple(row['C_point'])].append(row)
        groups_ce[ce].append(row)
        groups_cej16[(ce, row['terminal16_j'])].append(row)
    h_c, m_c, _ = hist_and_max(groups_c)
    h_ce, m_ce, w_ce = hist_and_max(groups_ce)
    h_cej16, m_cej16, w_cej16 = hist_and_max(groups_cej16)
    out = {
        'status': 'COMPLETE_ORIGINAL_C_E_GROUP_SCREEN',
        'prime':p,
        'protocol_sha256':sha256((HERE/'protocol.json').read_bytes()).hexdigest(),
        'source_hashes':{name:sha256(path.read_bytes()).hexdigest() for name,path in
                         [('census',census_path),('image',image_path),
                          ('coordinate_map',map_path),('intermediate_j',intermediate_path)]},
        'source_count':len(rows), 'unique_C_path_count':len(c_by_path),
        'raw_C_candidate_count_histogram':dict(sorted(candidate_counts.items())),
        'C_point_count':len(groups_c), 'C_histogram':h_c, 'C_maximum':m_c,
        'CE_group_count':len(groups_ce), 'CE_histogram':h_ce,
        'CE_maximum':m_ce, 'CE_maximum_witness_keys':w_ce,
        'CE_j16_group_count':len(groups_cej16), 'CE_j16_histogram':h_cej16,
        'CE_j16_maximum':m_cej16, 'CE_j16_maximum_witness_keys':w_cej16,
        'CE_groups_forcing_multiple_B_lifts':sum(len(v)>24 for v in groups_ce.values()),
        'rows':rows,
    }
    (HERE/'result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:out[k] for k in ('status','source_count','unique_C_path_count',
                       'CE_group_count','CE_maximum','CE_j16_group_count',
                       'CE_j16_maximum','CE_groups_forcing_multiple_B_lifts')},sort_keys=True))


if __name__ == '__main__':
    main()
