"""Target-conditioned quartic root extraction and source-span decoding."""
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def field(degree):
    P = PolynomialRing(GF(2), 'u')
    u = P.gen()
    modulus = (u**41+u**3+1) if degree == 41 else (u**131+u**13+u**2+u+1)
    K = GF(2**degree, name='u', modulus=modulus)

    def dec(value):
        return K(P([(value >> i) & 1 for i in range(degree)]))

    def enc(value):
        return sum(int(bit) << i for i, bit in enumerate(value.polynomial().list()))

    return K, dec, enc


def quartic_coefficients(K, dec, terms, p):
    powers = [K.one(), p, p*p, p*p*p, p*p*p*p]
    grouped = [K.zero() for _ in range(5)]
    for i, j, value in terms:
        grouped[j] += dec(value)*powers[i]
    return grouped


def root_timing(K, dec, enc, ring, terms, first_code, p,
                decode_source, source_valid):
    started = time.monotonic()
    grouped = quartic_coefficients(K, dec, terms, p)
    polynomial = ring(grouped)
    degree = int(polynomial.degree()) if polynomial else -1
    prep_seconds = time.monotonic()-started
    roots_started = time.monotonic()
    roots = [] if not polynomial else polynomial.roots(multiplicities=False)
    root_seconds = time.monotonic()-roots_started
    hits = []
    for root in roots:
        code = decode_source(enc(root))
        if code is not None:
            hits.append({'second_code': code, 'valid_source': bool(source_valid(code)),
                         'distinct': code != first_code})
    return {'first_code': first_code, 'quartic_degree': degree,
            'field_roots': len(roots), 'span_root_hits': hits,
            'coefficient_seconds': prep_seconds, 'root_seconds': root_seconds,
            'total_seconds': time.monotonic()-started}


def n41_data(cfg):
    lines = (WORKSPACE / cfg['n41_input']).read_text().splitlines()
    assert lines[0] == 'FREECODE 25 281 13'
    sources, targets = {}, {}
    for line in lines[1:]:
        fields = line.split()
        if fields[0] == 'P':
            _, code, p1, p2 = fields
            sources[int(code)] = (int(p1), int(p2))
        elif fields[0] == 'T':
            _, index, x, y = fields
            targets[int(index)] = {'point': [int(x), int(y)], 'terms': []}
        elif fields[0] == 'C':
            _, index, i, j, value = fields
            targets[int(index)]['terms'].append((int(i), int(j), int(value)))
    assert len(sources) == 281 and len(targets) == 25
    return sources, targets


def bit_basis_decoder(basis):
    pivots = {}
    for j, value in enumerate(basis):
        word, code = value, 1 << j
        while word:
            bit = word.bit_length()-1
            if bit not in pivots:
                pivots[bit] = (word, code)
                break
            row, row_code = pivots[bit]
            word ^= row
            code ^= row_code
        assert word

    def decode(value):
        code = 0
        while value:
            bit = value.bit_length()-1
            if bit not in pivots:
                return None
            row, row_code = pivots[bit]
            value ^= row
            code ^= row_code
        return code

    return decode


def summarize(rows):
    roots = [row['root_seconds'] for row in rows]
    return {'queries': len(rows), 'root_seconds_total': sum(roots),
            'root_seconds_median': statistics.median(roots),
            'root_seconds_max': max(roots),
            'field_roots_total': sum(row['field_roots'] for row in rows),
            'span_hits_total': sum(len(row['span_root_hits']) for row in rows)}


def run_n41(cfg, mode):
    sources, targets = n41_data(cfg)
    census = json.loads((WORKSPACE / cfg['n41_census']).read_text())
    K, dec, enc = field(41)
    R = PolynomialRing(K, 'q')
    qmap = {value[1]: code for code, value in sources.items()}
    assert len(qmap) == len(sources)
    panels = [0] if mode == 'n41_smoke' else [0, 1]
    first_codes = [253] if mode == 'n41_smoke' else sorted(sources)
    rows = []
    for index in panels:
        target_rows = []
        for number, code in enumerate(first_codes):
            record = root_timing(K, dec, enc, R, targets[index]['terms'],
                                 code, dec(sources[code][0]), qmap.get,
                                 lambda qcode: qcode in sources)
            record['target_index'] = index
            target_rows.append(record)
            if number % 32 == 0:
                print(json.dumps({'event': 'PROGRESS', 'mode': mode,
                                  'target_index': index, 'first_codes_done': number+1}),
                      flush=True)
        hits = sorted([[row['first_code'], hit['second_code']]
                       for row in target_rows for hit in row['span_root_hits']
                       if hit['valid_source'] and hit['distinct']])
        assert hits == sorted(census['rows'][index]['zero_pairs'])
        rows.extend(target_rows)
    return {'status': 'PASS_N41_QUARTIC_ROOT_CONTROL',
            'target_indices': panels, 'source_codes_per_target': len(first_codes),
            'rows': rows, 'summary': summarize(rows),
            'matching_zero_pairs': {str(i): census['rows'][i]['zero_pairs'] for i in panels}}


