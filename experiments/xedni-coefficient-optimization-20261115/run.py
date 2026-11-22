"""Exhaustive same-budget public vector search on fresh fields."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def mul_add_cost(k):
    k=abs(k)
    return k.bit_length()+k.bit_count()

def search(d,q,vectors,cap):
    tests=adds=admitted=0
    for t in range(cap):
        if t:
            adds+=1  # advance Q-(t-1)G to Q-tG
        if t==0 or t==d:
            continue
        admitted+=1
        for j,(a,b) in enumerate(vectors):
            tests+=1
            adds+=mul_add_cost(a)+mul_add_cost(b)+1
            if ((a+b)*d-b*t)%q==0:
                recovered=(b*t*pow((a+b)%q,-1,q))%q
                assert recovered==d
                return {'status':'hit','query_index':t+1,'offset':t,
                        'vector_index':j,'vector':[a,b],
                        'vector_tests':tests,'group_add_calls':adds,
                        'admitted_queries':admitted,'recovered_scalar':recovered}
    return {'status':'capped','query_index':cap,'offset':cap-1,
            'vector_index':None,'vector':None,'vector_tests':tests,
            'group_add_calls':adds,'admitted_queries':admitted,
            'recovered_scalar':None}

def main():
    protocol=json.loads((HERE/'protocol.json').read_text())
    family=json.loads((HERE/'family-selection.json').read_text())
    fields=json.loads((HERE/'field-selection.json').read_text())
    assert family['protocol_sha256']==fields['protocol_sha256']==sha(HERE/'protocol.json')
    assert fields['family_selection_sha256']==sha(HERE/'family-selection.json')
    cap=protocol['query_cap'];assert cap==35
    vectors={name:[tuple(v) for v in family[name]] for name in ('baseline','selected')}
    assert all(len(v)==13 for v in vectors.values())
    output=[]
    for p,q in fields['selected']:
        raw=[];sums={name:{'hits':0,'capped':0,'vector_tests':0,'group_add_calls':0} for name in vectors}
        for d in range(1,q):
            item={'scalar':d}
            for name,V in vectors.items():
                r=search(d,q,V,cap)
                item[name]=r
                sums[name][r['status']+'s' if r['status']=='hit' else 'capped']+=1
                sums[name]['vector_tests']+=r['vector_tests']
                sums[name]['group_add_calls']+=r['group_add_calls']
            raw.append(item)
        path=HERE/f'p{p}-targets.jsonl'
        path.write_text(''.join(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n' for x in raw))
        assert all(x['hits']+x['capped']==q-1 for x in sums.values())
        output.append({'field_prime':p,'subgroup_order':q,'target_count':q-1,
                       'raw_path':path.name,'raw_sha256':sha(path),
                       'arms':sums})
    print(json.dumps({'schema':'xedni-coefficient-optimization-result-v1','status':'PASS',
                      'protocol_sha256':sha(HERE/'protocol.json'),
                      'source_sha256':sha(Path(__file__)),
                      'family_selection_sha256':sha(HERE/'family-selection.json'),
                      'field_selection_sha256':sha(HERE/'field-selection.json'),
                      'fields':output},sort_keys=True,indent=2))

if __name__=='__main__':main()
