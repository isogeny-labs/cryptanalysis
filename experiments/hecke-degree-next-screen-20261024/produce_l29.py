"""Construct degree-29 Hecke rows at the two preselected full-split fibers."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import GF, classical_modular_polynomial, matrix

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'hecke-two-sheet-small-order-20261023/tools'))
sys.path.insert(0, str(ROOT / 'hecke-l23-targeted-20261024'))
import hecke11 as H
from modular_hecke_stream import build_mod

def sha(path):
    return sha256(path.read_bytes()).hexdigest()

def key(P):
    return (-1, -1) if P.is_zero() else (int(P[0]), int(P[1]))

def main():
    path = HERE / 'l29_protocol.json'
    raw = path.read_bytes()
    protocol = json.loads(raw)
    assert protocol['status'] == 'FROZEN_BEFORE_L29_BUILD'
    source_paths = {
        'producer': HERE / 'produce_l29.py',
        'builder': ROOT / 'hecke-l23-targeted-20261024/modular_hecke_stream.py',
        'hecke11': ROOT / 'hecke-two-sheet-small-order-20261023/tools/hecke11.py',
        'screen': HERE / 'result.json',
        'frontier': ROOT / 'hecke-torsion-frontiers-20261024/p20023.result.json',
        'seed': ROOT / 'hecke-torsion-frontiers-20261024/p20023.seed.result.json',
        'sign': ROOT / 'hecke-sign-closure-20261024/result.json',
        'l23': ROOT / 'hecke-l23-targeted-20261024/result.v2.json',
    }
    assert protocol['source_sha256'] == {name: sha(p) for name, p in source_paths.items()}
    screen = json.loads(source_paths['screen'].read_text())
    prior = json.loads(source_paths['frontier'].read_text())
    seed = json.loads(source_paths['seed'].read_text())
    sign = json.loads(source_paths['sign'].read_text())
    l23 = json.loads(source_paths['l23'].read_text())
    selected = screen['outcomes']['29']['fully_split_adjacencies']
    assert [r['source_j'] for r in selected] == [11535, 14826]
    assert protocol['source_points'] == [[13138, 17262], [7159, 18790]]

    funcs, meta = build_mod(29, 20023, H)
    encoded = {f'{l}:{part}:{k}': {f'{a},{b}': int(c) for (a,b), c in coeff.items()}
               for (l,part,k), coeff in funcs.items()}
    (HERE / 'l29_functions.json').write_text(json.dumps({'functions': encoded, 'metadata': meta},
                                                        indent=2, sort_keys=True)+'\n')
    _, jfun = H.build([2, 3])
    rd = H.Reduced(20023, funcs, jfun, [29])
    phi = classical_modular_polynomial(29)
    T = rd.E([5,5,1]); assert 5*T == rd.E(0)
    def point(a): return rd.E([a[0], a[1], 1])
    def orbit(P): return min(key(P+k*T) for k in range(5))
    accepted = []; attempts = []; new = set()
    old_keys = [tuple(x) for x in prior['column_representatives']]
    old_set = set(old_keys)
    for rep in protocol['source_points']:
        P = point(rep)
        j = rd.j(P); assert j is not None
        xroots = rd.neighbour_x(29, P).roots()
        multiplicity = sum(int(m) for _,m in xroots)
        record = {'source': rep, 'j': int(j), 'rational_x_root_multiplicity': multiplicity}
        if multiplicity != 30:
            record['status'] = 'NOT_ALL_RATIONAL_X'; attempts.append(record); continue
        neighbors = rd.neighbours_all(29, P)
        if neighbors is None or len(neighbors) != 30:
            record['status'] = 'UNRESOLVED_NEIGHBOURS'; attempts.append(record); continue
        if any(rd.j(Q) is None for Q in neighbors):
            record['status'] = 'CUSP_NEIGHBOUR'; attempts.append(record); continue
        assert sum(neighbors, rd.E(0)) == rd.a_l[29]*P
        assert all(phi(j, rd.j(Q)) == 0 for Q in neighbors)
        coeff = Counter(orbit(Q) for Q in neighbors)
        coeff[orbit(P)] -= int(rd.a_l[29])
        coeff = {a:v for a,v in coeff.items() if v}
        new.update(set(coeff)-old_set)
        record['status'] = 'ACCEPTED'; record['row_index'] = len(accepted)
        attempts.append(record)
        accepted.append({'source': rep, 'j': int(j), 'neighbors': [key(Q) for Q in neighbors],
                         'coefficients': coeff})
    keys = sorted(old_set | {tuple(x) for x in l23['new_representatives']} | new)
    idx = {a:i for i,a in enumerate(keys)}
    def enc(row): return {str(idx[a]):v for a,v in row.items() if v}
    def oldenc(row): return enc({old_keys[int(j)]:v for j,v in row.items()})
    base_rows = [oldenc(r['coefficients']) for r in seed['accepted_rows']]
    base_rows += [oldenc(r) for r in prior['rows']]
    sign_rows = [oldenc(r['coefficients']) for r in sign['sign_rows']]
    l23_keys = [tuple(x) for x in l23['all_column_representatives']]
    l23_rows = [enc({l23_keys[int(j)]:v for j,v in r['coefficients'].items()})
                for r in l23['accepted_rows']]
    new_rows = [enc(r['coefficients']) for r in accepted]
    anchor = idx[orbit(point((1,8630)))]
    def mat(rows):
        entries = {(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
        entries[(len(rows),anchor)] = 1
        return matrix(GF(4021),len(rows)+1,len(keys),entries,sparse=False)
    old_indices = {idx[x] for x in old_keys}
    dropped = sorted(set(range(len(keys))) - old_indices)
    rank = {}
    for name, rows in [('hecke',base_rows+l23_rows),
                       ('hecke_sign',base_rows+sign_rows+l23_rows)]:
        before = mat(rows); after = mat(rows+new_rows)
        K = after.right_kernel()
        support = set().union(*(set(v.support()) for v in K.basis()))
        projection = int(after.matrix_from_columns(dropped).rank()) if dropped else 0
        rank[name] = {'before_rank':int(before.rank()),'after_rank':int(after.rank()),
                      'new_column_projection_rank':projection,
                      'induced_old_rank':int(after.rank())-projection,
                      'nullity':int(K.dimension()),
                      'ambiguous_old_indices':sorted(old_keys.index(keys[i]) for i in support & old_indices)}
    out = {'status':'L29_TARGETED_PRODUCED','protocol_sha256':sha256(raw).hexdigest(),
           'source_sha256':{name:sha(p) for name,p in source_paths.items()},
           'functions_sha256':sha(HERE/'l29_functions.json'),'function_metadata':meta,
           'attempts':attempts,'accepted_rows':[
               {**{k:v for k,v in r.items() if k!='coefficients'},'coefficients':enc(r['coefficients'])}
               for r in accepted],
           'new_representatives':sorted(new), 'all_column_representatives':keys,
           'rank_diagnostics':rank,'candidate_id':None,'timing_claim':None}
    (HERE/'l29_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'attempts':attempts,'new_columns':len(new),'rank':rank},sort_keys=True),flush=True)

if __name__ == '__main__': main()
