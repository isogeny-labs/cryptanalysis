"""Independent integer-field scan and corrected source-pair comparison."""
import json
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = 887


def points(kind):
    squares = defaultdict(list)
    for y in range(P):
        squares[y*y % P].append(y)
    out = []
    for x in range(P):
        rhs = (4*(x*x*x-7)+1 if kind == 'C' else x*x*x+432) % P
        for value in squares[rhs]:
            y = (value-1)*pow(2, -1, P) % P if kind == 'C' else value
            out.append((x, y))
    return sorted(out)


def grouped(terms, xc, yc):
    coeffs = [0] * 13
    for term in terms:
        exponent = term['x_E_exponent']
        coeffs[exponent] = (coeffs[exponent] + int(term['integer_coefficient'])
                            * pow(xc, term['x_C_exponent'], P)
                            * pow(yc, term['y_C_exponent'], P)) % P
    return coeffs


def horner(coeffs, x):
    value = 0
    for coeff in reversed(coeffs):
        value = (value*x + coeff) % P
    return value


def j_value(record, x, y):
    def eval_terms(terms):
        total = 0
        for term in terms:
            coefficient = term['coefficient']
            if '/' in coefficient:
                numerator, denominator = map(int, coefficient.split('/'))
            else:
                numerator, denominator = int(coefficient), 1
            total += numerator * pow(denominator, -1, P) * pow(x, term['x_power'], P) * pow(y, term['y_power'], P)
        return total % P
    denominator = eval_terms(record['denominator'])
    return None if denominator == 0 else -eval_terms(record['numerator']) * pow(denominator, -1, P) % P


def dual_image(point):
    x, y = point
    return ((pow(x, 3, P)-64)*pow(x*x, -1, P) % P,
            y*(pow(x, 3, P)+128)*pow(x, -3, P) % P)


def branch(terms, xc, yc, xe):
    return sum(int(t['integer_coefficient']) * pow(xc, t['x_C_exponent'], P)
               * pow(yc, t['y_C_exponent'], P) * pow(xe, t['x_E_exponent'], P)
               for t in terms) % P


