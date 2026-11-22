"""Find a contradiction certificate for quadratic Boolean root interpolation."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
protocol = json.loads((here/'low_degree_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for source, digest in protocol['sources'].items():
    assert sha(source) == digest, source
assert not (here/'low_degree_result.json').exists()


def features(code, bits):
    terms = [1] + [(code >> i) & 1 for i in range(bits)]
    terms.extend(((code >> i) & 1) & ((code >> j) & 1)
                 for i in range(bits) for j in range(i+1, bits))
    return sum(value << j for j, value in enumerate(terms))


results = []
for mode, bits, count in [('n41', 8, 71), ('n131', 28, 448)]:
    data = json.loads((here/f'{mode}_result.json').read_text())['queries'][0]['sources']
    if mode == 'n131':
        data = [row for row in data if isinstance(row['code'], int)]
    data = sorted(data, key=lambda row: row['code'])[:count]
    assert len(data) == count and len({row['code'] for row in data}) == count
    basis = {}
    contradiction = None
    for i, row in enumerate(data):
        x = features(row['code'], bits)
        y = row['pair_roots'][0]
        witness = 1 << i
        while x:
            pivot = x.bit_length()-1
            if pivot not in basis:
                basis[pivot] = (x, y, witness)
                break
            bx, by, bw = basis[pivot]
            x ^= bx
            y ^= by
            witness ^= bw
        if not x and y:
            selected = [j for j in range(count) if witness >> j & 1]
            assert len(selected) >= 2
            fx, fy = 0, 0
            for j in selected:
                fx ^= features(data[j]['code'], bits)
                fy ^= data[j]['pair_roots'][0]
            assert fx == 0 and fy == y and fy != 0
            contradiction = {'source_indices': selected,
                             'source_codes': [data[j]['code'] for j in selected],
                             'xor_features': fx, 'xor_output': fy,
                             'first_detected_row': i}
            break
    assert contradiction is not None, (mode, len(basis))
    results.append({'mode': mode, 'code_bits': bits,
                    'monomials_degree_at_most_two': 1+bits+bits*(bits-1)//2,
                    'sample_size': count, 'rank_before_contradiction': len(basis),
                    'contradiction': contradiction})

out = {'status': 'PASS_QUADRATIC_SECTION_CONTRADICTION_CERTIFICATES',
       'candidate_id': None, 'section': 'first halftrace pair root',
       'protocol_sha256': sha(here/'low_degree_protocol.json'), 'results': results}
(here/'low_degree_result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
for row in results:
    print(row['mode'], 'monomials', row['monomials_degree_at_most_two'],
          'rank', row['rank_before_contradiction'],
          'witness_terms', len(row['contradiction']['source_indices']),
          'first_detected_row', row['contradiction']['first_detected_row'])
