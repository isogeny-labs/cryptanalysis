"""Extract compact branch-invariant degree-two obstruction certificates."""
import hashlib
import json
from pathlib import Path

here = Path(__file__).resolve().parent
p = json.loads((here/'certificate_protocol.json').read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for path,digest in p['sources'].items():
    assert sha(path) == digest, path
assert not (here/'certificate_result.json').exists()


def features(code,bits):
    values=[1]+[(code>>i)&1 for i in range(bits)]
    values += [((code>>i)&1)&((code>>j)&1)
               for i in range(bits) for j in range(i+1,bits)]
    return sum(value<<i for i,value in enumerate(values))


def make(mode, bits, path):
    rows = json.loads(Path(path).read_text())['queries'][0]['sources']
    rows = sorted((row for row in rows if isinstance(row['code'],int)),
                  key=lambda row:row['code'])
    feature_basis = {}
    selected = None
    for i,row in enumerate(rows):
        vector=features(row['code'],bits)
        combination=1<<i
        while vector:
            pivot=vector.bit_length()-1
            if pivot not in feature_basis:
                feature_basis[pivot]=(vector,combination)
                break
            old,old_combination=feature_basis[pivot]
            vector^=old
            combination^=old_combination
        if not vector:
            selected=[j for j in range(len(rows)) if combination>>j&1]
            break
    assert selected is not None
    root_xor=0
    for j in selected:
        root_xor^=rows[j]['pair_roots'][0]
    linear_basis={}

    def insert(x,rhs):
        while x:
            pivot=x.bit_length()-1
            if pivot not in linear_basis:
                linear_basis[pivot]=(x,rhs)
                return
            old,old_rhs=linear_basis[pivot]
            x^=old
            rhs^=old_rhs
        assert rhs==0

    for row in rows:
        insert(row['pair_roots'][0]^row['pair_roots'][1],0)
    insert(root_xor,1)
    mask=0
    for pivot in sorted(linear_basis):
        vector,rhs=linear_basis[pivot]
        value=rhs^(((vector^(1<<pivot))&mask).bit_count()&1)
        mask|=value<<pivot
    assert mask and all((((row['pair_roots'][0]^row['pair_roots'][1])&mask).bit_count()&1)==0
                        for row in rows)
    assert (root_xor&mask).bit_count()&1
    feature_xor=0
    for j in selected:
        feature_xor^=features(rows[j]['code'],bits)
    assert feature_xor==0
    return {'mode':mode,'source_count':len(rows),'code_bits':bits,
            'selected_indices':selected,
            'selected_codes':[rows[j]['code'] for j in selected],
            'annihilator_mask':mask,'annihilator_weight':mask.bit_count(),
            'feature_xor':feature_xor,
            'selected_root_xor':root_xor,
            'selected_root_parity':(root_xor&mask).bit_count()&1,
            'all_branch_differences_annihilated':True}


out={'status':'PASS_BRANCH_INVARIANT_QUADRATIC_OBSTRUCTION_CERTIFICATES',
     'candidate_id':None,
     'certificates':[make('n41',8,p['n41_source']),
                     make('n131',28,p['n131_source'])],
     'protocol_sha256':sha(here/'certificate_protocol.json')}
(here/'certificate_result.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
for row in out['certificates']:
    print(row['mode'],'selected',len(row['selected_indices']),
          'annihilator',hex(row['annihilator_mask']),
          'weight',row['annihilator_weight'])
