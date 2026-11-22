"""Exact Boolean ANF of the bivariate resultant with degree-lex order."""
import hashlib
import json
import sys
import time
from pathlib import Path

from sage.all import BooleanPolynomialRing

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]
sys.path.insert(0, str(HERE.parent / 'resultant_block_span_20261018'))
from probe import BinaryField, load_n41, product, source_basis, evaluate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def power_maps(F, basis, base):
    """Boolean ANFs for powers 0..4 of base plus the listed bit basis."""
    linear = {0: base}
    linear.update({1 << j: b for j, b in enumerate(basis) if b})
    squared = {mask: F.square(value) for mask, value in linear.items()}
    fourth = {mask: F.square(value) for mask, value in squared.items()}
    cube = {}
    for xmask, xvalue in linear.items():
        for ymask, yvalue in squared.items():
            mask = xmask | ymask
            cube[mask] = cube.get(mask, 0) ^ F.mul(xvalue, yvalue)
    return [{0: 1},
            {mask: value for mask, value in linear.items() if value},
            {mask: value for mask, value in squared.items() if value},
            {mask: value for mask, value in cube.items() if value},
            {mask: value for mask, value in fourth.items() if value}]


def coeff_map(F, terms, apowers, bpowers, bshift):
    out = {}
    for i, j, c in terms:
        for amask, avalue in apowers[i].items():
            ca = F.mul(c, avalue)
            for bmask, bvalue in bpowers[j].items():
                mask = amask | (bmask << bshift)
                out[mask] = out.get(mask, 0) ^ F.mul(ca, bvalue)
    return {mask: value for mask, value in out.items() if value}


def eval_anf(coeffs, assignment):
    out = 0
    for monomial, field_coeff in coeffs.items():
        if monomial & assignment == monomial:
            out ^= field_coeff
    return out


def load_case(name, cfg):
    if name.startswith('n41_'):
        F = BinaryField(41, (1 << 3) | 1)
        bits = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
        bases = source_basis(F, bits, 112, [12, 24])
        products, rows = load_n41(WORKSPACE / cfg['n41_input'])
        assert len(products) == 281
        assert all((product(bases[0], c), product(bases[1], c)) == row
                   for c, row in products.items())
        target = 0 if name == 'n41_positive' else 1
        free_a = list(range(10))
        free_b = list(range(10))
        fixed_a = fixed_b = 0
        known_codes = (253, 63) if target == 0 else None
        curve_id = cfg['n41_curve_id']
        terms = rows[target]['terms']
        point = rows[target]['point']
    elif name == 'n131_positive_48':
        F = BinaryField(131, (1 << 13) | (1 << 2) | (1 << 1) | 1)
        seed_mask = 898618
        bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
        bases = source_basis(F, bits, seed_mask << 1, [0, 18])
        source = json.loads((WORKSPACE / cfg['n131_input']).read_text())
        target = 0
        free_a = list(range(16))
        free_b = list(range(32))
        fixed_a = fixed_b = 0
        known_codes = (3, 16722)
        curve_id = cfg['n131_curve_id']
        terms = [tuple(item) for item in source['rows'][target]['terms']]
        point = source['rows'][target]['point']
        assert product(bases[0], 3) == source['positive_source_checks'][0]['unrotated_product']
        assert product(bases[1], 16722) == source['rows'][0]['positive_pair_products'][1]
    else:
        raise ValueError(name)
    return F, bases, terms, point, free_a, free_b, fixed_a, fixed_b, known_codes, curve_id