def main():
    protocol_path = HERE / 'protocol.json'
    protocol = json.loads(protocol_path.read_text())
    inputs = {}
    for name, record in protocol['inputs'].items():
        path = Path(record['path'])
        assert sha256(path.read_bytes()).hexdigest() == record['sha256']
        inputs[name] = json.loads(path.read_text())
    result = json.loads((HERE / 'result.json').read_text())
    assert result['protocol_sha256'] == sha256(protocol_path.read_bytes()).hexdigest()
    produced = {}
    for shard in result['pair_shards']:
        path = HERE / shard['file']
        assert sha256(path.read_bytes()).hexdigest() == shard['sha256']
        for row in json.loads(path.read_text()):
            key = (tuple(row['C_point']), tuple(row['E_point']))
            assert key not in produced
            produced[key] = row
    c_points, e_points = points('C'), points('E')
    assert len(c_points)+1 == len(e_points)+1 == 888
    e_by_x = defaultdict(list)
    for xe, ye in e_points:
        e_by_x[xe].append(ye)
    scan = set()
    for xc, yc in c_points:
        coeffs = grouped(inputs['resolvent']['terms'], xc, yc)
        for xe, y_values in e_by_x.items():
            if horner(coeffs, xe) == 0:
                scan.update((((xc, yc), (xe, ye)) for ye in y_values))
    assert scan == set(produced) and len(scan) == 872

    maps = inputs['coordinate']
    intermediate = inputs['intermediate']
    points_by_js = defaultdict(list)
    for xc, yc in c_points:
        js = tuple(j_value(record, xc, yc) for record in
                   (maps['source_j'], intermediate['j3'], intermediate['j9'], maps['target_j']))
        points_by_js[js].append((xc, yc))
    models = {(tuple(model['curve_ainvs']), model['label']): model
              for model in inputs['census']['rows']}
    source_pairs = defaultdict(list)
    source_rows = []
    for i in range(4):
        source_rows.extend(inputs[f'corrected_{i:02d}'])
    assert len(source_rows) == 872
    for row in source_rows:
        model = models[(tuple(row['source_ainvs']), row['source_label'])]
        i, j = row['pair']
        assert 0 <= i < len(model['two_paths']) and 0 <= j < len(model['three_paths'])
        js = (model['j'], *(edge['target_j'] for edge in model['three_paths'][j]))
        assert len(points_by_js[js]) == 1
        bp = tuple(row['B_point'])
        key = (points_by_js[js][0], dual_image(bp))
        source_pairs[key].append({'source_label': row['source_label'],
                                  'source_ainvs': row['source_ainvs'], 'pair': row['pair'],
                                  'B_point': row['B_point']})
    assert len(source_pairs) == 864
    assert Counter(map(len, source_pairs.values())) == {1: 856, 2: 8}
    assert set(source_pairs) <= scan
    extra = sorted(scan - set(source_pairs))
    missing = sorted(set(source_pairs) - scan)
    assert not missing
    branch_status = Counter()
    matched_status = Counter()
    extra_status = Counter()
    branch_mismatch = []
    for key, row in produced.items():
        (xc, yc), (xe, ye) = key
        numerator = branch(inputs['branch']['numerator_terms'], xc, yc, xe)
        denominator = branch(inputs['branch']['denominator_terms'], xc, yc, xe)
        if denominator == 0:
            status = 'ZERO_DENOMINATOR'
        else:
            xb = numerator * pow(denominator, -1, P) % P
            yden = (xb**3+128) % P
            if xb == 0 or yden == 0:
                status = 'UNDEFINED_Y_INVERSE'
            else:
                yb = ye*pow(xb, 3, P)*pow(yden, -1, P) % P
                status = 'VALID' if (yb*yb-xb**3+16) % P == 0 and (xb**3-xe*xb*xb-64) % P == 0 else 'INVALID'
                if status == 'VALID' and key in source_pairs and (xb, yb) not in {
                        tuple(source['B_point']) for source in source_pairs[key]}:
                    branch_mismatch.append(key)
        assert status == row['branch_status']
        branch_status[status] += 1
        (matched_status if key in source_pairs else extra_status)[status] += 1
    assert not branch_mismatch
    exception_details = []
    for (xc, yc), (xe, ye) in extra:
        numerator = branch(inputs['branch']['numerator_terms'], xc, yc, xe)
        denominator = branch(inputs['branch']['denominator_terms'], xc, yc, xe)
        selected_x = numerator * pow(denominator, -1, P) % P if denominator else None
        cubic_roots = [x for x in range(P) if (x**3-xe*x*x-64) % P == 0]
        rational_b = [[x, y] for x in cubic_roots for y in range(P)
                      if (y*y-x**3+16) % P == 0]
        exception_details.append({'C_point': [xc, yc], 'E_point': [xe, ye],
                                  'branch_numerator': numerator,
                                  'branch_denominator': denominator,
                                  'selected_x_B': selected_x,
                                  'cubic_roots': cubic_roots,
                                  'rational_B_candidates': rational_b})
    assert Counter((d['branch_numerator'] == 0, d['branch_denominator'] == 0,
                    d['selected_x_B']) for d in exception_details) == {
                        (False, False, 806): 4, (True, True, None): 4}
    out = {'status': 'PASS_INDEPENDENT_P887_INVERSE_AUDIT',
           'C_group_order': 888, 'E_group_order': 888,
           'resolvent_pair_count': len(scan), 'corrected_source_count': len(source_rows),
           'corrected_pair_count': len(source_pairs),
           'source_pair_multiplicity_histogram': dict(sorted(Counter(map(len, source_pairs.values())).items())),
           'matched_pair_count': len(set(source_pairs) & scan),
           'extra_pairs': [[list(c), list(e)] for c, e in extra],
           'exception_details': exception_details,
           'missing_pairs': [[list(c), list(e)] for c, e in missing],
           'branch_status_histogram': dict(sorted(branch_status.items())),
           'matched_branch_status_histogram': dict(sorted(matched_status.items())),
           'extra_branch_status_histogram': dict(sorted(extra_status.items())),
           'branch_mismatch_count': len(branch_mismatch)}
    (HERE / 'audit.json').write_text(json.dumps(out, sort_keys=True, indent=2) + '\n')
    print(json.dumps(out, sort_keys=True))


if __name__ == '__main__':
    main()
