"""Independent trace replay for nine external census primes."""
from hashlib import sha256
from pathlib import Path
import json

from sage.all import pari

P=Path(__file__).resolve().parent
SHA=lambda q:sha256(q.read_bytes()).hexdigest()

def trace_by_character_sum(p,a,b):
    s=0
    for x in range(p):
        v=(x*x*x+a*x+b)%p
        if v:
            z=pow(v,(p-1)//2,p)
            assert z in (1,p-1)
            s+=1 if z==1 else -1
    return -s

def trace_by_pari(p,a,b):
    E=pari.ellinit([0,0,0,a,b],p)
    return p+1-int(pari.ellcard(E))

def main():
    gate=json.loads((P/'external_validation_protocol.json').read_text())
    assert gate['status']=='FROZEN_BEFORE_EXTERNAL_TRACE_REPLAY'
    assert gate['script_sha256']==SHA(P/'external_validate.py')
    assert gate['census_sha256']==SHA(P/'external_result.json')
    census=json.loads((P/'external_result.json').read_text())
    rows=[]
    for text,fact in sorted(census['prime_facts'].items(),key=lambda item:int(item[0])):
        p=int(text);j=(-121)%p
        k=j*pow((j-1728)%p,-1,p)%p
        a=(-3*k)%p;b=(-2*k)%p
        denom=(4*pow(a,3,p)+27*pow(b,2,p))%p
        assert denom and 1728*4*pow(a,3,p)*pow(denom,-1,p)%p==j
        if p<=100000:
            trace=trace_by_character_sum(p,a,b);method='character_sum'
        else:
            trace=trace_by_pari(p,a,b);method='pari_ellcard'
        rows.append({'p':p,'method':method,'independent_trace':trace,
                     'sage_trace_abs':fact['trace_abs'],
                     'match':abs(trace)==fact['trace_abs']})
    status='PASS_NINE_EXTERNAL_PRIME_TRACE_REPLAY' if len(rows)==9 and all(r['match'] for r in rows) else 'EXTERNAL_TRACE_REPLAY_MISMATCH'
    result={'status':status,'protocol_sha256':SHA(P/'external_validation_protocol.json'),
            'census_sha256':SHA(P/'external_result.json'),
            'script_sha256':SHA(P/'external_validate.py'),'rows':rows}
    (P/'external_validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':status,'primes':len(rows),'mismatches':[r['p'] for r in rows if not r['match']]}))

if __name__=='__main__':main()
