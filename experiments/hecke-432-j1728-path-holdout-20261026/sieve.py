"""Frozen source-free search for a two-sheet j=1728 prime."""
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


def prime(n):
    return n>=2 and all(n%d for d in range(2,int(n**0.5)+1))


def rational_at(terms,c,p):
    x,y=c
    total=0
    for term in terms:
        s=term['coefficient']
        a,b=(map(int,s.split('/')) if '/' in s else (int(s),1))
        total+=a*pow(b,-1,p)*pow(x,term['x_power'],p)*pow(y,term['y_power'],p)
    return total%p


def source_j(record,c,p):
    den=rational_at(record['denominator'],c,p)
    if den==0:return None
    return -rational_at(record['numerator'],c,p)*pow(den,-1,p)%p


def main():
    protocol_path=HERE/'sieve_protocol.json'
    protocol=json.loads(protocol_path.read_text())
    assert protocol['status']=='FROZEN_BEFORE_J1728_SOURCE_FREE_PRIME_SIEVE'
    for name,rec in protocol['inputs'].items():
        assert sha256(Path(rec['path']).read_bytes()).hexdigest()==rec['sha256'],name
    inverse=load('j1728_inverse',protocol['inputs']['inverse_filter']['path'])
    resolvent=json.loads(Path(protocol['inputs']['resolvent']['path']).read_text())
    branch=json.loads(Path(protocol['inputs']['branch']['path']).read_text())
    coordinate=json.loads(Path(protocol['inputs']['coordinate']['path']).read_text())
    cells=[];selected=None
    for p in range(1320,protocol['prime_cap_exclusive']):
        if p%24!=23 or not prime(p):continue
        cs=[c for c in inverse.curve_points(p,'C') if source_j(coordinate['source_j'],c,p)==1728%p]
        es=inverse.curve_points(p,'E')
        rows=[]
        for c in cs:
            coeffs=inverse.resolvent_coefficients(resolvent['terms'],c,p)
            for e in es:
                if inverse.horner(coeffs,e[0],p):continue
                value=inverse.evaluate_pair(c,e,p,resolvent,branch)
                rows.append({'C_point':list(c),'E_point':list(e),**value})
        valid=[r for r in rows if r['status']=='VALID']
        cell={'prime':p,'j1728_C_points':[list(c) for c in cs],
              'resolvent_pairs':len(rows),'valid_triples':len(valid),
              'distinct_valid_C_points':len({tuple(r['C_point']) for r in valid}),
              'rows':rows}
        cells.append(cell)
        print(json.dumps({'prime':p,'C_points':len(cs),'valid':len(valid),
                          'distinct_valid_C':cell['distinct_valid_C_points']}),flush=True)
        if len(valid)>=4 and cell['distinct_valid_C_points']>=2:
            selected=p;break
    result={'status':'SELECTED_J1728_TWO_SHEET_PRIME' if selected else 'BOUNDED_NO_J1728_TWO_SHEET_PRIME',
            'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
            'source_code_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
            'selected_prime':selected,'cells':cells}
    (HERE/'sieve_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'selected_prime':selected,'cells':len(cells)}))


if __name__=='__main__':main()
