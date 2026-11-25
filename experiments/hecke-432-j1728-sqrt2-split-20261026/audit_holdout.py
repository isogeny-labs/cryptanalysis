"""Independent exhaustive x_E replay for the fresh sqrt2 holdout."""
import json
from hashlib import sha256
from pathlib import Path

from sympy import isprime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def rational(terms,x,y,p):
    result=0
    for t in terms:
        raw=t['coefficient'];a,b=(map(int,raw.split('/')) if '/' in raw else (int(raw),1))
        result+=a*pow(b,-1,p)*pow(x,t['x_power'],p)*pow(y,t['y_power'],p)
    return result%p


def main():
    pp=HERE/'holdout_protocol.json';protocol=json.loads(pp.read_text())
    sp=HERE/'holdout_selection.json';selection=json.loads(sp.read_text())
    tp=HERE/'holdout_result.json';result=json.loads(tp.read_text())
    assert selection['protocol_sha256']==sha256(pp.read_bytes()).hexdigest()
    assert result['selection_sha256']==sha256(sp.read_bytes()).hexdigest()
    cp=Path(protocol['inputs']['coordinate']['path'])
    coord=json.loads(cp.read_text())['source_j']
    rp=ROOT/'experiments/hecke-432-relative-resolvent-20261025/relative_resolvent.json'
    assert result['resolvent_sha256']==sha256(rp.read_bytes()).hexdigest()
    terms=json.loads(rp.read_text())['terms']
    rows=[];tested=0
    for cell in selection['selected']:
        p=cell['prime'];assert isprime(p) and p%24==11
        for x,y in cell['C_points']:
            assert (y*y+y-x*x*x+7)%p==0
            den=rational(coord['denominator'],x,y,p)
            assert den and -rational(coord['numerator'],x,y,p)*pow(den,-1,p)%p==1728%p
            a=[0]*13
            for t in terms:
                e=t['x_E_exponent']
                a[e]=(a[e]+int(t['integer_coefficient'])*pow(x,t['x_C_exponent'],p)*pow(y,t['y_C_exponent'],p))%p
            assert a[12]
            roots=[]
            for z in range(p):
                value=0
                for c in reversed(a):value=(value*z+c)%p
                if value==0:roots.append(z)
            assert not roots
            tested+=p
            rows.append({'prime':p,'C_point':[x,y],'exhaustive_x_E_candidates':p,
                         'rational_resolvent_x_E_roots':0})
    assert len(rows)==6 and result['status']=='PASS_PROSPECTIVE_SQRT2_FROBENIUS_HOLDOUT'
    out={'status':'PASS_INDEPENDENT_EXHAUSTIVE_HOLDOUT_AUDIT',
         'protocol_sha256':sha256(pp.read_bytes()).hexdigest(),
         'selection_sha256':sha256(sp.read_bytes()).hexdigest(),
         'holdout_result_sha256':sha256(tp.read_bytes()).hexdigest(),
         'resolvent_sha256':sha256(rp.read_bytes()).hexdigest(),
         'total_x_E_candidates':tested,'rows':rows}
    (HERE/'holdout_audit.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'rows':len(rows),'total_x_E_candidates':tested}))


if __name__=='__main__':main()