def main():
    case = sys.argv[1]
    assert case in ('n41_positive', 'n41_ordinary', 'n131_positive_48')
    cfg = json.loads((HERE / 'deglex_protocol.json').read_text())
    for name, expected in cfg['sources'].items():
        source = Path(name)
        if not source.is_absolute():
            source = WORKSPACE / source
        assert sha(source) == expected, name
    assert not (HERE / f'{case}_deglex_result.json').exists()
    F, bases, terms, point, free_a, free_b, fixed_a, fixed_b, known, curve_id = load_case(case, cfg)
    nbits = len(free_a)+len(free_b)
    assert nbits in (20, 48)
    started = time.monotonic()
    abase = product(bases[0], fixed_a)
    bbase = product(bases[1], fixed_b)
    apowers = power_maps(F, [bases[0][j] for j in free_a], abase)
    bpowers = power_maps(F, [bases[1][j] for j in free_b], bbase)
    coeffs = coeff_map(F, terms, apowers, bpowers, len(free_a))
    assert coeffs and max(mask.bit_count() for mask in coeffs) <= 4
    if known is not None:
        acode, bcode = known
        assert acode & fixed_a == fixed_a and bcode & fixed_b == fixed_b
        assignment = sum(((acode >> j) & 1) << k for k, j in enumerate(free_a))
        assignment |= sum(((bcode >> j) & 1) << (len(free_a)+k)
                          for k, j in enumerate(free_b))
        assert eval_anf(coeffs, assignment) == 0
        assert evaluate(F, terms, product(bases[0], acode),
                        product(bases[1], bcode)) == 0
    else:
        assignment = None
    print(json.dumps({'event': 'ANF_READY', 'case': case,
                      'field_degree': F.degree, 'bits': nbits,
                      'field_coefficients': len(coeffs),
                      'build_seconds': time.monotonic()-started}), flush=True)

    R = BooleanPolynomialRing(nbits, 'x', order='deglex')
    bit_dicts = [dict() for _ in range(F.degree)]
    for mask, value in coeffs.items():
        exponent = tuple((mask >> j) & 1 for j in range(nbits))
        while value:
            low = value & -value
            bit_dicts[low.bit_length()-1][exponent] = 1
            value ^= low
    equations = [R._from_dict(d) for d in bit_dicts]
    assert len(equations) == F.degree
    print(json.dumps({'event': 'GB_START', 'case': case,
                      'equations': len(equations), 'total_anf_terms':
                      sum(len(d) for d in bit_dicts),
                      'build_seconds': time.monotonic()-started}), flush=True)
    gb_started = time.monotonic()
    gb = list(R.ideal(equations).groebner_basis())
    gb_seconds = time.monotonic()-gb_started
    xs = R.gens()
    pins = {}
    for j in range(nbits):
        if xs[j] in gb:
            pins[j] = 0
        elif xs[j]+1 in gb:
            pins[j] = 1
    recovered = sum(bit << j for j, bit in pins.items()) if len(pins) == nbits else None
    codes = None
    if recovered is not None:
        acode = fixed_a | sum(((recovered >> k) & 1) << j for k, j in enumerate(free_a))
        bcode = fixed_b | sum(((recovered >> (len(free_a)+k)) & 1) << j
                             for k, j in enumerate(free_b))
        codes = [acode, bcode]
        assert eval_anf(coeffs, recovered) == 0
        assert evaluate(F, terms, product(bases[0], acode),
                        product(bases[1], bcode)) == 0
    result = {'status': 'GB_COMPLETE', 'candidate_id': None,
              'case': case, 'curve_id': curve_id, 'target_point': point,
              'free_bits': [len(free_a), len(free_b)],
              'fixed_codes': [fixed_a, fixed_b],
              'field_coefficient_monomials': len(coeffs),
              'total_anf_terms': sum(len(d) for d in bit_dicts),
              'gb_polynomials': len(gb), 'gb_seconds': gb_seconds,
              'total_wall_seconds': time.monotonic()-started,
              'unit_ideal_reported': R.one() in gb,
              'linear_pins': len(pins), 'recovered_codes': codes,
              'known_positive_codes': list(known) if known else None,
              'protocol_sha256': sha(HERE / 'deglex_protocol.json')}
    (HERE / f'{case}_deglex_result.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
