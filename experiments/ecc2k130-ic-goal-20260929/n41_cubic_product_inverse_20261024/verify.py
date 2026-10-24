#!/usr/bin/env python3
"""Independent GF(2) Sylvester identity and archived full-panel witness audit."""
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class Poly:
    """Sparse polynomial with GF(2) coefficients in A,B,D,S,r."""
    def __init__(self, terms=()):
        self.terms = frozenset(terms)
    def __add__(self, other):
        if not isinstance(other, Poly):
            other = one if other % 2 else zero
        return Poly(self.terms ^ other.terms)
    __radd__ = __add__
    def __mul__(self, other):
        if not isinstance(other, Poly):
            other = one if other % 2 else zero
        out = set()
        for a in self.terms:
            for b in other.terms:
                term = tuple(x+y for x, y in zip(a, b))
                if term in out:
                    out.remove(term)
                else:
                    out.add(term)
        return Poly(out)
    __rmul__ = __mul__
    def __pow__(self, n):
        out = one
        for _ in range(n):
            out *= self
        return out
    def __eq__(self, other):
        return isinstance(other, Poly) and self.terms == other.terms

zero = Poly()
one = Poly([(0,)*5])
A, B, D, S, r = [Poly([tuple(int(i == j) for i in range(5))]) for j in range(5)]

def determinant(rows):
    out = zero
    for p in itertools.permutations(range(4)):
        term = one
        for i, j in enumerate(p):
            term *= rows[i][j]
        out += term  # Signs equal +1 in characteristic two.
    return out

def main():
    protocol = json.loads((HERE/'protocol.json').read_text())
    data = json.loads((HERE/'result.json').read_text())
    archive_path = ROOT/'n41_w8_three_pair_resultant_20261013/q_census.json'
    archive = json.loads(archive_path.read_text())
    assert sha(archive_path) == protocol['inputs']['n41_w8_three_pair_resultant_20261013/q_census.json']
    assert data['protocol_sha256'] == sha(HERE/'protocol.json')
    assert sha(HERE/'run.py') == protocol['producer_sha256']
    assert sha(HERE/'sage_runtime_info.json') == protocol['runtime_sha256']
    assert all(sha(ROOT/name) == digest for name, digest in protocol['inputs'].items())
    assert data['status'] == 'PASS_N41_FULL_PANEL_QUADRATIC_INVERSE'
    L = one+r
    M = L*B+r*A
    N = L*D+S*A
    norm = L*N*N+r*N*M+S*M*M
    formula = (D+S*A)**2+S*B**2+r*B*(D+S*(A+B))+r**2*D*(A+B+D)
    sylvester = [[L,r,S,zero], [zero,L,r,S],
                 [A,B,D,zero], [zero,A,B,D]]
    assert determinant(sylvester) == formula
    assert norm == L*formula
    assert len(data['panels']) == archive['panels'] == 33
    sums = {key: sum(row['counts'][key] for row in data['panels'])
            for key in data['panels'][0]['counts']}
    assert all(row['counts']['queries'] == 12432 for row in data['panels'])
    assert all(row['counts']['degree_2'] == 12432 for row in data['panels'])
    assert sums == {'queries':410256,'degree_0':0,'degree_1':0,'degree_2':410256,
                    'field_roots':820512,'source_product_hits':1,
                    'admissible_hits':1,'full_point_matches':1}
    assert [row[:4] for row in data['coordinate_hits']] == [row[:4] for row in archive['coordinate_hits']]
    assert data['full_matches'] == archive['full_matches']
    assert data['coordinate_hits'] == [[0,24,37,10,801447660706,216004441708]]
    assert data['full_matches'] == [[0,97,151,42,[0,14,109,51]]]
    assert data['target_dependent_ns'] <= protocol['limits']['wall_seconds']*10**9
    assert data['peak_process_rss_sample_bytes'] <= protocol['limits']['peak_rss_bytes']
    receipt = {'status':'PASS_INDEPENDENT_N41_QUADRATIC_INVERSE_AUDIT',
               'symbolic_resultant_terms':len(formula.terms),
               'symbolic_norm_terms':len(norm.terms),
               'panels':33,'counts':sums,
               'producer_sha256':sha(HERE/'run.py'),
               'verifier_sha256':sha(__file__),
               'result_sha256':sha(HERE/'result.json'),
               'archived_census_sha256':sha(archive_path),
               'protocol_sha256':sha(HERE/'protocol.json')}
    (HERE/'verification.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print({key:receipt[key] for key in ('status','symbolic_resultant_terms','panels','counts')})

if __name__ == '__main__':
    main()
