"""Select the first eight fresh prime-order fields under the frozen rule."""
import hashlib
import json
from pathlib import Path
from sage.all import EllipticCurve, GF, prime_range, is_prime

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
protocol=json.loads((HERE/'protocol.json').read_text())
family=json.loads((HERE/'family-selection.json').read_text())
assert family['protocol_sha256']==sha(HERE/'protocol.json')
checked=[];selected=[]
for p in prime_range(1501,10001):
    E=EllipticCurve(GF(p),[-1,-2]);G=E(2,2)
    q=int(E.cardinality())
    prime=bool(is_prime(q))
    checked.append({'p':int(p),'q':q,'prime_order':prime})
    if prime and not G.is_zero():
        assert int(G.order())==q
        selected.append([int(p),q])
        if len(selected)==8:break
assert len(selected)==8
print(json.dumps({'schema':'xedni-coefficient-optimization-fields-v1','status':'PASS',
                  'protocol_sha256':sha(HERE/'protocol.json'),
                  'family_selection_sha256':sha(HERE/'family-selection.json'),
                  'source_sha256':sha(Path(__file__)),
                  'checked':checked,'selected':selected},sort_keys=True,indent=2))
