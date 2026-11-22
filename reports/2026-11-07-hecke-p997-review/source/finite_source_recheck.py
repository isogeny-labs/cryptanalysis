"""Independent integer-mod-p record recheck; not a blind rederivation."""
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

P = 997
BASE = Path(__file__).resolve().parent / 'scratch-base'
HERE = BASE / 'experiments/hecke-432-prime997-20261025'

def j_invariant(a, b):
    return 1728 * 4*a**3 * pow((4*a**3+27*b*b) % P, -1, P) % P

@lru_cache(None)
def roots(a, b, ell):
    if ell == 2:
        return tuple(x for x in range(P) if (x**3+a*x+b) % P == 0)
    return tuple(x for x in range(P)
                 if (3*x**4+6*a*x*x+12*b*x-a*a) % P == 0)

def target(a, b, r, ell):
    if ell == 2:
        t = 3*r*r+a
        return (a-5*t) % P, (b-7*r*t) % P
    return (a-5*(6*r*r+2*a)) % P, (b-7*(10*r**3+6*a*r+4*b)) % P

@lru_cache(None)
def paths(a, b, ell, depth, back=None):
    if depth == 0:
        return ((),)
    out = []
    for r in roots(a, b, ell):
        if r == back:
            continue
        aa, bb = target(a, b, r, ell)
        for tail in paths(aa, bb, ell, depth-1, -ell*r % P):
            out.append((r,)+tail)
    return tuple(out)

def main():
    census = json.loads((HERE/'census.json').read_text())
    image = json.loads((HERE/'image.json').read_text())
    raw = {r['j']:r for r in census['rows']}
    assert len(raw) == len(census['rows']) == 62
    assert all(r['label']=='generic' for r in census['rows'])
    checked_edges = 0
    for row in census['rows']:
        a, b = row['curve_ainvs'][3:]
        assert row['j'] == j_invariant(a,b)
        assert row['paired_chain_count'] == len(row['two_paths'])*len(row['three_paths'])
        squares = Counter(y*y % P for y in range(P))
        assert row['trace'] == P-sum(squares[(x**3+a*x+b) % P] for x in range(P))
        for ell, depth, key in [(2,4,'two_paths'),(3,3,'three_paths')]:
            listed = set()
            for path in row[key]:
                assert len(path) == depth
                aa, bb, back = a, b, None
                for edge in path:
                    r = edge['kernel_x']
                    assert r in roots(aa,bb,ell) and r != back
                    assert edge['source_j'] == j_invariant(aa,bb)
                    aa,bb = target(aa,bb,r,ell)
                    assert edge['target_ainvs'] == [0,0,0,aa,bb]
                    assert edge['target_j'] == j_invariant(aa,bb)
                    back = -ell*r % P
                    assert edge['dual_kernel_x'] == back
                    checked_edges += 1
                listed.add(tuple(e['kernel_x'] for e in path))
            assert len(listed) == len(row[key])
            assert listed == set(paths(a,b,ell,depth))
    all_j = {}
    primitive = next(g for g in range(2,P) if all(pow(g,(P-1)//q,P)!=1 for q in [2,3,83]))
    special = []
    for j in range(P):
        if j in [0,1728 % P]:
            models = ([(0,pow(primitive,k,P)) for k in range(6)] if j == 0
                      else [(pow(primitive,k,P),0) for k in range(4)])
            for a,b in models:
                n2 = len(paths(a,b,2,4))
                n3 = len(paths(a,b,3,3)) if n2 else 0
                special.append({'j':j,'a':a,'b':b,'paired_chains':n2*n3})
            continue
        a,b = -3*j*(j-1728) % P, -2*j*(j-1728)**2 % P
        n2 = len(paths(a,b,2,4))
        n3 = len(paths(a,b,3,3)) if n2 else 0
        if n2*n3:
            all_j[j] = n2*n3
            assert raw[j]['curve_ainvs'] == [0,0,0,a,b]
            assert raw[j]['paired_chain_count'] == n2*n3
    assert set(all_j) == set(raw)
    assert sum(all_j.values()) == 1800
    assert not any(r['paired_chains'] for r in special)
    # Re-enumerate all B points, not merely the three saved candidates.
    squares = {}
    for y in range(P):
        squares.setdefault(y*y % P,[]).append(y)
    B = [None]+[(x,y) for x in range(P) for y in squares.get((x**3-16) % P,[])]
    E = [None]+[(x,y) for x in range(P) for y in squares.get((x**3+432) % P,[])]
    def dual(q):
        if q is None or q[0] == 0:
            return None
        x,y = q
        return ((x**3-64)*pow(x,-2,P) % P,y*(x**3+128)*pow(x,-3,P) % P)
    preimages = {}
    for q in B:
        preimages.setdefault(dual(q),set()).add(q)
    fibers = Counter()
    for row in image['rows']:
        v = row['projections'][0]
        h = tuple(v['E_point']) if v['E_point'] is not None else None
        qset = {tuple(q) if q is not None else None for q in v['B_preimages']}
        assert qset == preimages[h]
        fibers[h] += 1
    assert len(B)==len(E)==1008
    assert len(preimages)==336 and all(len(v)==3 for v in preimages.values())
    assert len(fibers)==72 and None not in fibers
    result = {'status':'PASS_FINITE_SOURCE_AND_COSET_RECHECK','prime':P,
              'all_j_values_reconstructed':P,'generic_classes':len(raw),
              'source_pairs':sum(all_j.values()),'raw_edges_checked':checked_edges,
              'special_twists':special,'B_order':len(B),'E_order':len(E),
              'dual_rational_image_size':len(preimages),
              'E_projection_images':len(fibers),'histogram':dict(sorted(Counter(fibers.values()).items())),
              'scope':'finite chain formulas and archived cosets; no modular-map or quarter-shift reevaluation'}
    (Path(__file__).resolve().parent/'finite-source-recheck.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))

if __name__ == '__main__':
    main()
