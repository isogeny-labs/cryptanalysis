"""Independently replay source identity, modular invariants, and group counts."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
P = 997


def evaluate(terms, x, y):
    return sum((int(term['coefficient'].split('/')[0]) *
                pow(int(term['coefficient'].split('/')[1]), -1, P)
                if '/' in term['coefficient'] else int(term['coefficient'])) *
               pow(x, term['x_power'], P) * pow(y, term['y_power'], P)
               for term in terms) % P


def map_value(data, x, y):
    denominator = evaluate(data['denominator'], x, y)
    assert denominator
    return -evaluate(data['numerator'], x, y) * pow(denominator, -1, P) % P


def histogram(grouping):
    counts = Counter(len(group) for group in grouping.values())
    return {str(size): counts[size] for size in sorted(counts)}


def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    result = json.loads((HERE/'result.json').read_text())
    inputs = {
        'census':ROOT/'hecke-432-prime997-20261025'/'census.json',
        'image':ROOT/'hecke-432-prime997-20261025'/'image.json',
        'coordinate_map':ROOT/'hecke-27-coordinate-bridge-20261025'/'coordinate_map.json',
        'intermediate_j':ROOT/'hecke-432-prime997-20261025'/'intermediate_j.json',
    }
    assert result['protocol_sha256'] == sha256((HERE/'protocol.json').read_bytes()).hexdigest()
    assert result['source_hashes'] == {name:sha256(path.read_bytes()).hexdigest()
                                       for name,path in inputs.items()}
    census = json.loads(inputs['census'].read_text())
    image = json.loads(inputs['image'].read_text())
    maps = json.loads(inputs['coordinate_map'].read_text())
    intermediate = json.loads(inputs['intermediate_j'].read_text())
    sources = {(tuple(row['curve_ainvs']),row['label']):row for row in census['rows']}
    assert len(sources) == len(census['rows'])
    image_rows = {(tuple(row['source_ainvs']),row['source_label'],*row['pair']):row
                  for row in image['rows']}
    assert len(image_rows) == image['row_count'] == 1800
    assert result['source_count'] == len(result['rows']) == 1800
    groups_c, groups_ce, groups_cej16 = defaultdict(list), defaultdict(list), defaultdict(list)
    seen = set()
    paths = set()
    for row in result['rows']:
        source_key = (tuple(row['source_ainvs']),row['source_label'])
        i,j = row['pair']
        key = (*source_key,i,j)
        assert key not in seen
        seen.add(key)
        source = sources[source_key]
        original = image_rows[key]
        path = source['three_paths'][j]
        assert row['source_j'] == original['source_j'] == source['j']
        assert row['E_point'] == original['projections'][0]['E_point']
        assert row['terminal16_j'] == source['two_paths'][i][-1]['target_j']
        assert row['terminal27_j'] == path[-1]['target_j']
        x,y = row['C_point']
        assert 0 <= x < P and 0 <= y < P and (y*y+y-x*x*x+7)%P == 0
        assert map_value(maps['source_j'],x,y) == source['j']
        assert map_value(maps['target_j'],x,y) == path[-1]['target_j']
        assert map_value(intermediate['j3'],x,y) == path[0]['target_j']
        assert map_value(intermediate['j9'],x,y) == path[1]['target_j']
        if row['E_point'] is not None:
            ex,ey = row['E_point']
            assert (ey*ey-ex*ex*ex-432)%P == 0
        paths.add((source_key,j))
        ce = (tuple(row['C_point']),tuple(row['E_point']) if row['E_point'] else None)
        groups_c[tuple(row['C_point'])].append(key)
        groups_ce[ce].append(key)
        groups_cej16[(ce,row['terminal16_j'])].append(key)
    assert seen == set(image_rows)
    assert result['unique_C_path_count'] == len(paths)
    assert result['C_point_count'] == len(groups_c)
    assert result['C_histogram'] == histogram(groups_c)
    assert result['C_maximum'] == max(map(len,groups_c.values()))
    assert result['CE_histogram'] == histogram(groups_ce)
    assert result['CE_j16_histogram'] == histogram(groups_cej16)
    assert result['CE_group_count'] == len(groups_ce)
    assert result['CE_j16_group_count'] == len(groups_cej16)
    assert result['CE_maximum'] == max(map(len,groups_ce.values()))
    assert result['CE_j16_maximum'] == max(map(len,groups_cej16.values()))
    assert result['CE_groups_forcing_multiple_B_lifts'] == sum(len(v)>24 for v in groups_ce.values())
    out = {'status':'PASS_INDEPENDENT_ORIGINAL_C_AUDIT',
           'source_count':len(seen),'path_count':len(paths),
           'C_point_count':len(groups_c),'C_histogram':histogram(groups_c),
           'CE_histogram':histogram(groups_ce),
           'CE_j16_histogram':histogram(groups_cej16),
           'CE_maximum':result['CE_maximum'],
           'CE_j16_maximum':result['CE_j16_maximum']}
    (HERE/'audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__ == '__main__':
    main()
