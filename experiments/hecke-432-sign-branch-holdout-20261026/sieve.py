"""Frozen source-free search for a nonzero-T-derivative B sign branch."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def is_prime(n):
    if n<2: return False
    for d in range(2,int(n**0.5)+1):
        if n%d==0: return False
    return True


def main():
    protocol_path=HERE/'sieve_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_SIGN_BRANCH_SIEVE'
    for name,record in protocol['inputs'].items():
        assert sha256(Path(record['path']).read_bytes()).hexdigest()==record['sha256'],name
    inverse=load('sign_inverse',protocol['inputs']['inverse_filter']['path'])
    gradient=load('sign_gradient',protocol['inputs']['gradient']['path'])
    resolvent=json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    branch=json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    terms=json.loads(Path(protocol['inputs']['b_resolvent']['path']).read_text())['terms']
    cells=[]
    selected=None
    for p in range(1280,protocol['prime_cap_exclusive']):
        if not is_prime(p): continue
        xs=[x for x in range(1,p) if pow(x,3,p)==16%p]
        if not xs: continue
        special=[((x,0),((-48)*pow(x*x,-1,p)%p,0)) for x in xs]
        hits=[]
        c_points=inverse.curve_points(p,'C')
        for c in c_points:
            coeffs=inverse.resolvent_coefficients(resolvent['terms'],c,p)
            for b,e in special:
                if inverse.horner(coeffs,e[0],p): continue
                value=inverse.evaluate_pair(c,e,p,resolvent,branch)
                if value['status']!='VALID' or value['B_point']!=list(b): continue
                v,dt,dc,db=gradient.gradients(terms,c,b,p)
                assert v==db==0
                hits.append({'C_point':list(c),'E_point':list(e),'B_point':list(b),'dT':dt,'dC':dc,'selected_condition':dc==0 and dt!=0})
        chosen=[h for h in hits if h['selected_condition']]
        cell={'prime':p,'B_two_torsion_points':len(special),'C_group_order':len(c_points)+1,
              'valid_sign_branch_triples':len(hits),'nonzero_T_critical_triples':len(chosen),
              'hits':hits}
        cells.append(cell)
        print(json.dumps({'prime':p,'valid':len(hits),'critical_nonzero_T':len(chosen)}),flush=True)
        if chosen:
            selected=p
            break
    out={'status':'SELECTED_SIGN_BRANCH_PRIME' if selected else 'BOUNDED_NO_SIGN_BRANCH_PRIME',
         'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
         'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'selected_prime':selected,'cells':cells}
    (HERE/'sieve_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'selected_prime':selected,'cells':len(cells)}))


if __name__=='__main__': main()
