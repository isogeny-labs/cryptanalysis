"""Frozen exact-source validity sample for W29 and W33."""
import hashlib
import json
import random
import resource
import signal
import time
from pathlib import Path

from sage.all import GF, PolynomialRing

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'sample_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


assert protocol['script_sha256'] == sha(__file__)
for path,digest in protocol['sources'].items():
    assert sha(path) == digest,path
assert not (HERE/'sample_result.json').exists()
signal.signal(signal.SIGALRM,lambda _s,_f: (_ for _ in ()).throw(TimeoutError('sample wall cap')))
signal.alarm(protocol['wall_cap_seconds'])
started=time.monotonic()
P=PolynomialRing(GF(2),'u')
u=P.gen()
K=GF(2**131,name='u',modulus=u**131+u**13+u**2+u+1)
seed=K(P([(1797236>>i)&1 for i in range(131)]))


def valid(code,basis):
    a=K.zero()
    for i,value in enumerate(basis):
        if code>>i&1:
            a+=value
    b=a+seed
    if not a or not b:
        return False
    product=a*b
    inverse=~product
    return (int(a.trace())==0 and int((a*inverse).trace())==0 and
            int((seed*inverse).trace())==0)


def basis_for(width):
    bits=[bit for bit in range(width) if bit!=(898618).bit_length()-1]
    return [K(P([int(i==bit+1) for i in range(131)])) for bit in bits]


rows=[]
for entry in protocol['samples']:
    width=entry['width']
    basis=basis_for(width)
    rng=random.Random(entry['seed'])
    count=entry['draws']
    mask=(1<<len(basis))-1
    successes=0
    digest=hashlib.sha256()
    for _ in range(count):
        code=rng.getrandbits(len(basis))&mask
        result=valid(code,basis)
        successes+=int(result)
        digest.update(code.to_bytes(4,'little'))
        digest.update(bytes((int(result),)))
    rate=successes/count
    rows.append({'width':width,'code_bits':len(basis),'seed':entry['seed'],
                 'draws':count,'valid':successes,'fraction':rate,
                 'ordered_sample_digest_sha256':digest.hexdigest(),
                 'wald_95_halfwidth':1.96*(rate*(1-rate)/count)**0.5})
signal.alarm(0)
exact=json.loads(Path(protocol['w29_exact_census']).read_text())
assert exact['status']=='COMPLETE'
parts=exact['terminal_line'].split()
assert parts[:3]==['PRODUCE','COMPLETE','67109836']
assert int(parts[3])==2*int(parts[2])
result={'status':'PASS_N131_W29_W33_VALIDITY_SAMPLES',
        'candidate_id':None,'rows':rows,
        'w29_exact_valid_codes':int(parts[2]),
        'w29_exact_fraction':int(parts[2])/(1<<28),
        'w29_exact_census_sha256':sha(protocol['w29_exact_census']),
        'wall_seconds':time.monotonic()-started,
        'self_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'protocol_sha256':sha(HERE/'sample_protocol.json')}
(HERE/'sample_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
print(json.dumps(result,sort_keys=True))
