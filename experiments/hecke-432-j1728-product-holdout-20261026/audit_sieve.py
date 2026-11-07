"""Independent rational-point and polynomial replay of the p1439 selection."""
import importlib.util
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prime(n):
    return n>=2 and all(n%d for d in range(2,int(n**0.5)+1))


def poly_at(terms,c,xe,p):
    x,y=c
    return sum(int(t['integer_coefficient'])*pow(x,t['x_C_exponent'],p)*pow(y,t['y_C_exponent'],p)*pow(xe,t['x_E_exponent'],p) for t in terms)%p


def main():
    protocol_path=HERE/'sieve_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    result=json.loads((HERE/'sieve_result.json').read_text())
    assert result['protocol_sha256']==sha256(protocol_path.read_bytes()).hexdigest()
    assert result['source_code_sha256']==sha256((HERE/'sieve.py').read_bytes()).hexdigest()
    for rec in protocol['inputs'].values():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    deps=json.loads((HERE/'audit_dependencies.json').read_text())
    for rec in deps.values():assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256']
    arithmetic=load('independent_curve_arithmetic',deps['prior_certificate_audit']['path'])
    eligible=[p for p in range(1368,result['selected_prime']+1) if p%24==23 and prime(p)]
    assert eligible==[c['prime'] for c in result['cells']]==[1439]
    coord=json.loads(Path(protocol['inputs']['coordinate']['path']).read_text())
    resolvent=json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    branch=json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    for cell in result['cells']:
        p=cell['prime'];arithmetic.P=p
        cs=[c for c in arithmetic.curve_points('C') if arithmetic.j_value(coord['source_j'],c)==1728%p]
        assert [list(c) for c in cs]==cell['j1728_C_points']
        es=arithmetic.curve_points('E')
        rows=[]
        for c in cs:
            for e in es:
                xe,ye=e
                if poly_at(resolvent['terms'],c,xe,p):continue
                numerator=poly_at(branch['numerator_terms'],c,xe,p)
                denominator=poly_at(branch['denominator_terms'],c,xe,p)
                if denominator==0:
                    result_row={'status':'ZERO_DENOMINATOR','numerator':numerator}
                else:
                    xb=numerator*pow(denominator,-1,p)%p
                    yden=(xb**3+128)%p
                    if xb==0 or yden==0:
                        result_row={'status':'Y_INVERSE_UNDEFINED','x_B':xb}
                    else:
                        yb=ye*pow(xb,3,p)*pow(yden,-1,p)%p
                        if (yb*yb-xb**3+16)%p or (xb**3-xe*xb*xb-64)%p:
                            result_row={'status':'BRANCH_EQUATION_FAILURE','B_point':[xb,yb]}
                        else:
                            result_row={'status':'VALID','B_point':[xb,yb]}
                rows.append({'C_point':list(c),'E_point':list(e),**result_row})
        assert rows==cell['rows']
        valid=[r for r in rows if r['status']=='VALID']
        assert len(rows)==cell['resolvent_pairs'] and len(valid)==cell['valid_triples']
        assert len({tuple(r['C_point']) for r in valid})==cell['distinct_valid_C_points']
    out={'status':'PASS_INDEPENDENT_J1728_PRIME_SIEVE_AUDIT',
         'selected_prime':result['selected_prime'],'eligible_primes':eligible,
         'j1728_valid_triples':result['cells'][-1]['valid_triples'],
         'status_histogram':dict(Counter(r['status'] for r in result['cells'][-1]['rows'])),
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest()}
    (HERE/'sieve_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
