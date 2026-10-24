"""Compare streamed Hecke identification with existing exact reductions."""
from hashlib import sha256
import json
from pathlib import Path
import sys
from sage.all import GF

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
MODULE=ROOT/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
L13=ROOT/'hecke-l13-closure-20261024/functions.json'
sys.path.insert(0,str(MODULE.parent));sys.path.insert(0,str(HERE))
import hecke11 as H
from modular_hecke_stream import build_mod
def sha(path):return sha256(path.read_bytes()).hexdigest()

def main():
    protocol=json.loads((HERE/'smoke_protocol.v2.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_STREAM_BUILDER_SMOKE'
    sources={'smoke':HERE/'smoke_stream.py','stream_builder':HERE/'modular_hecke_stream.py',
             'hecke11':MODULE,'l13_functions':L13}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    F=GF(20023);checks={}
    for l in (2,3,5):
        rational,_=H.build([l]);streamed,meta=build_mod(l,20023,H)
        assert set(rational)==set(streamed)
        mismatch=[str(tag) for tag,coeff in rational.items()
                  if {ab:F(v) for ab,v in coeff.items()}!=streamed[tag]]
        assert not mismatch
        checks[str(l)]={'functions':len(streamed),'coefficient_mismatches':mismatch,
                        'q_precision':meta['q_precision']}
    l13_saved=json.loads(L13.read_text())['functions']
    streamed,meta=build_mod(13,20023,H)
    encoded={f'{l}:{part}:{k}':{f'{a},{b}':int(v) for (a,b),v in coeff.items()}
             for (l,part,k),coeff in streamed.items()}
    assert encoded==l13_saved
    checks['13']={'functions':len(streamed),'coefficient_mismatches':[],
                  'q_precision':meta['q_precision']}
    out={'status':'PASS_STREAMED_MODULAR_HECKE_REPLAY',
         'protocol_sha256':sha(HERE/'smoke_protocol.v2.json'),
         'smoke_sha256':sha(HERE/'smoke_stream.py'),'checks':checks}
    (HERE/'smoke.v2.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
