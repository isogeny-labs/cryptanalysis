"""Exact standard-Python Hecke commutator replay on the sealed D=-1295 class."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREV = HERE.parent/'hecke-two-sheet-small-order-20261023'
PROOF = HERE.parent/'hecke-ramified11-fullrank-20261023'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def rank_mod(rows,cols,q):
    a=[[int(row.get(str(j),0))%q for j in cols] for row in rows]
    rank=0
    for j in range(len(cols)):
        pivot=next((k for k in range(rank,len(a)) if a[k][j]),None)
        if pivot is None:continue
        a[rank],a[pivot]=a[pivot],a[rank]
        inv=pow(a[rank][j],-1,q)
        a[rank]=[(v*inv)%q for v in a[rank]]
        for k in range(rank+1,len(a)):
            if a[k][j]:
                factor=a[k][j]
                a[k]=[(v-factor*w)%q for v,w in zip(a[k],a[rank])]
        rank+=1
        if rank==len(a):break
    return rank


def main():
    protocol_raw=(HERE/'protocol.json').read_bytes(); protocol=json.loads(protocol_raw)
    assert protocol['status']=='FROZEN_BEFORE_COMMUTATOR_REPLAY'
    assert protocol['source_sha256']['replay']==digest(HERE/'replay.py')
    assert protocol['source_sha256']['predecessor_seal']==digest(PREV/'SEAL.json')
    assert protocol['source_sha256']['formal_theorem']==digest(PROOF/'formal/HeckeCommutator.lean')
    seal=json.loads((PREV/'SEAL.json').read_text())
    for rel,h in seal['files'].items():assert digest(PREV/rel)==h,rel
    data=json.loads((PREV/'data/exp11_class_walk_D1295_f6.json').read_text())
    audit=json.loads((PREV/'audit.json').read_text())
    assert (data['DK'],data['f'],data['p'],data['u'])==(-1295,6,11719,16)
    points=audit['point_records']; meta=audit['row_records']; rows=data['relation_rows']
    assert (len(points),len(meta),len(rows))==(432,360,360)
    assert dict(Counter(r['conductor'] for r in points))=={1:72,2:72,3:144,6:144}
    row_for={(r['source'],r['degree']):r['row'] for r in meta}
    assert len(row_for)==360
    a_l={2:-2,3:-1}
    def neighbours(source,degree):
        row=rows[row_for[(source,degree)]]
        counts={int(j):v for j,v in row.items()}
        counts[source]=counts.get(source,0)+a_l[degree]
        assert all(v>=0 for v in counts.values())
        out=[j for j,n in counts.items() for _ in range(n)]
        assert len(out)==degree+1
        return out
    c1=[r['column'] for r in points if r['conductor']==1]
    c2=[r['column'] for r in points if r['conductor']==2]
    c2_row_ids={row_for[(j,3)] for j in c2}
    assert (len(c1),len(c2),len(c2_row_ids))==(72,72,72)
    certificates=[]
    for source in c1:
        n2,n3=neighbours(source,2),neighbours(source,3)
        targets=[j for j in n2 if points[j]['conductor']==2]
        assert len(targets)==1
        target=targets[0]
        assert all(points[j]['conductor']==1 for j in n2 if j!=target)
        assert all(points[j]['conductor'] in (1,3) for j in n3)
        terms=Counter()
        for j in n3:terms[row_for[(j,2)]]+=1
        terms[row_for[(source,2)]]+=1
        for j in n2:
            if j!=target:terms[row_for[(j,3)]]-=1
        terms[row_for[(source,3)]]-=2
        terms={k:v for k,v in terms.items() if v}
        assert len(terms)==8
        target_row=row_for[(target,3)]
        assert set(terms).isdisjoint(c2_row_ids)
        result=Counter()
        for row_id,coefficient in terms.items():
            for col,value in rows[row_id].items():result[int(col)]+=coefficient*value
        result={str(k):v for k,v in result.items() if v}
        assert result==rows[target_row],(source,target_row)
        certificates.append({'c1_source_column':source,'c2_target_column':target,
                             'c2_row':target_row,
                             'terms':{str(k):v for k,v in sorted(terms.items())}})
    assert len({w['c2_target_column'] for w in certificates})==72
    assert {w['c2_row'] for w in certificates}==c2_row_ids
    others=[i for i in range(360) if i not in c2_row_ids]
    nonfloor=[r['column'] for r in points if r['conductor']!=6]
    assert (len(others),len(nonfloor))==(288,288)
    mod_ranks={}
    for q in (101,1000000007):
        mod_ranks[str(q)]={'other_rows_full':rank_mod([rows[i] for i in others],list(range(432)),q),
                           'other_rows_nonfloor':rank_mod([rows[i] for i in others],nonfloor,q)}
        assert mod_ranks[str(q)]=={'other_rows_full':288,'other_rows_nonfloor':272}
    assert audit['ranks']['combined_full_QQ']==288
    assert audit['ranks']['combined_nonfloor_QQ']==272
    out={'status':'PASS_TWO_SHEET_HECKE_COMMUTATOR_REPLAY',
         'protocol_sha256':sha256(protocol_raw).hexdigest(),
         'script_sha256':digest(HERE/'replay.py'),
         'predecessor_seal_sha256':digest(PREV/'SEAL.json'),
         'source_data_sha256':digest(PREV/'data/exp11_class_walk_D1295_f6.json'),
         'source_audit_sha256':digest(PREV/'audit.json'),
         'c1_point_count':len(c1),'c2_point_count':len(c2),
         'commutator_certificates':certificates,
         'certificate_count':len(certificates),
         'certificate_terms_per_row':sorted({len(w['terms']) for w in certificates}),
         'other_row_count':len(others),'modular_rank_receipts':mod_ranks,
         'certified_full_rank_QQ':288,'certified_nonfloor_rank_QQ':272,
         'c2_increment_full_QQ':0,'c2_increment_nonfloor_QQ':0,
         'candidate_id':None,'timing_claim':None}
    (HERE/'replay.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:out[k] for k in ('status','certificate_count','certificate_terms_per_row',
                                         'certified_full_rank_QQ','certified_nonfloor_rank_QQ',
                                         'c2_increment_full_QQ')},sort_keys=True))


if __name__=='__main__':main()