def run_n131(cfg):
    gate = json.loads((HERE / 'n131_gate.json').read_text())
    for name, expected in gate['sources'].items():
        path = Path(name)
        if not path.is_absolute():
            path = WORKSPACE / path
        assert sha(path) == expected, name
    assert gate['status'] == 'FROZEN_N131_AFTER_N41_CONTROL'
    n41 = json.loads((HERE / 'n41_result.json').read_text())
    assert n41['status'] == 'PASS_N41_QUARTIC_ROOT_CONTROL'
    assert n41['target_indices'] == [0, 1] and n41['source_codes_per_target'] == 281
    source = json.loads((WORKSPACE / cfg['n131_input']).read_text())
    K, dec, enc = field(131)
    R = PolynomialRing(K, 'q')
    seed_mask = 898618
    seed = dec(seed_mask << 1)
    bits = [bit for bit in range(33) if bit != seed_mask.bit_length()-1]
    masks = [dec(1 << (bit+1)) for bit in bits]
    basis = [(a*a+seed*a)**(1 << 18) for a in masks]
    decode = bit_basis_decoder([enc(value) for value in basis])
    assert decode(source['rows'][0]['positive_pair_products'][1]) == 16722

    def parameter(code):
        return sum((masks[j] for j in range(32) if code >> j & 1), K.zero())

    def valid(code):
        a = parameter(code)
        return bool(a and a+seed and a.trace() == 0 and
                    (1/a).trace() == 0 and (1/(a+seed)).trace() == 0)

    proposed = cfg['n131_first_codes']
    assert proposed[0] == 3 and len(proposed) == len(set(proposed))
    first_codes = [code for code in proposed if valid(code)]
    assert first_codes[0] == 3 and valid(16722)
    rows = []
    for index in (0, 1):
        terms = [tuple(item) for item in source['rows'][index]['terms']]
        for number, code in enumerate(first_codes):
            a = parameter(code)
            p = a*(a+seed)
            record = root_timing(K, dec, enc, R, terms, code, p, decode, valid)
            record['target_index'] = index
            rows.append(record)
            if number % 8 == 0:
                print(json.dumps({'event': 'PROGRESS', 'mode': 'n131',
                                  'target_index': index, 'first_codes_done': number+1}),
                      flush=True)
    positive_hits = [hit['second_code'] for row in rows
                     if row['target_index'] == 0 and row['first_code'] == 3
                     for hit in row['span_root_hits']
                     if hit['valid_source'] and hit['distinct']]
    assert 16722 in positive_hits
    return {'status': 'PASS_N131_QUARTIC_ROOT_PANEL',
            'target_indices': [0, 1], 'proposed_first_codes': len(proposed),
            'valid_first_codes': len(first_codes), 'rows': rows,
            'summary': summarize(rows), 'positive_second_codes': positive_hits}


def main():
    mode = sys.argv[1]
    assert mode in ('n41_smoke', 'n41', 'n131')
    cfg = json.loads((HERE / 'protocol.json').read_text())
    for name, expected in cfg['sources'].items():
        path = Path(name)
        if not path.is_absolute():
            path = WORKSPACE / path
        assert sha(path) == expected, name
    outcome = HERE / f'{mode}_result.json'
    assert not outcome.exists()
    started = time.monotonic()
    result = run_n41(cfg, mode) if mode.startswith('n41') else run_n131(cfg)
    result.update({'mode': mode, 'candidate_id': None,
                   'curve_id': cfg['n41_curve_id'] if mode.startswith('n41') else cfg['n131_curve_id'],
                   'wall_seconds': time.monotonic()-started,
                   'protocol_sha256': sha(HERE / 'protocol.json')})
    outcome.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({key: result[key] for key in
                      ('mode', 'status', 'wall_seconds', 'summary')}, sort_keys=True),
          flush=True)


if __name__ == '__main__':
    main()
