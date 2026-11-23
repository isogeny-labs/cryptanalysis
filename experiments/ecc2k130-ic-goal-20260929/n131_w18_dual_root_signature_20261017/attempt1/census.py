"""Exact dual-root signature and low-degree source-code screen for W18."""
import gzip
import hashlib
import itertools
import json
import signal
import sys
import time
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'n131_w18_linked_signature_prefix_20261012'
TABLE=SOURCE/'rows.tsv.gz'
AUDIT=SOURCE/'table_audit_result.json'
N=131
CODE_BITS=17
MAX_DEGREE=4


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name,value):
    with (HERE/name).open('x') as out:
        json.dump(value,out,sort_keys=True,indent=2)
        out.write('\n')


def freeze():
    prior=json.loads(AUDIT.read_text())
    assert prior['status'].startswith('PASS')
    save('protocol.json',{'status':'FROZEN_W18_DUAL_SIGNATURE_BEFORE_CENSUS',
                          'curve_id':'EC1N131Ckb1heb5f1998f20b',
                          'field_degree':N,'source_code_bits':CODE_BITS,
                          'source_code_count':33191,
                          'root_law':'two standard reciprocals per code, difference in 17-dimensional product image',
                          'degree_screen':[0,1,2,3,4],
                          'worker_count':1,'wall_cap_seconds':180,
                          'source_sha256':{'script':sha(Path(__file__)),
                                           'table':sha(TABLE),'prior_audit':sha(AUDIT)}})


def read_rows():
    rows=[]
    with gzip.open(TABLE,'rt') as stream:
        header=stream.readline().strip().split('\t')
        assert header==['code','mask_a','mask_b','root_bit','a0','a1',
                        'plus0','minus0','plus1','minus1']
        for line in stream:
            cells=list(map(int,line.strip().split('\t')))
            code,a,b,bit,x0,x1,*_=cells
            assert a==code and b==(code^212) and bit in (0,1)
            assert 0<=code<(1<<CODE_BITS) and 0<x0<(1<<N) and 0<x1<(1<<N)
            assert x0!=x1
            rows.append((code,x0,x1))
    assert len(rows)==33191 and len({row[0] for row in rows})==len(rows)
    return rows


def rref_high(vectors):
    basis={}
    for original in vectors:
        value=original
        while value:
            pivot=value.bit_length()-1
            if pivot not in basis:
                basis[pivot]=value
                break
            value^=basis[pivot]
    for pivot in sorted(basis):
        for other in list(basis):
            if other!=pivot and (basis[other]>>pivot)&1:
                basis[other]^=basis[pivot]
    return basis


def dual_masks(rows):
    pivots=rref_high(x0^x1 for _,x0,x1 in rows)
    assert len(pivots)==CODE_BITS
    free=[i for i in range(N) if i not in pivots]
    masks=[]
    for i in free:
        mask=1<<i
        for pivot,row in pivots.items():
            if (row>>i)&1:
                mask|=1<<pivot
        masks.append(mask)
    assert len(masks)==N-CODE_BITS
    assert all(((x0^x1)&mask).bit_count()%2==0
               for _,x0,x1 in rows for mask in masks)
    return pivots,masks


def monomials_at_degree(degree):
    for indices in itertools.combinations(range(CODE_BITS),degree):
        yield sum(1<<i for i in indices)


def screen(rows,masks):
    count=len(rows)
    allrows=(1<<count)-1
    varvectors=[0]*CODE_BITS
    labels=[0]*len(masks)
    signatures=[]
    for index,(code,x0,x1) in enumerate(rows):
        bit=1<<index
        for j in range(CODE_BITS):
            if (code>>j)&1:
                varvectors[j]|=bit
        signature=0
        for j,mask in enumerate(masks):
            if (x0&mask).bit_count()&1:
                labels[j]|=bit
                signature|=1<<j
        signatures.append(signature)
    basis={}
    monomials=[]
    degrees=[]
    fit_formulas={}
    for degree in range(MAX_DEGREE+1):
        for monom in monomials_at_degree(degree):
            vector=allrows
            for bit in range(CODE_BITS):
                if (monom>>bit)&1:
                    vector&=varvectors[bit]
            combo=1<<len(monomials)
            monomials.append(monom)
            while vector:
                pivot=vector.bit_length()-1
                if pivot in basis:
                    vector^=basis[pivot][0]
                    combo^=basis[pivot][1]
                else:
                    basis[pivot]=(vector,combo)
                    break
        newly=[]
        for index,label in enumerate(labels):
            if index in fit_formulas:
                continue
            vector=label;combo=0
            while vector:
                pivot=vector.bit_length()-1
                if pivot not in basis:
                    break
                vector^=basis[pivot][0]
                combo^=basis[pivot][1]
            if vector==0:
                selected=[monomials[j] for j in range(len(monomials))
                          if (combo>>j)&1]
                assert all((sum((code&monom)==monom for monom in selected)&1)==
                           ((x0&masks[index]).bit_count()&1)
                           for code,x0,_ in rows)
                fit_formulas[index]=selected
                newly.append(index)
        degrees.append({'degree':degree,'feature_count':len(monomials),
                        'feature_rank':len(basis),'new_signature_bits_fitting':newly,
                        'cumulative_signature_bits_fitting':len(fit_formulas)})
    return {'degree_screen':degrees,
            'fit_formulas':{str(i):v for i,v in fit_formulas.items()},
            'unique_full_signatures':len(set(signatures)),
            'signature_collision_count':len(signatures)-len(set(signatures)),
            'signature_values_sha256':hashlib.sha256(b''.join(
                value.to_bytes(15,'little') for value in signatures)).hexdigest(),
            'signature_trace_counts':dict(Counter(value&1 for value in signatures))}


def run():
    t0=time.monotonic_ns()
    signal.alarm(180)
    protocol=json.loads((HERE/'protocol.json').read_text())
    assert protocol['status']=='FROZEN_W18_DUAL_SIGNATURE_BEFORE_CENSUS'
    assert protocol['source_sha256']=={'script':sha(Path(__file__)),
                                       'table':sha(TABLE),'prior_audit':sha(AUDIT)}
    rows=read_rows()
    t1=time.monotonic_ns()
    pivots,masks=dual_masks(rows)
    t2=time.monotonic_ns()
    screen_result=screen(rows,masks)
    t3=time.monotonic_ns()
    result={'status':'PASS_W18_DUAL_ROOT_SIGNATURE_CENSUS',
            'curve_id':protocol['curve_id'],'source_code_count':len(rows),
            'delta_rank':len(pivots),'dual_dimension':len(masks),
            'dual_masks':masks,
            'dual_mask_weight_histogram':dict(Counter(m.bit_count() for m in masks)),
            'delta_pivot_positions':sorted(pivots),
            **screen_result,
            'phase_ns':{'table_parse':t1-t0,'dual_basis':t2-t1,
                        'degree_screen':t3-t2},
            'elapsed_ns':t3-t0,
            'protocol_sha256':sha(HERE/'protocol.json'),
            'source_sha256':protocol['source_sha256']}
    save('result.json',result)
    signal.alarm(0)
    print(result['status'],result['delta_rank'],result['dual_dimension'],
          [row['cumulative_signature_bits_fitting'] for row in result['degree_screen']],flush=True)


if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('freeze','run')
    {'freeze':freeze,'run':run}[sys.argv[1]]()
