"""Independent saved-row and class-number replay of the D1295 sheet result."""
from collections import Counter,defaultdict,deque
import hashlib
import json
from math import gcd,isqrt
from pathlib import Path

HERE=Path(__file__).resolve().parent
MODULUS=1000000007


def read(name):return json.loads((HERE/name).read_text())
def sha(name):return hashlib.sha256((HERE/name).read_bytes()).hexdigest()


def class_number(disc):
    total=0
    for a in range(1,isqrt((-disc)//3)+2):
        for b in range(-a,a+1):
            n=b*b-disc
            if n%(4*a):continue
            c=n//(4*a)
            if a>c or (b<0 and (abs(b)==a or a==c)):continue
            if gcd(gcd(a,abs(b)),c)==1:total+=1
    return total


def rank_mod(rows,q):
    a=[[value%q for value in row] for row in rows]
    pivot=0
    for col in range(len(a[0])):
        chosen=next((r for r in range(pivot,len(a)) if a[r][col]),None)
        if chosen is None:continue
        a[pivot],a[chosen]=a[chosen],a[pivot]
        inverse=pow(a[pivot][col],-1,q)
        a[pivot]=[v*inverse%q for v in a[pivot]]
        for r in range(pivot+1,len(a)):
            factor=a[r][col]
            if factor:a[r]=[(v-factor*w)%q for v,w in zip(a[r],a[pivot])]
        pivot+=1
        if pivot==len(a):break
    return pivot


def components(adj):
    unseen=set(adj)
    found=[]
    while unseen:
        first=min(unseen)
        queue=deque([first])
        seen={first}
        unseen.remove(first)
        while queue:
            src=queue.popleft()
            for dst in adj[src]:
                if dst not in seen:
                    seen.add(dst)
                    unseen.remove(dst)
                    queue.append(dst)
        found.append(seen)
    return found


def main():
    selection,protocol,gate,data,audit=(read(name) for name in
        ('selection.json','producer_protocol.json','fiber_gate_result.json',
         'data/exp11_class_walk_D1295_f6.json','audit.json'))
    assert selection['protocol_sha256']==sha('selection_protocol.json')
    assert selection['chosen']=={'d':1295,'h1':36,'h2':36,'h3':72,
        'norm3_order_f2':18,'frobenius_discriminant_mod_11':9,
        'v':8,'p':11719,'u_abs':16,'conductor2_points_predicted':72,
        'separate_cycle_count_predicted':4,'separate_cycle_length_predicted':18,
        'sheet_swap_cycle_count_predicted':2,'sheet_swap_cycle_length_predicted':36}
    assert protocol['selection_sha256']==sha('selection.json')
    for name,digest in protocol['source_sha256'].items():assert sha(name)==digest
    assert all(11719%q for q in range(2,isqrt(11719)+1))
    assert 16**2-4*11719==-1295*6*6
    classes={str(f):class_number(-1295*f*f) for f in (1,2,3,6)}
    assert classes=={'1':36,'2':36,'3':72,'6':72}
    assert gate['status']=='PASS_UNIFORM_TWO_SHEET_GATE'
    assert gate['script_sha256']==sha('fiber_gate.py')
    assert {f:row['class_number'] for f,row in gate['strata'].items()}==classes
    assert all(row['rational_point_count']==2*classes[f] and
               row['points_per_j']=={'2':classes[f]}
               for f,row in gate['strata'].items())
    assert (data['class_size'],data['relations'],data['rank'])==(432,360,288)
    assert audit['status']=='VERIFIED_D1295_SHEET_ACTION'
    assert audit['data_sha256']==sha('data/exp11_class_walk_D1295_f6.json')
    assert audit['script_sha256']==sha('audit.py')
    assert audit['verdict']=='SEPARATE_SHEET_CYCLES'
    assert audit['cycle_lengths']==[18]*4
    assert audit['ranks']=={'degree3_full_QQ':144,'degree3_nonfloor_QQ':136,
                            'combined_full_QQ':288,'combined_nonfloor_QQ':272}
    point_records=audit['point_records']
    assert len(point_records)==432
    c2={r['column'] for r in point_records if r['conductor']==2}
    floor={r['column'] for r in point_records if r['conductor']==6}
    j_by_col={r['column']:r['j'] for r in point_records}
    assert len(c2)==72 and len(floor)==144
    fibers=Counter(j_by_col[col] for col in c2)
    assert len(fibers)==36 and set(fibers.values())=={2}
    source_rows={int(src):int(row) for src,row in audit['degree3_source_rows'].items()}
    assert set(source_rows)==c2
    adj={}
    for src in c2:
        raw=data['relation_rows'][source_rows[src]]
        projected={int(col):int(value) for col,value in raw.items()
                   if int(col) not in floor and value}
        assert projected.get(src)==1 and len(projected)==3
        assert set(projected.values())=={1} and set(projected)<=c2
        adj[src]=set(projected)-{src}
    assert all(len(ns)==2 and all(src in adj[dst] for dst in ns)
               for src,ns in adj.items())
    groups=components(adj)
    assert sorted(map(len,groups))==[18]*4
    sets=[]
    for group in groups:
        js=Counter(j_by_col[col] for col in group)
        assert len(js)==18 and set(js.values())=={1}
        sets.append(set(js))
        rows=[]
        order=sorted(group)
        for src in order:
            row=data['relation_rows'][source_rows[src]]
            rows.append([int(row.get(str(col),0)) for col in order])
        assert rank_mod(rows,MODULUS)==16
    matches=sorted((i,j) for i in range(4) for j in range(i+1,4) if sets[i]==sets[j])
    assert len(matches)==2 and len({i for pair in matches for i in pair})==4
    assert set().union(*sets)==set(fibers)
    result={'status':'PASS_PROSPECTIVE_SEPARATE_SHEET_CYCLES',
            'selection_protocol_sha256':sha('selection_protocol.json'),
            'producer_protocol_sha256':sha('producer_protocol.json'),
            'data_sha256':sha('data/exp11_class_walk_D1295_f6.json'),
            'audit_sha256':sha('audit.json'),
            'script_sha256':sha('validate.py'),
            'cycle_lengths':[18]*4,'paired_j_cycle_indices':matches,
            'degree3_projected_kernel_dimension':8,
            'class_numbers':classes,'modulus':MODULUS,
            'candidate_id':None,'timing_claim':None}
    (HERE/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
