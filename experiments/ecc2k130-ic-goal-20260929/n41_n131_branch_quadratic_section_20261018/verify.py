"""Check the frozen feature-dependency and branch-annihilator certificates."""
import hashlib
import json
from pathlib import Path

here=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


for name in ('protocol.json','certificate_protocol.json'):
    p=json.loads((here/name).read_text())
    for path,digest in p['sources'].items():
        assert sha(path)==digest,(name,path)


def features(code,bits):
    values=[1]+[(code>>i)&1 for i in range(bits)]
    for i in range(bits):
        for j in range(i+1,bits):
            values.append(((code>>i)&1)&((code>>j)&1))
    return sum(value<<index for index,value in enumerate(values))


producer=json.loads((here/'result.json').read_text())
certs=json.loads((here/'certificate_result.json').read_text())
assert producer['status']=='PASS_BRANCH_ADAPTIVE_QUADRATIC_SECTION_AUDIT'
assert certs['status']=='PASS_BRANCH_INVARIANT_QUADRATIC_OBSTRUCTION_CERTIFICATES'
assert producer['protocol_sha256']==sha(here/'protocol.json')
assert certs['protocol_sha256']==sha(here/'certificate_protocol.json')
p=json.loads((here/'certificate_protocol.json').read_text())
for row,cert in zip(producer['results'],certs['certificates']):
    assert row['mode']==cert['mode']
    assert row['status']=='NO_QUADRATIC_SECTION_ON_FROZEN_CODES'
    mode,bits=cert['mode'],cert['code_bits']
    data=json.loads(Path(p[f'{mode}_source']).read_text())['queries'][0]['sources']
    data=sorted((item for item in data if isinstance(item['code'],int)),
                key=lambda item:item['code'])
    assert len(data)==cert['source_count']
    selected=cert['selected_indices']
    assert [data[i]['code'] for i in selected]==cert['selected_codes']
    feature_xor=root_xor=0
    for i in selected:
        feature_xor^=features(data[i]['code'],bits)
        root_xor^=data[i]['pair_roots'][0]
    mask=cert['annihilator_mask']
    assert feature_xor==cert['feature_xor']==0
    assert root_xor==cert['selected_root_xor']
    assert (root_xor&mask).bit_count()%2==cert['selected_root_parity']==1
    assert all((((item['pair_roots'][0]^item['pair_roots'][1])&mask).bit_count()%2)==0
               for item in data)
    print(mode,'selected',len(selected),'mask',hex(mask),'verified')
lean=(here/'lean_check.log').read_text()
assert (here/'lean_exit_code.txt').read_text().strip()=='0'
assert "'BranchObstruction.no_branch_fit' depends on axioms: [propext, Quot.sound]" in lean
assert not any(word in (here/'BranchObstruction.lean').read_text()
               for word in ('sorry','admit','sorryAx'))
print('PASS_BRANCH_ADAPTIVE_SECTION_CERTIFICATE_REPLAY')
