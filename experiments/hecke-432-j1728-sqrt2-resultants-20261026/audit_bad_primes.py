"""Direct C and C-E enumeration at every small norm-screen exception."""
import json
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def rational(terms,x,y,p):
    total=0
    for t in terms:
        raw=t['coefficient'];a,b=(map(int,raw.split('/')) if '/' in raw else (int(raw),1))
        total+=a*pow(b,-1,p)*pow(x,t['x_power'],p)*pow(y,t['y_power'],p)
    return total%p


def horner(a,z,p):
    value=0
    for c in reversed(a):value=(value*z+c)%p
    return value


def main():
    rp=HERE/'resultant_norms.json';norms=json.loads(rp.read_text())
    assert norms['status']=='EXACT_CONJUGATE_RESULTANT_NORMS'
    bad=[c for c in norms['bad_primes_below_cap'] if c['class_mod_24']==11]
    cp=ROOT/'experiments/hecke-27-coordinate-bridge-20261025/coordinate_map.json'
    coord=json.loads(cp.read_text())['source_j']
    resolvent_path=ROOT/'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    terms=json.loads(resolvent_path.read_text())['terms']
    cells=[]
    for item in bad:
        p=item['prime'];squares=defaultdict(list)
        for z in range(p):squares[z*z%p].append(z)
        half=pow(2,-1,p);cs=[]
        for x in range(p):
            for z in squares[(4*(x*x*x-7)+1)%p]:
                y=(z-1)*half%p
                den=rational(coord['denominator'],x,y,p)
                if den and -rational(coord['numerator'],x,y,p)*pow(den,-1,p)%p==1728%p:
                    cs.append((x,y))
        rows=[]
        for x,y in cs:
            a=[0]*13
            for t in terms:
                e=t['x_E_exponent']
                a[e]=(a[e]+int(t['integer_coefficient'])*pow(x,t['x_C_exponent'],p)*pow(y,t['y_C_exponent'],p))%p
            roots=[z for z in range(p) if horner(a,z,p)==0]
            pairs=sum(len(squares[(z*z*z+432)%p]) for z in roots)
            rows.append({'C_point':[x,y],'rational_x_E_roots':roots,'rational_CE_pairs':pairs})
        cell={'prime':p,'reasons':item['reasons'],'C_points':len(cs),
              'rational_CE_pairs':sum(r['rational_CE_pairs'] for r in rows),'rows':rows}
        cells.append(cell)
        print(json.dumps({'prime':p,'C_points':len(cs),'rational_CE_pairs':cell['rational_CE_pairs']}),flush=True)
    out={'status':'EXACT_DIRECT_BAD_PRIME_AUDIT',
         'resultant_norms_sha256':sha256(rp.read_bytes()).hexdigest(),
         'coordinate_sha256':sha256(cp.read_bytes()).hexdigest(),
         'resolvent_sha256':sha256(resolvent_path.read_bytes()).hexdigest(),
         'cells':cells}
    (HERE/'bad_prime_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'bad_cells':len(cells),
                      'total_pairs':sum(c['rational_CE_pairs'] for c in cells)}))


if __name__=='__main__':main()
