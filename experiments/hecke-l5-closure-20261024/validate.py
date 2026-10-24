"""Independent exhaustive degree-5 root-splitting audit of the saved sources."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

from sage.all import EllipticCurve, GF

HERE=Path(__file__).resolve().parent
MODULE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'
sys.path.insert(0,str(MODULE.parent))
import hecke11 as H

def sha(path):return sha256(path.read_bytes()).hexdigest()
def key(P):return (-1,-1) if P.is_zero() else (int(P[0]),int(P[1]))

def main():
    protocol=json.loads((HERE/'validation_protocol.json').read_text())
    assert protocol['status']=='FROZEN_BEFORE_L5_VALIDATOR'
    sources={'validator':HERE/'validate.py','result':HERE/'result.json','hecke11':MODULE}
    assert protocol['source_sha256']=={name:sha(path) for name,path in sources.items()}
    data=json.loads(sources['result'].read_text())
    funcs,jfun=H.build([5]);rd=H.Reduced(20023,funcs,jfun,[5])
    T=rd.E([5,5,1]);assert 5*T==rd.E(0)
    keys=[tuple(x) for x in data['all_column_representatives']]
    assert len(keys)==3949 and not data['new_representatives'] and not data['accepted_rows']
    expected={tuple(rec['source']):rec for rec in data['attempts']}
    assert len(expected)==data['source_point_count']==19745
    statuses=Counter();root_multiplicity=Counter()
    for rep in keys:
        P0=rd.E(0) if rep==(-1,-1) else rd.E([rep[0],rep[1],1])
        for k in range(5):
            P=P0+k*T
            saved=expected[key(P)]
            if rd.j(P) is None:
                assert saved['status']=='SOURCE_UNDEFINED_J'
                statuses['SOURCE_UNDEFINED_J']+=1
                continue
            roots=rd.neighbour_x(5,P).roots()
            multiplicity=sum(int(m) for _,m in roots)
            root_multiplicity[multiplicity]+=1
            assert multiplicity<6 and saved['status']=='NOT_ALL_RATIONAL'
            statuses['NOT_ALL_RATIONAL']+=1
    assert dict(statuses)==data['status_counts']
    assert 20023%5==3 and {a*a%5 for a in range(5)}=={0,1,4}
    out={'status':'PASS_EXHAUSTIVE_L5_ROOT_SPLITTING_AUDIT',
         'protocol_sha256':sha(HERE/'validation_protocol.json'),
         'result_sha256':sha(HERE/'result.json'),
         'validator_sha256':sha(HERE/'validate.py'),
         'source_points_checked':len(expected),'status_counts':dict(statuses),
         'rational_root_multiplicity_histogram':dict(root_multiplicity),
         'determinant_residue_mod5':3,'square_residues_mod5':[0,1,4]}
    (HERE/'validation.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))

if __name__=='__main__':main()
