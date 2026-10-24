"""Independent small-prime point count for the frozen X0(11) Hecke eigenvalues."""
import ast
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'hecke-two-sheet-small-order-20261023/tools/hecke11.py'


def main():
    raw=SOURCE.read_bytes()
    module=ast.parse(raw)
    models=[ast.literal_eval(node.value) for node in module.body
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='AINV'
                                                for t in node.targets)]
    assert models==[[0,-1,1,-10,-20]]
    counts={}
    for ell in (2,3):
        count=1+sum((y*y+y-x*x*x+x*x+10*x+20)%ell==0
                    for x in range(ell) for y in range(ell))
        counts[str(ell)]={'point_count':count,'a_ell':ell+1-count}
    assert counts=={'2':{'point_count':5,'a_ell':-2},
                    '3':{'point_count':5,'a_ell':-1}}
    out={'status':'PASS_INDEPENDENT_SMALL_PRIME_EIGENVALUES',
         'curve_ainvs':models[0],
         'hecke11_source_sha256':sha256(raw).hexdigest(),
         'point_counts':counts,
         'replay_sha256':sha256((HERE/'replay.json').read_bytes()).hexdigest(),
         'script_sha256':sha256((HERE/'verify_curve.py').read_bytes()).hexdigest()}
    (HERE/'curve_check.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
