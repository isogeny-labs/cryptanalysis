"""Independent curve and branch-equation replay for valid small-prime triples."""
import json
from hashlib import sha256
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def branch_value(terms,c,xe,p):
    x,y=c
    return sum(int(t['integer_coefficient'])*pow(x,t['x_C_exponent'],p)
               *pow(y,t['y_C_exponent'],p)*pow(xe,t['x_E_exponent'],p)
               for t in terms)%p


def main():
    rp=HERE/'branch_result.json';result=json.loads(rp.read_text())
    bp=ROOT/'experiments/hecke-432-b-coordinate-resolvent-20261025/branch_formula.json'
    branch=json.loads(bp.read_text())
    audited=[]
    for cell in result['cells']:
        p=cell['prime']
        for row in cell['rows']:
            x,y=row['C_point'];xe,ye=row['E_point']
            assert (y*y+y-x*x*x+7)%p==0
            assert (ye*ye-xe*xe*xe-432)%p==0
            numerator=branch_value(branch['numerator_terms'],(x,y),xe,p)
            denominator=branch_value(branch['denominator_terms'],(x,y),xe,p)
            if row['status']=='ZERO_DENOMINATOR':
                assert denominator==0 and numerator==row['numerator']
                continue
            assert row['status']=='VALID'
            assert denominator
            xb,yb=row['B_point']
            assert xb==numerator*pow(denominator,-1,p)%p
            assert (yb*yb-xb*xb*xb+16)%p==0
            assert (xb*xb*xb-xe*xb*xb-64)%p==0
            assert (ye*pow(xb,3,p)-yb*(xb**3+128))%p==0
            audited.append({'prime':p,'C_point':[x,y],'E_point':[xe,ye],'B_point':[xb,yb]})
    assert len(audited)==4 and {r['prime'] for r in audited}=={131}
    out={'status':'PASS_INDEPENDENT_VALID_BRANCH_REPLAY',
         'branch_result_sha256':sha256(rp.read_bytes()).hexdigest(),
         'branch_formula_sha256':sha256(bp.read_bytes()).hexdigest(),
         'valid_triples':audited}
    (HERE/'branch_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'valid_triples':len(audited)}))


if __name__=='__main__':main()
