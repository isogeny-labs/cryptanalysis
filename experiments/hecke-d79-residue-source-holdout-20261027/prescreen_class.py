"""Choose the first eligible 40-point D79 class without degree-13 outputs."""
import hashlib
import importlib.util
import json
import resource
import time
from collections import Counter
from pathlib import Path

from sage.all import EllipticCurve, EllipticCurve_from_j, GF, hilbert_class_polynomial, is_prime, factor, matrix, QQ

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = json.loads((HERE / 'inputs.json').read_text())


def load_source():
    item = PLAN['frozen']['hecke11.py']
    path = ROOT / item['path']
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('SOURCE_PIN_MISMATCH')
    spec = importlib.util.spec_from_file_location('residue_holdout_class_source', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def class_case(H, funcs, jfun, H79, p, v, n, q):
    start = time.perf_counter_ns()
    R = H.Reduced(p, funcs, jfun, [2, 5])
    E, Fp = R.E, R.Fp
    if int(E.cardinality()) != n:
        raise ValueError('CURVE_ORDER_MISMATCH')
    starts = []
    for j in H79.change_ring(Fp).roots(multiplicities=False):
        if abs(int(EllipticCurve_from_j(j).trace_of_frobenius())) == 2*v:
            starts.extend(R.points_with_j(j))
    seen, frontier = set(starts), list(starts)
    cache = {}
    def in_class(P):
        j = R.j(P)
        if j is None or j == 0 or j == 1728:
            return False
        if j not in cache:
            cache[j] = abs(int(EllipticCurve_from_j(j).trace_of_frobenius()))
        return cache[j] == 2*v
    while frontier:
        nxt = []
        for P in frontier:
            for ell in (2, 5):
                for Q in R.neighbour_candidates(ell, P):
                    if Q not in seen and in_class(Q):
                        seen.add(Q)
                        nxt.append(Q)
        frontier = nxt
    points = sorted(seen, key=lambda P:(int(P[0]),int(P[1])))
    cell = {'p':p,'v':v,'curve_order':n,'largest_prime_factor':q,
            'start_count':len(starts),'class_size':len(points),
            'class_walk_wall_ns':time.perf_counter_ns()-start}
    if len(points) != 40:
        cell['status'] = 'CLASS_SIZE_MISMATCH'
        return cell
    index = {P:i for i,P in enumerate(points)}
    rows = []
    for i,P in enumerate(points):
        for ell in (2,5):
            nb = R.neighbours_all(ell,P)
            if nb is None or not all(Q in index for Q in nb):
                continue
            if sum(nb,E(0)) != R.a_l[ell]*P:
                raise ValueError('BASE_HECKE_EQUATION_FAIL')
            row = Counter(index[Q] for Q in nb)
            row[i] -= int(R.a_l[ell])
            sparse = {k:x for k,x in row.items() if x}
            if sum((x*points[k] for k,x in sparse.items()),E(0)) != E(0):
                raise ValueError('BASE_ROW_GROUP_FAIL')
            rows.append({'source':i,'degree':ell,'row':{str(k):x for k,x in sorted(sparse.items())}})
    projected = [(n//5)*P for P in points]
    T = next((Q for Q in projected if Q != E(0)),None)
    if T is None:
        raise ValueError('ORDER5_PROJECTION_EMPTY')
    lookup = {k*T:k for k in range(5)}
    if len(lookup) != 5 or any(Q not in lookup for Q in projected):
        raise ValueError('ORDER5_PROJECTION_FAIL')
    residues = [lookup[Q] for Q in projected]
    buckets = {r:[i for i,x in enumerate(residues) if x==r] for r in range(5)}
    def round_robin(group):
        return [bucket[k] for k in range(max(len(buckets[r]) for r in group))
                for r in group for bucket in [buckets[r]] if k<len(bucket)]
    order = round_robin((1,4))+round_robin((2,3))+round_robin((0,))
    old_order = round_robin((0,1,2,3,4))
    if sorted(order)!=list(range(40)) or sorted(old_order)!=list(range(40)):
        raise ValueError('SOURCE_ORDER_NOT_PERMUTATION')
    base_rank = int(matrix(QQ,len(rows),40,lambda i,j:int(rows[i]['row'].get(str(j),0))).rank())
    cell.update({'status':'CLASS_READY','class_points':[[int(P[0]),int(P[1])] for P in points],
                 'base_rows':rows,'base_rank_qq':base_rank,'projection_residues':residues,
                 'projection_counts':{str(r):residues.count(r) for r in range(5)},
                 'source_order':order,'old_priority_order':old_order,'ascending_order':list(range(40))})
    return cell


def main():
    H=load_source()
    funcs,jfun=H.build([2,5])
    H79=hilbert_class_polynomial(-79)
    checked=[]
    selected=None
    eligible_seen=0
    path=HERE/'class-result.json'
    for v in range(273,502,2):
        p=v*v+316
        if not is_prime(p):
            continue
        E=EllipticCurve(GF(p),[0,-1,1,-10,-20])
        n=int(E.cardinality())
        q=int(max(prime for prime,_ in factor(n)))
        eligible=n%5==0 and (p-1)%5!=0 and q>=53
        if not eligible:
            continue
        eligible_seen+=1
        cell=class_case(H,funcs,jfun,H79,p,v,n,q)
        checked.append(cell)
        out={'schema':'hecke-d79-residue-source-class-v1','status':'RUNNING',
             'checked_eligible_cases':checked,'selected':None,
             'candidate_id':None,'target_online_ms':None}
        path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
        print(json.dumps({'p':p,'v':v,'status':cell['status'],'class_size':cell['class_size']}),flush=True)
        if cell['status']=='CLASS_READY':
            selected=cell
            break
        if eligible_seen==8:
            break
    out={'schema':'hecke-d79-residue-source-class-v1',
         'status':'CLASS_READY' if selected else 'NO_CLASS',
         'checked_eligible_cases':checked,'selected':selected,
         'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
         'candidate_id':None,'target_online_ms':None}
    path.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':out['status'],'selected_p':None if not selected else selected['p']}))


if __name__=='__main__':
    main()
