"""Independent prime-field point counts for the j=-121 census."""
from hashlib import sha256
from pathlib import Path
import json

P=Path(__file__).resolve().parent
SHA=lambda q:sha256(q.read_bytes()).hexdigest()

def trace_abs(p):
    j=(-121)%p
    assert j not in (0,1728%p) and p>3
    k=j*pow((j-1728)%p,-1,p)%p
    a=(-3*k)%p;b=(-2*k)%p
    denom=(4*pow(a,3,p)+27*pow(b,2,p))%p
    assert denom and 1728*4*pow(a,3,p)*pow(denom,-1,p)%p==j
    character_sum=0
    for x in range(p):
        value=(x*x*x+a*x+b)%p
        if value:
            symbol=pow(value,(p-1)//2,p)
            assert symbol in (1,p-1)
            character_sum+=1 if symbol==1 else -1
    return abs(character_sum)

def main():
    gate=json.loads((P/'validation_protocol.json').read_text())
    assert gate['status']=='FROZEN_BEFORE_INDEPENDENT_TRACE_REPLAY'
    assert gate['script_sha256']==SHA(P/'validate_trace.py')
    assert gate['census_sha256']==SHA(P/'RESULT.json')
    census=json.loads((P/'RESULT.json').read_text())
    rows=[]
    for text,record in sorted(census['prime_facts'].items(),key=lambda item:int(item[0])):
        p=int(text);observed=trace_abs(p)
        rows.append({'p':p,'sage_trace_abs':record['trace_abs'],
                     'independent_trace_abs':observed,'match':observed==record['trace_abs']})
    status='PASS_19_PRIME_TRACE_REPLAY' if len(rows)==19 and all(r['match'] for r in rows) else 'TRACE_REPLAY_MISMATCH'
    result={'status':status,'protocol_sha256':SHA(P/'validation_protocol.json'),
            'census_sha256':SHA(P/'RESULT.json'),
            'script_sha256':SHA(P/'validate_trace.py'),'rows':rows}
    (P/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':status,'primes':len(rows),'mismatches':[r['p'] for r in rows if not r['match']]}))

if __name__=='__main__':main()
