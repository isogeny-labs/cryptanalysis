"""Select a high-density, two-prime floor-cycle class under a frozen rule."""
from math import isqrt
import hashlib
import json
from pathlib import Path

from sage.all import BinaryQF, is_prime, pari

HERE=Path(__file__).resolve().parent


def squarefree(n):
    return all(n%(k*k) for k in range(2,isqrt(n)+1))


def first_prime(d):
    for v in range(1,isqrt(80000-9*d)+1):
        p=v*v+9*d
        if p>=10000 and p<=80000 and is_prime(p) and p not in (2,3,5,11):
            return v,p
    return None


def better(candidate,incumbent):
    if incumbent is None:return True
    lhs=candidate['floor_rank_predicted']*incumbent['floor_point_count_predicted']
    rhs=incumbent['floor_rank_predicted']*candidate['floor_point_count_predicted']
    return lhs>rhs or (lhs==rhs and (candidate['floor_rank_predicted']>incumbent['floor_rank_predicted'] or
        (candidate['floor_rank_predicted']==incumbent['floor_rank_predicted'] and candidate['d']<incumbent['d'])))


def main():
    raw=(HERE/'selection_protocol.json').read_bytes()
    assert json.loads(raw)['status']=='FROZEN_BEFORE_HIGH_DENSITY_CLASS_SELECTION'
    squares={x*x%11 for x in range(1,11)}
    inspected,eligible,chosen=[],[],None
    for d in range(624,3001):
        if d%24!=23 or not squarefree(d):continue
        h1=int(pari.qfbclassno(-d))
        h2=int(pari.qfbclassno(-4*d))
        h3=int(pari.qfbclassno(-9*d))
        f2=BinaryQF(2,1,(1+9*d)//8)
        f3=BinaryQF(3,2,(d+1)//3)
        assert (int(f2.discriminant()),int(f3.discriminant()))==(-9*d,-4*d)
        o2,o3=int(f2.form_class().order()),int(f3.form_class().order())
        assert 2*h3%o2==0 and 2*h2%o3==0
        k2=2*h3//o2
        k3=2*(2*h2//o3) if o3%3==0 else 0
        residue=(-36*d)%11
        row={'d':d,'h1':h1,'h2':h2,'h3':h3,'norm2_order_f3':o2,
             'norm3_order_f2':o3,'frobenius_discriminant_mod_11':residue,
             'degree2_directions_predicted':k2,'degree3_directions_predicted':k3,
             'floor_rank_predicted':k2+k3,'floor_point_count_predicted':4*h1}
        inspected.append(row)
        if h2!=h1 or h3!=2*h1 or h1>40 or o3%3!=0 or residue not in squares or k2<2 or k3<2:
            continue
        prime=first_prime(d)
        if prime is None:continue
        v,p=prime
        row.update({'v':v,'p':p,'u_abs':2*v})
        assert (2*v)**2-4*p==-36*d
        eligible.append(row)
        if better(row,chosen):chosen=row
    result={'status':'FROZEN_HIGH_DENSITY_HOLDOUT_SELECTED' if chosen else 'NO_CLASS_IN_BOUND',
            'protocol_sha256':hashlib.sha256(raw).hexdigest(),
            'inspected_discriminants':len(inspected),'eligible_classes':len(eligible),
            'rows':inspected,'chosen':chosen,
            'script_sha256':hashlib.sha256((HERE/'select.py').read_bytes()).hexdigest()}
    (HERE/'selection.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},sort_keys=True))


if __name__=='__main__':main()
