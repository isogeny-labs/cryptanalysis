"""Test every branch assignment for a quadratic Boolean source-root section."""
import hashlib
import json
import time
from pathlib import Path

here = Path(__file__).resolve().parent
protocol = json.loads((here/'protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path, digest in protocol['sources'].items():
    assert sha(path) == digest, path
assert not (here/'result.json').exists()
started = time.monotonic()


def feature_vector(code, bits):
    values = [1] + [(code >> i) & 1 for i in range(bits)]
    values += [((code >> i) & 1) & ((code >> j) & 1)
               for i in range(bits) for j in range(i+1, bits)]
    return sum(value << j for j,value in enumerate(values))


def analyze(mode, n, code_bits, source_path):
    data = json.loads(Path(source_path).read_text())['queries'][0]['sources']
    data = sorted((row for row in data if isinstance(row['code'], int)),
                  key=lambda row: row['code'])
    count = len(data)
    assert count == (71 if mode == 'n41' else 512)
    assert len({row['code'] for row in data}) == count
    features = [feature_vector(row['code'],code_bits) for row in data]
    roots = [row['pair_roots'][0] for row in data]
    deltas = [row['pair_roots'][0] ^ row['pair_roots'][1] for row in data]
    assert all(delta for delta in deltas)
    field_mask = (1 << n)-1
    assert all((root|delta) <= field_mask for root,delta in zip(roots,deltas))

    feature_basis = {}
    dependencies = []
    for index, vector in enumerate(features):
        combination = 1 << index
        while vector:
            pivot = vector.bit_length()-1
            if pivot not in feature_basis:
                feature_basis[pivot] = (vector,combination)
                break
            old_vector, old_combination = feature_basis[pivot]
            vector ^= old_vector
            combination ^= old_combination
        if not vector:
            dependencies.append(combination)
    assert len(dependencies) == count-len(feature_basis)
    root_masks = [sum(((root >> bit)&1) << j for j,root in enumerate(roots))
                  for bit in range(n)]
    delta_masks = [sum(((delta >> bit)&1) << j for j,delta in enumerate(deltas))
                   for bit in range(n)]

    equations = []
    branch_basis = {}
    contradiction = None
    for dep_index, dep in enumerate(dependencies):
        for bit in range(n):
            coeff = dep & delta_masks[bit]
            rhs = (dep & root_masks[bit]).bit_count() & 1
            eq_id = len(equations)
            equations.append((coeff,rhs,dep_index,bit))
            witness = 1 << eq_id
            x,y = coeff,rhs
            while x:
                pivot = x.bit_length()-1
                if pivot not in branch_basis:
                    branch_basis[pivot] = (x,y,witness)
                    break
                old_x,old_y,old_witness = branch_basis[pivot]
                x ^= old_x
                y ^= old_y
                witness ^= old_witness
            if x == 0 and y == 1:
                ids = [i for i in range(len(equations)) if witness >> i & 1]
                check_x=check_y=0
                for i in ids:
                    check_x ^= equations[i][0]
                    check_y ^= equations[i][1]
                assert check_x == 0 and check_y == 1
                contradiction = {'equation_ids': ids,
                                 'xor_branch_coefficients': check_x,
                                 'xor_required_bits': check_y,
                                 'first_detected_equation': eq_id}
                break
        if contradiction is not None:
            break

    return {'mode': mode, 'field_degree': n, 'code_bits': code_bits,
            'source_count': count,
            'quadratic_feature_count': 1+code_bits+code_bits*(code_bits-1)//2,
            'feature_rank': len(feature_basis),
            'source_dependencies': len(dependencies),
            'branch_rank_before_stop': len(branch_basis),
            'equations_processed': len(equations),
            'status': 'NO_QUADRATIC_SECTION_ON_FROZEN_CODES'
                      if contradiction else 'QUADRATIC_SECTION_FEASIBLE_ON_FROZEN_CODES',
            'contradiction': contradiction,
            'codes_sha256': hashlib.sha256(json.dumps([row['code'] for row in data],
                                            separators=(',', ':')).encode()).hexdigest()}


rows = [analyze('n41',41,8,protocol['n41_source']),
        analyze('n131',131,28,protocol['n131_source'])]
out = {'status': 'PASS_BRANCH_ADAPTIVE_QUADRATIC_SECTION_AUDIT',
       'candidate_id': None, 'results': rows,
       'wall_seconds': time.monotonic()-started,
       'protocol_sha256': sha(here/'protocol.json')}
(here/'result.json').write_text(json.dumps(out, sort_keys=True, indent=2)+'\n')
for row in rows:
    print(json.dumps({k: row[k] for k in ('mode','status','source_count',
                                         'quadratic_feature_count','source_dependencies',
                                         'branch_rank_before_stop','equations_processed')}))
