"""Checked-Sage prospective inert-2 class with non-three cycle order."""
from hashlib import sha256
import json
from math import isqrt
from pathlib import Path

from sage.all import is_prime, pari

HERE=Path(__file__).resolve().parent

def squarefree(n):
    return all(n%(k*k) for k in range(2,isqrt(n)+1))

def first_prime(d):
    upper=250000-9*d
    if upper<1:return None
    for v in range(1,isqrt(upper)+1):
        p=v*v+9*d
        if 10000<=p<=250000 and p not in (2,3,5,11) and is_prime(p):
            return v,int(p)
    return None

def form_order(d,h2):
    q=pari.qfbprimeform(-4*d,3)
    identity=pari.qfbpow(q,0)
    for k in range(1,h2+1):
        if h2%k==0 and pari.qfbpow(q,k)==identity:
            return k,str(q),str(identity)
    raise AssertionError((d,h2))

def main():
    raw=(HERE/'selection_protocol.json').read_bytes()
    protocol=json.loads(raw)
    assert protocol['status']=='FROZEN_BEFORE_NON3_CYCLE_SELECTION'
    squares={x*x%11 for x in range(1,11)}
    inspected=[];chosen=None
    for d in range(35,10001):
        if d%24!=11 or not squarefree(d):continue
        h1=int(pari.qfbclassno(-d))
        h2=int(pari.qfbclassno(-4*d))
        h3=int(pari.qfbclassno(-9*d))
        h6=int(pari.qfbclassno(-36*d))
        residue=(-36*d)%11
        row={'d':d,'h1':h1,'h2':h2,'h3':h3,'h6':h6,
             'frobenius_discriminant_mod_11':residue}
        inspected.append(row)
        if not(4<=h1<=20 and h2==3*h1 and h3==2*h1 and h6==6*h1 and
               residue in squares):continue
        order,form,identity=form_order(d,h2)
        row.update({'norm3_form':form,'principal_form':identity,'norm3_order_at_conductor2':order})
        if order%3==0:continue
        prime=first_prime(d)
        if prime is None:continue
        v,p=prime
        row.update({'v':v,'p':p,'u_abs':2*v})
        assert (2*v)**2-4*p==-36*d
        chosen=row;break
    result={'status':'NON3_CYCLE_HOLDOUT_SELECTED' if chosen else 'NO_ELIGIBLE_CLASS_IN_BOUND',
            'selection_protocol_sha256':sha256(raw).hexdigest(),
            'script_sha256':sha256((HERE/'select.py').read_bytes()).hexdigest(),
            'inspected':inspected,'inspected_count':len(inspected),'chosen':chosen,
            'candidate_id':None,'timing_claim':None}
    (HERE/'selection.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('status','inspected_count','chosen')},sort_keys=True))

if __name__=='__main__':main()
