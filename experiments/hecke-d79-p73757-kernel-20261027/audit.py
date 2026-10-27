"""Pure-Python replay of p73757 group laws, q logs, rows and modular ranks."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PLAN=json.loads((HERE/'inputs.json').read_text())
POST=json.loads((HERE/'post_run.json').read_text())


def frozen(name):
    item=PLAN['frozen'][name]
    raw=(ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    return json.loads(raw)


def add(A,B,p):
    if A is None:return B
    if B is None:return A
    x,y=A;u,v=B
    if x==u and (y+v+1)%p==0:return None
    if A==B:
        top=(3*x*x-2*x-10)%p;bottom=(2*y+1)%p
    else:
        top=(v-y)%p;bottom=(u-x)%p
    slope=top*pow(bottom,-1,p)%p
    intercept=(y-slope*x)%p
    X=(slope*slope+1-x-u)%p
    Y=(-slope*X-intercept-1)%p
    return X,Y


def neg(A,p):
    return None if A is None else (A[0],(-A[1]-1)%p)


def mul(k,P,p):
    if k<0:return mul(-k,neg(P,p),p)
    acc=None
    while k:
        if k&1:acc=add(acc,P,p)
        P=add(P,P,p);k>>=1
    return acc


def sparse(item):
    return {int(k):int(v) for k,v in item['row'].items() if v}


def rank(rows,q):
    pivots={}
    for row in rows:
        work={j:x%q for j,x in row.items() if x%q}
        while work:
            j=min(work)
            if j not in pivots:
                z=pow(work[j],-1,q)
                pivots[j]={k:x*z%q for k,x in work.items()}
                break
            z=work[j]
            for k,x in pivots[j].items():
                y=(work.get(k,0)-z*x)%q
                if y:work[k]=y
                else:work.pop(k,None)
    return len(pivots)


def main():
    raw=(HERE/'result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==POST['result_sha256']
    result=json.loads(raw)
    p,q=PLAN['p'],PLAN['q']
    cls=frozen('class-result.json')['cases'][0]
    prior=frozen('analysis.json')['cases'][0]
    five=frozen('result.json')
    points=[tuple(x) for x in cls['class_points']]
    assert len(points)==40 and all(0<=x<p and 0<=y<p and (y*y+y-x*x*x+x*x+10*x+20)%p==0 for x,y in points)
    projected=[mul(PLAN['cofactor_for_q_projection'],P,p) for P in points]
    anchor=next(i for i,x in enumerate(projected) if x is not None)
    T=projected[anchor]
    table={mul(k,T,p):k for k in range(q)}
    assert len(table)==q and mul(q,T,p) is None
    logs=[table[x] for x in projected]
    assert logs==result['q_logs'] and anchor==result['anchor_index'] and logs[anchor]==1
    assert hashlib.sha256(json.dumps(logs,separators=(',',':')).encode()).hexdigest()==result['q_log_vector_sha256']
    base=[sparse(x) for x in cls['base_rows']+prior['direct_candidates']+prior['hecke_candidates']]
    direct=[sparse(x) for x in five['arms']['direct']['candidates']]
    hecke=[sparse(x) for x in five['arms']['hecke']['candidates']]
    families={'support4':base,'support4_plus_direct5':base+direct,
              'support4_plus_hecke5':base+hecke,'support4_plus_both5':base+direct+hecke}
    output={'schema':'hecke-d79-p73757-kernel-audit-v1','status':'PASS','p':p,'q':q,
            'anchor_index':anchor,'checked_families':{}}
    for name,rows in families.items():
        record=result['families'][name]
        assert len(rows)==record['rows']
        for row in rows:
            assert sum(v*logs[i] for i,v in row.items())%q==0
            group_sum=None
            for i,v in row.items():
                group_sum=add(group_sum,mul(v,points[i],p),p)
            assert group_sum is None
        r=rank(rows,q)
        basis=record['kernel_basis']
        assert r==record['rank_mod_q'] and len(basis)==40-r
        assert rank([{j:x for j,x in enumerate(vector) if x} for vector in basis],q)==len(basis)
        assert all(sum(v*vector[i] for i,v in row.items())%q==0 for row in rows for vector in basis)
        anchor_row={anchor:1}
        assert rank(rows+[anchor_row],q)==record['anchor_coordinate_rank']
        if r==39:
            assert record['normalized_unique_kernel']==logs
        output['checked_families'][name]={'rows':len(rows),'rank_mod_q':r,
                                           'kernel_dimension':40-r,
                                           'group_rows_checked':len(rows),
                                           'anchor_coordinate_rank':record['anchor_coordinate_rank']}
    (HERE/'audit.json').write_text(json.dumps(output,indent=2,sort_keys=True)+'\n')
    print(json.dumps(output['checked_families'],sort_keys=True))


if __name__=='__main__':
    main()
