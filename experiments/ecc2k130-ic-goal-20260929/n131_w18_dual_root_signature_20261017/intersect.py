"""Intersect root-invariant signatures with source-code ANF spaces."""
import hashlib
import json
import signal
import sys
import time
from pathlib import Path

import census

HERE=Path(__file__).resolve().parent
MAX_DEGREE=5


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name,value):
    with (HERE/name).open('x') as out:
        json.dump(value,out,sort_keys=True,indent=2)
        out.write('\n')


def freeze():
    original=json.loads((HERE/'result.json').read_text())
    assert original['status']=='PASS_W18_DUAL_ROOT_SIGNATURE_CENSUS'
    save('intersection_protocol.json',{
        'status':'FROZEN_DUAL_ANF_INTERSECTION_BEFORE_RUN',
        'curve_id':original['curve_id'],'source_code_count':33191,
        'dual_dimension':114,'degree_screen':list(range(MAX_DEGREE+1)),
        'worker_count':1,'wall_cap_seconds':180,
        'source_sha256':{'script':sha(Path(__file__)),'census':sha(HERE/'census.py'),
                         'census_result':sha(HERE/'result.json'),
                         'table':sha(census.TABLE)}})


def rank_with_combos(vectors):
    basis={};dependencies=[]
    for i,original in enumerate(vectors):
        value=original;combo=1<<i
        while value:
            pivot=value.bit_length()-1
            if pivot in basis:
                value^=basis[pivot][0]
                combo^=basis[pivot][1]
            else:
                basis[pivot]=(value,combo)
                break
        if value==0:
            dependencies.append(combo)
    return basis,dependencies


def run():
    t0=time.monotonic_ns()
    signal.alarm(180)
    protocol=json.loads((HERE/'intersection_protocol.json').read_text())
    assert protocol['status']=='FROZEN_DUAL_ANF_INTERSECTION_BEFORE_RUN'
    assert protocol['source_sha256']=={
        'script':sha(Path(__file__)),'census':sha(HERE/'census.py'),
        'census_result':sha(HERE/'result.json'),'table':sha(census.TABLE)}
    rows=census.read_rows()
    original=json.loads((HERE/'result.json').read_text())
    masks=original['dual_masks']
    assert len(masks)==114
    allrows=(1<<len(rows))-1
    codebit=[0]*17;labels=[0]*len(masks)
    for index,(code,x0,_) in enumerate(rows):
        indexbit=1<<index
        for j in range(17):
            if (code>>j)&1:
                codebit[j]|=indexbit
        for j,mask in enumerate(masks):
            if (x0&mask).bit_count()&1:
                labels[j]|=indexbit
    signature_rank=len(rank_with_combos(labels)[0])
    features={};monomials=[];screens=[]
    for degree in range(MAX_DEGREE+1):
        for monom in census.monomials_at_degree(degree):
            value=allrows
            for bit in range(17):
                if (monom>>bit)&1:
                    value&=codebit[bit]
            monomials.append(monom)
            while value:
                pivot=value.bit_length()-1
                if pivot in features:
                    value^=features[pivot]
                else:
                    features[pivot]=value
                    break
        residuals=[]
        feature_pivots=sorted(features,reverse=True)
        for label in labels:
            value=label
            for pivot in feature_pivots:
                if (value>>pivot)&1:
                    value^=features[pivot]
            residuals.append(value)
        quotient_basis,dependencies=rank_with_combos(residuals)
        intersection=signature_rank-len(quotient_basis)
        assert intersection>=0
        screens.append({'degree':degree,'feature_count':len(monomials),
                        'feature_rank':len(features),'signature_rank':signature_rank,
                        'quotient_signature_rank':len(quotient_basis),
                        'intersection_dimension':intersection,
                        'first_dependency_mask':dependencies[0] if dependencies else None})
    elapsed=time.monotonic_ns()-t0
    result={'status':'PASS_W18_DUAL_ANF_INTERSECTION',
            'curve_id':protocol['curve_id'],'source_code_count':len(rows),
            'dual_dimension':len(masks),'signature_rank':signature_rank,
            'screens':screens,'elapsed_ns':elapsed,
            'source_sha256':protocol['source_sha256'],
            'protocol_sha256':sha(HERE/'intersection_protocol.json')}
    save('intersection_result.json',result)
    signal.alarm(0)
    print(result['status'],[(row['degree'],row['intersection_dimension'])
                             for row in screens],flush=True)


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('freeze','run')
    {'freeze':freeze,'run':run}[sys.argv[1]]()
