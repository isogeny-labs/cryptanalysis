"""Audit the explicit p=997 hypotheses in the generic-degree proof."""
import json
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
P = 997


def read(name):
    path = ROOT / name
    return json.loads(path.read_text()), sha256(path.read_bytes()).hexdigest()


def coefficients(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key == 'coefficient':
                yield Fraction(child)
            else:
                yield from coefficients(child)
    elif isinstance(value, list):
        for child in value:
            yield from coefficients(child)


def main():
    protocol, protocol_hash = read('hecke-432-geometric-fiber-20261025/protocol.json')
    count, count_hash = read('hecke-432-geometric-fiber-20261025/count_result.json')
    evaluation, evaluation_hash = read('hecke-432-geometric-fiber-20261025/evaluation.json')
    prior, prior_hash = read('hecke-432-geometric-fiber-20261025/audit.json')
    coordinate, coordinate_hash = read('hecke-27-coordinate-bridge-20261025/coordinate_map.json')
    intermediate, intermediate_hash = read('hecke-432-prime997-20261025/intermediate_j.json')
    assert protocol['prime'] == P and protocol['selected_source_j'] == 18
    assert P % (2 * 3) != 0
    assert protocol['selected_C_point'] == [639, 232]
    x, y = protocol['selected_C_point']
    assert (y*y+y-x**3+7) % P == 0
    source = protocol['selected_source_curve_ainvs']
    assert source[:3] == [0, 0, 0] and source[3:] == [616, 645]
    a, b = source[3:]
    source_delta = -16*(4*a**3+27*b**2)
    c_delta = -3**9
    e_delta = -432**3
    assert all(delta % P for delta in (source_delta,c_delta,e_delta))
    source_j = 1728*4*a**3*pow(4*a**3+27*b**2,-1,P) % P
    assert source_j == 18 and source_j not in (0,1728%P)
    assert coordinate['curve_ainvs'] == intermediate['curve_ainvs'] == [0,0,1,0,-7]
    maps = {
        'source_j': coordinate['source_j'],
        'target_j': coordinate['target_j'],
        'j3': intermediate['j3'],
        'j9': intermediate['j9'],
    }
    denominator_counts = {}
    for name, item in maps.items():
        cs = list(coefficients(item))
        assert cs and all(c.denominator % P for c in cs)
        denominator_counts[name] = len(cs)
    assert count['protocol_sha256'] == protocol_hash
    assert evaluation['count_sha256'] == count_hash
    assert evaluation['protocol_sha256'] == protocol_hash
    assert evaluation['source_sha256']['coordinate_map'] == coordinate_hash
    assert evaluation['source_sha256']['intermediate_j'] == intermediate_hash
    assert count['status'] == 'COMPLETE_GEOMETRIC_16_FIBER'
    assert evaluation['status'] == 'COMPLETE_GEOMETRIC_E_FIBER'
    assert count['selected_extension_degree'] == evaluation['extension_degree'] == 4
    assert evaluation['selected_C_point'] == protocol['selected_C_point']
    assert evaluation['path_count'] == evaluation['evaluated_count'] == 24
    assert evaluation['distinct_E_outputs'] == 24
    assert all(row['status'] == 'PASS' for row in evaluation['rows'])
    assert prior['status'] == 'PASS_INDEPENDENT_GEOMETRIC_FIBER_AUDIT'
    assert prior['path_count'] == prior['distinct_E_outputs'] == 24
    result = {
        'status': 'PASS_EXPLICIT_GOOD_REDUCTION_AND_SOURCE_BINDINGS',
        'prime': P,
        'source_j': source_j,
        'source_discriminant_mod_p': source_delta % P,
        'C_discriminant_mod_p': c_delta % P,
        'E_discriminant_mod_p': e_delta % P,
        'rational_map_coefficient_counts': denominator_counts,
        'denominators_divisible_by_p': 0,
        'geometric_lifts': evaluation['path_count'],
        'distinct_E_outputs': evaluation['distinct_E_outputs'],
        'input_sha256': {
            'protocol': protocol_hash,
            'count': count_hash,
            'evaluation': evaluation_hash,
            'independent_audit': prior_hash,
            'coordinate_map': coordinate_hash,
            'intermediate_j': intermediate_hash,
        },
    }
    (HERE/'audit.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
