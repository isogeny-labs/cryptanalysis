"""Independent exact-field check of the eliminated public S3 root."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

D=Path(__file__).resolve().parent
ROOT=D.parent
SOURCE=ROOT/'n41_w8_quotient_first_pair_20261015'
NORM=ROOT/'n41_three_code_nested_norm_20261015'
WITNESS=ROOT/'n41_sixpair_shared_target_20261017'/'join_audit_result.json'
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(NORM))
import circuit
from three_norm import Ops,three_source_norm
spec=importlib.util.spec_from_file_location('old_n41_builder',SOURCE/'build.py')
old_build=importlib.util.module_from_spec(spec);spec.loader.exec_module(old_build)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    F=circuit.F
    e=circuit.projector()
    geometry=circuit.geometry()
    witness=json.loads(WITNESS.read_text())
    rows=witness['pair_rows']
    add=old_build.prior.add
    left=add(add(tuple(rows[0]['raw_sum']),tuple(rows[1]['raw_sum'])),
             tuple(rows[2]['raw_sum']))
    right=add(add(tuple(rows[3]['raw_sum']),tuple(rows[4]['raw_sum'])),
              tuple(rows[5]['raw_sum']))
    assert add(left,right)==tuple(witness['raw_target'])
    t,u,q=[F.inv(x) for x in (left[0],right[0],witness['raw_target'][0])]
    lead_root=1^F.mul(t,q)
    assert lead_root
    lead=F.square(lead_root)
    alpha=F.mul(F.mul(t,q),F.inv(lead))
    beta=F.mul(F.square(t^q),F.inv(lead))
    assert F.square(u)^F.mul(alpha,u)^beta==0
    assert F.mul(lead,F.square(u))^F.mul(F.mul(t,q),u)^F.square(t^q)==0
    h=F.square(F.halftrace(e['seed']))
    coefficients=[]
    for slot,row in enumerate(rows):
        code=sum(((row['masks'][0]>>bit)&1)<<j for j,bit in enumerate(e['bits']))
        product=0
        for j,value in enumerate(e['basis']):
            if code>>j&1:product^=value
        rotation=geometry['rotations'][slot]
        hs=circuit.frob(h,rotation)
        divisor=1^hs
        assert divisor
        coefficients.append((F.mul(circuit.frob(product,rotation),F.inv(divisor)),
                             F.mul(hs,F.inv(divisor))))
    ops=Ops(0,1,lambda a,b:a^b,F.mul)
    ops.square=F.square
    def right_norm(value):
        return three_source_norm(*(x for pair in coefficients[3:] for x in pair),
                                 value,ops)
    root_two=u^alpha
    values=[right_norm(u),right_norm(root_two)]
    assert values[0]==0
    result={'status':'PASS','archive_sha256':sha(WITNESS),
            'public_reciprocal':q,'left_reciprocal':t,'right_reciprocal':u,
            's3_quadratic_lead_root':lead_root,'s3_alpha':alpha,'s3_beta':beta,
            'other_right_root':root_two,'right_norm_values':values,
            'resultant_value':F.mul(values[0],values[1])}
    (D/'field_audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
