"""Recover all F199 class coordinates from relations and one known anchor."""
import hashlib
import json
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
SOLVE=json.loads((HERE/'anchor-plan.json').read_text())


def check_local(name,expected):
    raw=(HERE/name).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==expected
    return json.loads(raw)


def frozen(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def sparse(item):
    return {int(k):int(v) for k,v in item['row'].items() if v}


def main():
    result=check_local('result.json',SOLVE['result_sha256'])
    check_local('anchor-audit.json',SOLVE['anchor_audit_sha256'])
    assert hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest()==SOLVE['inputs_sha256']
    cls=frozen('class-result.json')['cases'][0]
    prior=frozen('analysis.json')['cases'][0]
    five=frozen('result.json')
    rows=[sparse(x) for x in cls['base_rows']+prior['direct_candidates']+prior['hecke_candidates']]
    rows += [sparse(x) for x in five['arms']['direct']['candidates']]
    rows += [sparse(x) for x in five['arms']['hecke']['candidates']]
    q=PLAN['q']
    equations=[(row,0) for row in rows]+[({SOLVE['anchor_index']:1},SOLVE['anchor_value'])]
    start=time.perf_counter_ns()
    pivots={}
    dependent=0
    for raw,rhs in equations:
        work={j:v%q for j,v in raw.items() if v%q}
        b=rhs%q
        while work:
            j=min(work)
            if j not in pivots:
                z=pow(work[j],-1,q)
                pivots[j]=({k:v*z%q for k,v in work.items()},b*z%q)
                break
            z=work[j]
            basis,basis_rhs=pivots[j]
            b=(b-z*basis_rhs)%q
            for k,v in basis.items():
                y=(work.get(k,0)-z*v)%q
                if y:work[k]=y
                else:work.pop(k,None)
        else:
            if b:raise ValueError('INCONSISTENT_RELATION_SYSTEM')
            dependent+=1
    if len(pivots)!=40:
        raise ValueError('ANCHOR_NOT_FULL_RANK')
    solution=[0]*40
    for j in sorted(pivots,reverse=True):
        row,b=pivots[j]
        solution[j]=(b-sum(v*solution[k] for k,v in row.items() if k!=j))%q
    if solution!=result['q_logs']:
        raise ValueError('SOLVED_VECTOR_MISMATCH')
    if any((sum(v*solution[j] for j,v in row.items())-rhs)%q for row,rhs in equations):
        raise ValueError('EQUATION_REPLAY_FAIL')
    output={'schema':'hecke-d79-p73757-anchor-solve-v1','status':'PASS',
            'q':q,'relation_rows':len(rows),'anchor_index':SOLVE['anchor_index'],
            'anchor_value':SOLVE['anchor_value'],'rank_with_anchor':len(pivots),
            'dependent_equations':dependent,'recovered_q_logs':solution,
            'recovered_vector_sha256':result['q_log_vector_sha256'],
            'solve_wall_ns':time.perf_counter_ns()-start,
            'candidate_id':None,'target_online_ms':None}
    (HERE/'anchor-solve.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','rank_with_anchor':40,'relation_rows':len(rows)}))


if __name__=='__main__':
    main()
