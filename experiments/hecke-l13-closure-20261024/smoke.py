"""Compare finite-field q-series identification with rational coefficients at 2,3,5."""
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF

HERE=Path(__file__).resolve().parent
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent));sys.path.insert(0,str(HERE))
import hecke11 as H
from modular_hecke import build_mod

def sha(path):return sha256(path.read_bytes()).hexdigest()
def main():
    protocol=json.loads((HERE/'smoke_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_MODULAR_BUILDER_SMOKE'
    sources={'smoke':HERE/'smoke.py','modular_hecke':HERE/'modular_hecke.py','hecke11':MODULE}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    F=GF(20023);cases={}
    for l in (2,3,5):
        rational,_=H.build([l]);modular,meta=build_mod(l,20023,H)
        assert set(rational)==set(modular)
        mismatch=[]
        for tag,coeff in rational.items():
            if {ab:F(c) for ab,c in coeff.items()}!=modular[tag]:mismatch.append(str(tag))
        assert not mismatch
        cases[str(l)]={'functions_compared':len(modular),'mismatches':mismatch,
                       'q_precision':meta['q_precision']}
    out={'status':'PASS_MODULAR_HECKE_BUILDER_SMALL_DEGREES',
         'protocol_sha256':sha(HERE/'smoke_protocol.json'),
         'smoke_sha256':sha(HERE/'smoke.py'),'cases':cases}
    (HERE/'smoke.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
