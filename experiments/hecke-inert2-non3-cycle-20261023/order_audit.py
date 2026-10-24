"""Independent checked-Sage receipt for the norm-3 form order."""
from hashlib import sha256
import json
from pathlib import Path

from sage.all import is_prime, pari

HERE=Path(__file__).resolve().parent

def main():
    selected=json.loads((HERE/'selection.json').read_text())
    row=selected['chosen']
    d,p,v=(row[k] for k in ('d','p','v'))
    assert (d,p,v)==(227,12043,100)
    assert is_prime(p) and 4*v*v-4*p==-36*d
    D=-4*d
    form=pari.qfbprimeform(D,3)
    identity=pari.qfbpow(form,0)
    powers=[{'exponent':k,'reduced_form':str(pari.qfbpow(form,k)),
             'principal':bool(pari.qfbpow(form,k)==identity)} for k in range(1,16)]
    assert [r['exponent'] for r in powers if r['principal']]==[5,10,15]
    out={'status':'NORM3_ORDER_FIVE_IN_CONDUCTOR2_CLASS_GROUP',
         'discriminant':D,'class_number':int(pari.qfbclassno(D)),
         'form':str(form),'principal_form':str(identity),'order':5,
         'powers':powers,'selection_sha256':sha256((HERE/'selection.json').read_bytes()).hexdigest(),
         'script_sha256':sha256((HERE/'order_audit.py').read_bytes()).hexdigest(),
         'candidate_id':None,'timing_claim':None}
    assert out['class_number']==15
    (HERE/'order_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'order':out['order']},sort_keys=True))

if __name__=='__main__':main()
