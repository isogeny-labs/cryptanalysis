"""Exact source-bound memory gate for literal bucket-905 left tuple materialization."""
import hashlib,json,math
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def choose2(n):return n*(n-1)//2
def main():
    p=json.loads((HERE/'projection_protocol.json').read_text())
    paths={'source':HERE/'project_n131.py',
           'support':ROOT/'n131_w16_w18_sixpair_width_gate_20261010/support_w18.tsv',
           'join_source':HERE/'bucket_join.cpp','plan':HERE/'bucket_plan.json',
           'n41_audit':HERE/'bucket_audit_result.json'}
    assert {k:sha(v) for k,v in paths.items()}==p['sha256']
    plan=json.loads(paths['plan'].read_text())
    assert plan['plan'][0]['low6_masks']==[9,14]
    masks={int(a):int(c) for a,c in (line.split() for line in paths['support'].read_text().splitlines())}
    assert len(masks)==131307 and len(set(masks.values()))==131068
    bycol=Counter(masks.values());same=sum(choose2(v) for v in bycol.values())
    total_pair_states=4*(choose2(len(masks))-same)
    assert total_pair_states==34482792912
    A={c for a,c in masks.items() if a&63==9}
    B={c for a,c in masks.items() if a&63==14}
    assert len(A)==sum(a&63==9 for a in masks)
    assert len(B)==sum(a&63==14 for a in masks)
    countA=Counter(bycol[c] for c in A);countB=Counter(bycol[c] for c in B)
    def second_states(ki,kj):
        remaining=len(masks)-ki-kj
        return 4*(choose2(remaining)-same+choose2(ki)+choose2(kj))
    class_pairs=Counter();left_tuples=0
    for ki,na in countA.items():
        for kj,nb in countB.items():
            n=na*nb
            if ki==kj:n-=sum(bycol[c]==ki for c in A&B)
            assert n>=0
            class_pairs[f'{ki},{kj}']=n
            left_tuples+=4*n*second_states(ki,kj)
    edges=sum(class_pairs.values());first_pair_states=4*edges
    assert edges==len(A)*len(B)-len(A&B)
    bits_bytes=(left_tuples+7)//8
    result={'status':'FAIL_N131_LITERAL_LEFT_HASH_MEMORY_GATE','candidate_id':None,
            'curve_id':'EC1N131Ckb1heb5f1998f20b',
            'source_masks':len(masks),'folded_columns':len(bycol),
            'full_signed_pair_states_per_slot':total_pair_states,
            'low6_9_masks':len(A),'low6_14_masks':len(B),
            'same_column_cross_class_pairs':len(A&B),
            'first_unordered_admissible_edges':edges,
            'first_signed_pair_states':first_pair_states,
            'column_multiplicity_class_pairs':dict(class_pairs),
            'literal_left_entries':left_tuples,
            'one_bit_per_entry_bytes':bits_bytes,
            'rss_cap_bytes':p['rss_cap_bytes'],
            'one_bit_memory_cap_ratio':format(bits_bytes/p['rss_cap_bytes'],'.9e'),
            'sha256':{k:sha(v) for k,v in paths.items()},
            'protocol_sha256':sha(HERE/'projection_protocol.json')}
    assert bits_bytes>p['rss_cap_bytes']
    (HERE/'projection_result.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(result['status'],edges,first_pair_states,left_tuples,bits_bytes,flush=True)
if __name__=='__main__':main()
