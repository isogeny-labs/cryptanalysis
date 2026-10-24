"""Dense FLINT/finite-field rank audit of the frozen p=12043 row ledger."""
from hashlib import sha256
import json
from pathlib import Path
from sage.all import ZZ, GF, matrix

HERE=Path(__file__).resolve().parent
def sha(p):return sha256(p.read_bytes()).hexdigest()
def main():
    raw=(HERE/'p12043.rank.protocol.json').read_bytes();protocol=json.loads(raw)
    source=HERE/'p12043.result.json';data=json.loads(source.read_text())
    assert protocol['status']=='FROZEN_BEFORE_RANK_AUDIT'
    assert protocol['source_sha256']=={'result':sha(source),'rank_script':sha(HERE/'rank_p12043.py')}
    rows=data['rows'];keys=[tuple(x) for x in data['column_representatives']]
    assert len(rows)==2812 and len(keys)==2320
    index={a:i for i,a in enumerate(keys)}
    entries={(i,int(j)):v for i,row in enumerate(rows) for j,v in row.items()}
    boundaries={name:{index[tuple(x)] for x in values}
                for name,values in data['boundary_representatives'].items()}
    results={}
    for modulus in (None,101,1000000007,13,23):
        F=ZZ if modulus is None else GF(modulus)
        M=matrix(F,len(rows),len(keys),entries,sparse=False)
        full=int(M.rank());part={'full_rank':full}
        for name,keep in boundaries.items():
            discard=sorted(set(range(len(keys)))-keep)
            projected=int(M.matrix_from_columns(discard).rank())
            part[name]={'column_count':len(keep),'discarded_projection_rank':projected,
                        'induced_rank':full-projected}
        results['exact' if modulus is None else str(modulus)]=part
    out={'status':'PASS_DENSE_EXACT_AND_MODULAR_RANKS',
         'protocol_sha256':sha256(raw).hexdigest(),'result_sha256':sha(source),
         'rank_script_sha256':sha(HERE/'rank_p12043.py'),'rank_results':results}
    (HERE/'p12043.rank.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(results,sort_keys=True))

if __name__=='__main__':main()
