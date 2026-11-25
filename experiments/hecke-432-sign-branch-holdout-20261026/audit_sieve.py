"""Independent p1280..p1319 sign-branch selection audit."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def is_prime(n):
    if n<2:return False
    return all(n%d for d in range(2,int(n**0.5)+1))


def at(terms,c,t,p):
    x,y=c
    return sum(int(r['integer_coefficient'])*pow(x,r['x_C_exponent'],p)*pow(y,r['y_C_exponent'],p)*pow(t,r['x_E_exponent'],p) for r in terms)%p


def main():
    protocol_path=HERE/'sieve_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    result=json.loads((HERE/'sieve_result.json').read_text())
    assert result['protocol_sha256']==sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256']==sha256((HERE/'sieve.py').read_bytes()).hexdigest()
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    dep=json.loads((HERE/'audit_dependencies.json').read_text())
    for rec in dep.values():assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    math=load('audited_finite_math',dep['prior_certificate_audit']['path'])
    dual=load('audited_dual_math',dep['dual_gradient_audit']['path'])
    resolvent=json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())['terms']
    branch=json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    bterms=json.loads(Path(protocol['inputs']['b_resolvent']['path']).read_text())['terms']
    eligible=[]
    for p in range(1280,result['selected_prime']+1):
        if is_prime(p) and any(pow(x,3,p)==16%p for x in range(1,p)):
            eligible.append(p)
    assert eligible==[cell['prime'] for cell in result['cells']]
    all_hits=[]
    for cell in result['cells']:
        p=cell['prime']; math.P=p
        c_points=math.curve_points('C')
        xs=[x for x in range(1,p) if pow(x,3,p)==16%p]
        assert len(xs)==cell['B_two_torsion_points']
        hits=[]
        for c in c_points:
            for x in xs:
                e=((-48)*pow(x*x,-1,p)%p,0)
                if (e[0]**3+432)%p:continue
                if at(resolvent,c,e[0],p):continue
                num=at(branch['numerator_terms'],c,e[0],p)
                den=at(branch['denominator_terms'],c,e[0],p)
                if not den:continue
                bx=num*pow(den,-1,p)%p
                if bx!=x or (bx**3+128)%p==0:continue
                assert (bx**3-16)%p==0
                value_t,dt=dual.dual_value(bterms,c,bx,p,'T')
                value_c,dc=dual.dual_value(bterms,c,bx,p,'C')
                assert value_t==value_c==0
                hits.append({'C_point':list(c),'E_point':list(e),'B_point':[x,0],
                             'dT':dt,'dC':dc,'selected_condition':dc==0 and dt!=0})
        hits.sort(key=lambda h:(h['C_point'],h['B_point']))
        observed=sorted(cell['hits'],key=lambda h:(h['C_point'],h['B_point']))
        assert hits==observed
        assert len(hits)==cell['valid_sign_branch_triples']
        assert sum(h['selected_condition'] for h in hits)==cell['nonzero_T_critical_triples']
        all_hits.extend(hits)
    assert result['selected_prime']==1319
    assert all(c['nonzero_T_critical_triples']==0 for c in result['cells'][:-1])
    assert result['cells'][-1]['nonzero_T_critical_triples']==4
    out={'status':'PASS_INDEPENDENT_SIGN_BRANCH_SIEVE_AUDIT',
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
         'eligible_primes':eligible,'valid_hits':len(all_hits),
         'selected_prime':result['selected_prime'],
         'selected_critical_hits':result['cells'][-1]['nonzero_T_critical_triples']}
    (HERE/'sieve_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
