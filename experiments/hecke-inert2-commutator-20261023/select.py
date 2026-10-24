"""Checked-Sage first-eligible inert-2, split-3, split-11 CM holdout."""
from hashlib import sha256
import json
from math import isqrt
from pathlib import Path

from sage.all import is_prime, pari

HERE=Path(__file__).resolve().parent


def squarefree(n):
    return all(n%(k*k) for k in range(2,isqrt(n)+1))


def first_prime(d):
    upper=120000-9*d
    if upper<1:return None
    for v in range(1,isqrt(upper)+1):
        p=v*v+9*d
        if 10000<=p<=120000 and p not in (2,3,5,11) and is_prime(p):
            return v,int(p)
    return None


def main():
    raw=(HERE/'selection_protocol.json').read_bytes()
    protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_INERT2_SELECTION'
    squares={x*x%11 for x in range(1,11)}
    inspected=[]; chosen=None
    for d in range(35,6001):
        if d%24!=11 or not squarefree(d):continue
        h1=int(pari.qfbclassno(-d))
        h2=int(pari.qfbclassno(-4*d))
        h3=int(pari.qfbclassno(-9*d))
        h6=int(pari.qfbclassno(-36*d))
        residue=(-36*d)%11
        row={'d':d,'h1':h1,'h2':h2,'h3':h3,'h6':h6,
             'frobenius_discriminant_mod_11':residue}
        inspected.append(row)
        if not(h1<=30 and h2==3*h1 and h3==2*h1 and h6==6*h1 and
               residue in squares):continue
        prime=first_prime(d)
        if prime is None:continue
        v,p=prime
        row.update({'v':v,'p':p,'u_abs':2*v})
        assert (2*v)**2-4*p==-36*d
        chosen=row;break
    result={'status':'INERT2_HOLDOUT_SELECTED' if chosen else 'NO_ELIGIBLE_CLASS',
            'selection_protocol_sha256':sha256(raw).hexdigest(),
            'script_sha256':sha256((HERE/'select.py').read_bytes()).hexdigest(),
            'inspected':inspected,'inspected_count':len(inspected),'chosen':chosen,
            'candidate_id':None,'timing_claim':None}
    (HERE/'selection.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','inspected_count','chosen')},sort_keys=True))


if __name__=='__main__':main()
