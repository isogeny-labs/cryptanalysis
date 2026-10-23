"""Select a split-3 CM class whose norm-3 order is below its class number."""
from math import isqrt
import hashlib
import json
from pathlib import Path

from sage.all import BinaryQF,is_prime,pari

HERE=Path(__file__).resolve().parent


def squarefree(n):
    return all(n%(k*k) for k in range(2,isqrt(n)+1))


def first_prime(d):
    for v in range(1,isqrt(120000-9*d)+1):
        p=v*v+9*d
        if 10000<=p<=120000 and is_prime(p) and p not in (2,3,5,11):
            return v,p
    return None


def main():
    raw=(HERE/'selection_protocol.json').read_bytes()
    assert json.loads(raw)['status']=='FROZEN_BEFORE_SMALL_ORDER_CLASS_SELECTION'
    squares={x*x%11 for x in range(1,11)}
    inspected=[]
    chosen=None
    for d in range(1056,6001):
        if d%24!=23 or not squarefree(d):continue
        h1=int(pari.qfbclassno(-d))
        h2=int(pari.qfbclassno(-4*d))
        h3=int(pari.qfbclassno(-9*d))
        norm3=BinaryQF(3,2,(d+1)//3)
        assert int(norm3.discriminant())==-4*d
        o3=int(norm3.form_class().order())
        residue=(-36*d)%11
        row={'d':d,'h1':h1,'h2':h2,'h3':h3,
             'norm3_order_f2':o3,'frobenius_discriminant_mod_11':residue}
        inspected.append(row)
        if (h2!=h1 or h3!=2*h1 or h1>80 or not 3<=o3<h2 or
            h2%o3!=0 or residue not in squares):continue
        prime=first_prime(d)
        if prime is None:continue
        v,p=prime
        row.update({'v':v,'p':p,'u_abs':2*v,
                    'conductor2_points_predicted':2*h2,
                    'separate_cycle_count_predicted':2*h2//o3,
                    'separate_cycle_length_predicted':o3,
                    'sheet_swap_cycle_count_predicted':h2//o3,
                    'sheet_swap_cycle_length_predicted':2*o3})
        assert (2*v)**2-4*p==-36*d
        chosen=row
        break
    result={'status':'FROZEN_SMALL_ORDER_HOLDOUT_SELECTED' if chosen else 'NO_CLASS_IN_BOUND',
            'protocol_sha256':hashlib.sha256(raw).hexdigest(),
            'inspected_discriminants':len(inspected),'rows':inspected,'chosen':chosen,
            'script_sha256':hashlib.sha256((HERE/'select.py').read_bytes()).hexdigest()}
    (HERE/'selection.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},sort_keys=True))


if __name__=='__main__':main()
